#!/usr/bin/env python3
"""
METAR to Lattice Integration (Modified)
============================

This program integrates METAR (Meteorological Aerodrome Reports) airport weather conditions 
with the Anduril Lattice SDK. It retrieves weather data for New England airports and 
publishes Lattice entities representing airports with their current weather conditions.

Modified to include:
1. Entity health components for flight_condition, temperature_c, wind_speed_kt, and visibility_miles
2. Set entity disposition based on flight condition:
   - VFR = DISPOSITION_ASSUMED_FRIENDLY
   - MVFR = DISPOSITION_SUSPICIOUS
   - IFR = DISPOSITION_HOSTILE
   - LIFR = DISPOSITION_HOSTILE

Author: Anduril Industries - Developer Relations
Date: June 2025
"""

import asyncio
import json
import logging
import os
import sys
import gzip
import requests
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple
from uuid import uuid4
import xml.etree.ElementTree as ET

# Lattice SDK imports
from anduril.entitymanager.v1 import (
    EntityManagerApiStub, PublishEntityRequest, Aliases,
    Entity, MilView, Location, Position, Ontology, Template, Provenance,
    Health, HealthStatus, ComponentHealth, ComponentMessage
)
from anduril.ontology.v1 import Disposition, Environment
from grpclib.client import Channel

# METAR parsing library
try:
    from metar import Metar
except ImportError:
    print("Installing METAR parsing library...")
    os.system("pip install metar")
    from metar import Metar

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FlightConditions:
    """Flight condition classifications based on visibility and ceiling"""

    @staticmethod
    def determine_flight_conditions(visibility_miles: float, ceiling_feet: Optional[int]) -> str:
        """
        Determine flight conditions based on visibility and ceiling.

        Args:
            visibility_miles: Visibility in statute miles
            ceiling_feet: Ceiling in feet AGL (Above Ground Level)

        Returns:
            Flight condition: VFR, MVFR, IFR, or LIFR
        """
        # Convert None ceiling to very high ceiling for VFR conditions
        if ceiling_feet is None:
            ceiling_feet = 10000

        # LIFR: Ceiling below 500 feet and/or visibility less than 1 mile
        if ceiling_feet < 500 or visibility_miles < 1:
            return "LIFR"

        # IFR: Ceiling 500-999 feet and/or visibility 1-3 miles
        if ceiling_feet < 1000 or visibility_miles < 3:
            return "IFR"

        # MVFR: Ceiling 1000-3000 feet and/or visibility 3-5 miles
        if ceiling_feet < 3000 or visibility_miles < 5:
            return "MVFR"

        # VFR: Ceiling greater than 3000 feet and visibility greater than 5 miles
        return "VFR"

    @staticmethod
    def get_disposition_for_condition(flight_condition: str) -> Disposition:
        """
        Map flight condition to Lattice disposition.

        Args:
            flight_condition: Flight condition (VFR, MVFR, IFR, LIFR)

        Returns:
            Lattice disposition enumeration value
        """
        if flight_condition == "VFR":
            return Disposition.ASSUMED_FRIENDLY
        elif flight_condition == "MVFR":
            return Disposition.SUSPICIOUS
        else:  # IFR or LIFR
            return Disposition.HOSTILE

class MetarApiClient:
    """Client for fetching METAR data from aviation weather APIs"""

    def __init__(self, api_base_url: str = "https://aviationweather.gov/api/data"):
        self.api_base_url = api_base_url
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Anduril-Lattice-METAR-Integration/1.0"
        })

    def get_metar_data(self, icao_codes: List[str], timeout: int = 30) -> Dict[str, Dict]:
        """
        Retrieve METAR data for the specified ICAO airport codes.

        Args:
            icao_codes: List of ICAO airport codes
            timeout: Request timeout in seconds

        Returns:
            Dictionary mapping ICAO codes to weather data
        """
        try:
            params = {
                'ids': ','.join(icao_codes),
                'format': 'json',
                'taf': 'false',
                'hours': '1'
            }

            response = self.session.get(
                f"{self.api_base_url}/metar",
                params=params,
                timeout=timeout
            )
            response.raise_for_status()

            data = response.json()
            results = {}

            for metar_entry in data:
                icao = metar_entry.get('icaoId', '').upper()
                raw_text = metar_entry.get('rawOb', '')

                if not icao or not raw_text:
                    continue

                try:
                    # Parse the METAR text
                    parsed_metar = Metar.Metar(raw_text)

                    # Extract weather data
                    weather_data = {
                        'icao': icao,
                        'raw_text': raw_text,
                        'observation_time': metar_entry.get('obsTime'),
                        'temperature_c': parsed_metar.temp.value() if parsed_metar.temp else None,
                        'dewpoint_c': parsed_metar.dewpt.value() if parsed_metar.dewpt else None,
                        'wind_direction': parsed_metar.wind_dir.value() if parsed_metar.wind_dir else None,
                        'wind_speed_kt': parsed_metar.wind_speed.value() if parsed_metar.wind_speed else None,
                        'visibility_miles': parsed_metar.vis.value() if parsed_metar.vis else None,
                        'pressure_hpa': parsed_metar.press.value() if parsed_metar.press else None,
                        'cloud_layers': self._parse_cloud_layers(parsed_metar),
                        'weather_phenomena': [str(wx) for wx in parsed_metar.weather] if parsed_metar.weather else []
                    }

                    # Calculate flight conditions
                    ceiling_feet = self._get_ceiling_feet(weather_data['cloud_layers'])
                    visibility_miles = weather_data['visibility_miles'] or 10.0

                    weather_data['ceiling_feet'] = ceiling_feet
                    weather_data['flight_condition'] = FlightConditions.determine_flight_conditions(
                        visibility_miles, ceiling_feet
                    )

                    results[icao] = weather_data

                except Exception as e:
                    logger.error(f"Error parsing METAR for {icao}: {e}")
                    results[icao] = {'error': str(e), 'raw_text': raw_text}

            return results

        except Exception as e:
            logger.error(f"Error fetching METAR data: {e}")
            return {}

    def _parse_cloud_layers(self, metar: 'Metar.Metar') -> List[Dict]:
        """Parse cloud layer information from METAR."""
        layers = []
        for layer in metar.sky:
            layer_info = {
                'coverage': layer[0],
                'altitude_ft': layer[1].value() if layer[1] else None,
                'cloud_type': layer[2] if len(layer) > 2 else None
            }
            layers.append(layer_info)
        return layers

    def _get_ceiling_feet(self, cloud_layers: List[Dict]) -> Optional[int]:
        """Determine ceiling height from cloud layers."""
        ceiling_coverages = ['BKN', 'OVC']  # Broken or Overcast
        for layer in cloud_layers:
            if layer['coverage'] in ceiling_coverages and layer['altitude_ft']:
                return layer['altitude_ft']
        return None

class NewEnglandAirports:
    """Database of New England airports with their information"""

    @staticmethod
    def get_airports() -> Dict[str, Dict]:
        """Return dictionary of New England airports"""
        return {
            # Massachusetts
            'KBOS': {
                'name': 'General Edward Lawrence Logan International Airport',
                'city': 'Boston',
                'state': 'MA',
                'lat': 42.3656132,
                'lon': -71.0095602,
                'type': 'major'
            },
            'KORH': {
                'name': 'Worcester Regional Airport',
                'city': 'Worcester',
                'state': 'MA',
                'lat': 42.2673056,
                'lon': -71.8757222,
                'type': 'regional'
            },
            'KBED': {
                'name': 'Laurence G. Hanscom Field',
                'city': 'Bedford',
                'state': 'MA',
                'lat': 42.4699167,
                'lon': -71.2889722,
                'type': 'municipal'
            },
            'KACK': {
                'name': 'Nantucket Memorial Airport',
                'city': 'Nantucket',
                'state': 'MA',
                'lat': 41.2530556,
                'lon': -70.0597222,
                'type': 'regional'
            },
            'KMVT': {
                'name': "Martha's Vineyard Airport",
                'city': "Vineyard Haven",
                'state': 'MA',
                'lat': 41.3931389,
                'lon': -70.6144444,
                'type': 'regional'
            },
            'KHYA': {
                'name': 'Barnstable Municipal Airport',
                'city': 'Hyannis',
                'state': 'MA',
                'lat': 41.6693333,
                'lon': -70.2802778,
                'type': 'municipal'
            },

            # New Hampshire
            'KMHT': {
                'name': 'Manchester-Boston Regional Airport',
                'city': 'Manchester',
                'state': 'NH',
                'lat': 42.9346511,
                'lon': -71.4375794,
                'type': 'major'
            },
            'KLEB': {
                'name': 'Lebanon Municipal Airport',
                'city': 'Lebanon',
                'state': 'NH',
                'lat': 43.6261111,
                'lon': -72.3041667,
                'type': 'municipal'
            },
            'KCON': {
                'name': 'Concord Municipal Airport',
                'city': 'Concord',
                'state': 'NH',
                'lat': 43.2027778,
                'lon': -71.5019444,
                'type': 'municipal'
            },

            # Connecticut
            'KBDL': {
                'name': 'Bradley International Airport',
                'city': 'Hartford/Windsor Locks',
                'state': 'CT',
                'lat': 41.9388889,
                'lon': -72.6833333,
                'type': 'major'
            },
            'KHVN': {
                'name': 'Tweed New Haven Airport',
                'city': 'New Haven',
                'state': 'CT',
                'lat': 41.2637222,
                'lon': -72.8869444,
                'type': 'regional'
            },
            'KGON': {
                'name': 'Groton-New London Airport',
                'city': 'Groton',
                'state': 'CT',
                'lat': 41.3301389,
                'lon': -72.0451389,
                'type': 'municipal'
            },

            # Rhode Island
            'KPVD': {
                'name': 'Theodore Francis Green Airport',
                'city': 'Providence/Warwick',
                'state': 'RI',
                'lat': 41.7251944,
                'lon': -71.4283333,
                'type': 'major'
            },

            # Vermont
            'KBTV': {
                'name': 'Patrick Leahy Burlington International Airport',
                'city': 'Burlington',
                'state': 'VT',
                'lat': 44.4719444,
                'lon': -73.1533333,
                'type': 'major'
            },
            'KMPV': {
                'name': 'Edward F. Knapp State Airport',
                'city': 'Montpelier',
                'state': 'VT',
                'lat': 44.2055556,
                'lon': -72.5633333,
                'type': 'municipal'
            },

            # Maine
            'KBGR': {
                'name': 'Bangor International Airport',
                'city': 'Bangor',
                'state': 'ME',
                'lat': 44.8073889,
                'lon': -68.8281667,
                'type': 'major'
            },
            'KPWM': {
                'name': 'Portland International Jetport',
                'city': 'Portland',
                'state': 'ME',
                'lat': 43.6461111,
                'lon': -70.3093056,
                'type': 'major'
            },
            'KAUG': {
                'name': 'Augusta State Airport',
                'city': 'Augusta',
                'state': 'ME',
                'lat': 44.3206111,
                'lon': -69.7972222,
                'type': 'municipal'
            },
            'KBHB': {
                'name': 'Hancock County-Bar Harbor Airport',
                'city': 'Bar Harbor',
                'state': 'ME',
                'lat': 44.4497778,
                'lon': -68.3616667,
                'type': 'municipal'
            }
        }


class LatticeWeatherIntegration:
    """Main class for integrating METAR weather data with Lattice"""

    def __init__(
        self,
        lattice_url: str = None,
        environment_token: str = None,
        sandboxes_token: str = None,
        update_interval_minutes: int = 30
    ):
        # Get configuration from environment if not provided
        self.lattice_url = lattice_url or os.getenv('LATTICE_URL')
        self.environment_token = environment_token or os.getenv('ENVIRONMENT_TOKEN')
        self.sandboxes_token = sandboxes_token or os.getenv('SANDBOXES_TOKEN')
        self.update_interval_minutes = update_interval_minutes

        # Initialize clients
        self.metar_client = MetarApiClient()
        self.airports = NewEnglandAirports.get_airports()

        # Validate configuration
        if not self.lattice_url or not self.environment_token:
            logger.error("Missing Lattice configuration. Set LATTICE_URL and ENVIRONMENT_TOKEN environment variables.")
            raise ValueError("Missing Lattice configuration.")

        logger.info(f"Initialized Lattice integration for {len(self.airports)} airports")

    async def start(self):
        """Start the integration loop"""
        logger.info(f"Starting METAR to Lattice integration with {self.update_interval_minutes}-minute updates")

        while True:
            try:
                # Get weather data
                all_icao_codes = list(self.airports.keys())
                metar_data = self.metar_client.get_metar_data(all_icao_codes)

                if metar_data:
                    logger.info(f"Successfully retrieved METAR data for {len(metar_data)} airports")

                    # Publish to Lattice
                    entities_published = await self.publish_weather_entities(metar_data)
                    logger.info(f"Published {entities_published}/{len(self.airports)} weather entities to Lattice")
                else:
                    logger.error("Failed to retrieve any METAR data")

            except Exception as e:
                logger.error(f"Error in integration cycle: {e}")

            # Wait for next update
            logger.info(f"Waiting {self.update_interval_minutes} minutes until next update...")
            await asyncio.sleep(self.update_interval_minutes * 60)

    async def publish_weather_entities(self, metar_data: Dict[str, Dict]) -> int:
        """
        Publish weather entities to Lattice.

        Args:
            metar_data: Dictionary of METAR data by airport ICAO code

        Returns:
            Number of entities successfully published
        """
        count = 0

        for icao, data in metar_data.items():
            try:
                # Skip if error
                if 'error' in data:
                    logger.warning(f"Skipping {icao}: {data['error']}")
                    continue

                # Get airport info
                airport = self.airports.get(icao)
                if not airport:
                    logger.warning(f"Skipping unknown airport: {icao}")
                    continue

                # Create and publish entity
                entity = await self.create_weather_entity(icao, airport, data)
                await self.publish_entity(entity)
                count += 1

            except Exception as e:
                logger.error(f"Error publishing weather entity for {icao}: {e}")

        return count

    async def create_weather_entity(self, icao: str, airport: Dict, weather: Dict) -> Entity:
        """
        Create a Lattice entity for an airport with weather data.

        Args:
            icao: ICAO code of the airport
            airport: Airport information
            weather: Weather data for the airport

        Returns:
            Lattice entity representing the airport's weather
        """
        # Calculate timestamps
        time_now = datetime.now(timezone.utc)
        expiry_time = time_now + timedelta(hours=2)

        # Format description including flight condition
        flight_condition = weather.get('flight_condition', 'Unknown')
        temperature_c = weather.get('temperature_c')
        temperature_f = None if temperature_c is None else (temperature_c * 9/5) + 32
        description = f"{airport['name']} ({icao}) - {flight_condition}"

        # Get disposition based on flight condition
        disposition = FlightConditions.get_disposition_for_condition(flight_condition)

        # Health components for each weather parameter
        health_components = []

        # Flight condition health component
        if flight_condition:
            condition_status = self._get_health_status_for_condition(flight_condition)
            health_components.append(
                ComponentHealth(
                    id=f"{icao}_flight_condition",
                    name="Flight Condition",
                    health=condition_status,
                    messages=[
                        ComponentMessage(
                            message=f"Current flight condition: {flight_condition}",
                            status=condition_status
                        )
                    ]
                )
            )

        # Temperature health component
        if temperature_c is not None:
            temp_status = self._get_health_status_for_temperature(temperature_c)
            health_components.append(
                ComponentHealth(
                    id=Entity.entity_id, # f"{icao}_temperature",
                    name="Temperature",
                    health=temp_status,
                    messages=[
                        ComponentMessage(
                            message=f"Current temperature: {temperature_c:.1f}°C ({temperature_f:.1f}°F)",
                            status=temp_status
                        )
                    ]
                )
            )

        # Wind speed health component
        wind_speed = weather.get('wind_speed_kt')
        if wind_speed is not None:
            wind_status = self._get_health_status_for_wind(wind_speed)
            health_components.append(
                ComponentHealth(
                    id=Entity.entity_id, # f"{icao}_wind_speed",
                    name="Wind Speed",
                    health=wind_status,
                    messages=[
                        ComponentMessage(
                            message=f"Current wind speed: {wind_speed} knots",
                            status=wind_status
                        )
                    ]
                )
            )

        # Visibility health component
        visibility = weather.get('visibility_miles')
        if visibility is not None:
            visibility_status = self._get_health_status_for_visibility(visibility)
            health_components.append(
                ComponentHealth(
                    id=Entity.entity_id, # f"{icao}_visibility",
                    name="Visibility",
                    health=visibility_status,
                    messages=[
                        ComponentMessage(
                            message=f"Current visibility: {visibility} miles",
                            status=visibility_status
                        )
                    ]
                )
            )

        # Overall health status based on flight condition
        overall_health_status = self._get_health_status_for_condition(flight_condition)

        # Create entity
        entity = Entity(
            entity_id=f"weather_{icao}",
            description=description,
            created_time=time_now,
            expiry_time=expiry_time,
            is_live=True,

            # Identification
            aliases=Aliases(
                name=f"{airport['name']} ({icao})"
            ),

            # Location
            location=Location(
                position=Position(
                    latitude_degrees=airport['lat'],
                    longitude_degrees=airport['lon']
                )
            ),

            # Classification
            mil_view=MilView(
                # Set disposition based on flight condition
                disposition=disposition,
                environment=Environment.AIR
            ),

            # Type
            ontology=Ontology(
                template=Template.SENSOR_POINT_OF_INTEREST,
                platform_type="RADAR"  # Using RADAR for weather station
            ),

            # Health status
            health=Health(
                health_status=overall_health_status,
                components=health_components
            ),

            # Metadata
            provenance=Provenance(
                integration_name="METAR-Weather-Integration",
                data_type="aviation_weather",
                source_update_time=time_now
            )
        )

        return entity

    def _get_health_status_for_condition(self, condition: str) -> HealthStatus:
        """Map flight condition to health status"""
        if condition == "VFR":
            return HealthStatus.HEALTHY
        elif condition == "MVFR":
            return HealthStatus.WARN
        elif condition == "IFR":
            return HealthStatus.FAIL
        elif condition == "LIFR":
            return HealthStatus.FAIL
        else:
            return HealthStatus.OFFLINE

    def _get_health_status_for_temperature(self, temp_c: float) -> HealthStatus:
        """Map temperature to health status"""
        if temp_c < -20 or temp_c > 40:
            return HealthStatus.FAIL
        elif temp_c < -10 or temp_c > 35:
            return HealthStatus.WARN
        else:
            return HealthStatus.HEALTHY

    def _get_health_status_for_wind(self, wind_kt: float) -> HealthStatus:
        """Map wind speed to health status"""
        if wind_kt > 30:
            return HealthStatus.ERROR
        elif wind_kt > 15:
            return HealthStatus.WARN
        else:
            return HealthStatus.HEALTHY

    def _get_health_status_for_visibility(self, visibility_miles: float) -> HealthStatus:
        """Map visibility to health status"""
        if visibility_miles < 1:
            return HealthStatus.FAIL
        elif visibility_miles < 5:
            return HealthStatus.WARN
        else:
            return HealthStatus.HEALTHY

    async def publish_entity(self, entity: Entity) -> None:
        """
        Publish an entity to Lattice.

        Args:
            entity: Entity to publish
        """
        try:
            # Set up gRPC channel
            channel = Channel(host=self.lattice_url, port=443, ssl=True)
            stub = EntityManagerApiStub(channel)

            # Prepare metadata
            metadata = {
                'authorization': f"Bearer {self.environment_token}"
            }

            # Add sandboxes token if available
            if self.sandboxes_token:
                metadata['anduril-sandbox-authorization'] = f"Bearer {self.sandboxes_token}"

            # Create request
            request = PublishEntityRequest(entity=entity)

            # Send request
            await stub.publish_entity(request, metadata=metadata)

            # Close channel
            channel.close()

        except Exception as e:
            logger.error(f"Error publishing entity: {e}")
            raise

async def main():
    """Main entry point"""
    try:
        # Create and start integration
        integration = LatticeWeatherIntegration()
        await integration.start()
    except KeyboardInterrupt:
        logger.info("Integration stopped by user")
    except Exception as e:
        logger.error(f"Integration error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("METAR to Lattice Weather Integration")
    print("=" * 50)
    print()
    asyncio.run(main())
