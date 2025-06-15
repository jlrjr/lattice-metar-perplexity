#!/usr/bin/env python3
"""
METAR to Lattice Integration
============================

This program integrates METAR (Meteorological Aerodrome Reports) airport weather conditions 
with the Anduril Lattice SDK. It retrieves weather data for New England airports and 
publishes Lattice entities representing airports with their current weather conditions.

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
    Entity, MilView, Location, Position, Ontology, Template, Provenance
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

        # LIFR: Ceiling < 500' and/or visibility < 1 mile
        if ceiling_feet < 500 or visibility_miles < 1:
            return "LIFR"

        # IFR: Ceiling 500-999' and/or visibility 1-3 miles
        elif ceiling_feet < 1000 or visibility_miles < 3:
            return "IFR"

        # MVFR: Ceiling 1000-3000' and/or visibility 3-5 miles
        elif ceiling_feet < 3000 or visibility_miles < 5:
            return "MVFR"

        # VFR: Ceiling > 3000' and visibility > 5 miles
        else:
            return "VFR"

class NewEnglandAirports:
    """New England airports database with ICAO codes and information"""

    AIRPORTS = {
        # Massachusetts
        "KBOS": {"name": "General Edward Lawrence Logan International Airport", 
                "city": "Boston", "state": "MA", "lat": 42.36298, "lon": -71.00684},
        "KORH": {"name": "Worcester Regional Airport", 
                "city": "Worcester", "state": "MA", "lat": 42.26734, "lon": -71.87571},
        "KBED": {"name": "Laurence G. Hanscom Field", 
                "city": "Bedford", "state": "MA", "lat": 42.47000, "lon": -71.28900},
        "KACK": {"name": "Nantucket Memorial Airport", 
                "city": "Nantucket", "state": "MA", "lat": 41.25305, "lon": -70.06018},
        "KMVT": {"name": "Martha's Vineyard Airport", 
                "city": "Martha's Vineyard", "state": "MA", "lat": 41.39131, "lon": -70.61431},
        "KHYA": {"name": "Barnstable Municipal Airport", 
                "city": "Hyannis", "state": "MA", "lat": 41.66934, "lon": -70.28036},

        # New Hampshire
        "KMHT": {"name": "Manchester-Boston Regional Airport", 
                "city": "Manchester", "state": "NH", "lat": 42.93260, "lon": -71.43570},
        "KLEB": {"name": "Lebanon Municipal Airport", 
                "city": "Lebanon", "state": "NH", "lat": 43.62608, "lon": -72.30417},
        "KCON": {"name": "Concord Municipal Airport", 
                "city": "Concord", "state": "NH", "lat": 43.20272, "lon": -71.50228},

        # Connecticut  
        "KBDL": {"name": "Bradley International Airport", 
                "city": "Hartford/Windsor Locks", "state": "CT", "lat": 41.93887, "lon": -72.68323},
        "KHVN": {"name": "Tweed New Haven Airport", 
                "city": "New Haven", "state": "CT", "lat": 41.26364, "lon": -72.88679},
        "KGON": {"name": "Groton-New London Airport", 
                "city": "Groton/New London", "state": "CT", "lat": 41.33011, "lon": -72.04517},

        # Rhode Island
        "KPVD": {"name": "Theodore Francis Green Airport", 
                "city": "Providence/Warwick", "state": "RI", "lat": 41.73239, "lon": -71.42056},

        # Vermont
        "KBTV": {"name": "Patrick Leahy Burlington International Airport", 
                "city": "Burlington", "state": "VT", "lat": 44.47194, "lon": -73.15328},
        "KMPV": {"name": "Edward F. Knapp State Airport", 
                "city": "Montpelier", "state": "VT", "lat": 44.20350, "lon": -72.56233},

        # Maine
        "KBGR": {"name": "Bangor International Airport", 
                "city": "Bangor", "state": "ME", "lat": 44.80744, "lon": -68.82814},
        "KPWM": {"name": "Portland International Jetport", 
                "city": "Portland", "state": "ME", "lat": 43.64617, "lon": -70.30875},
        "KAUG": {"name": "Augusta State Airport", 
                "city": "Augusta", "state": "ME", "lat": 44.32061, "lon": -69.79733},
        "KBHB": {"name": "Hancock County-Bar Harbor Airport", 
                "city": "Bar Harbor", "state": "ME", "lat": 44.44975, "lon": -68.36158},
    }

    @classmethod
    def get_airports(cls) -> Dict[str, Dict]:
        """Get all New England airports"""
        return cls.AIRPORTS

    @classmethod
    def get_airport_info(cls, icao: str) -> Optional[Dict]:
        """Get specific airport information"""
        return cls.AIRPORTS.get(icao)

class MetarApiClient:
    """Client for retrieving METAR and TAF data from Aviation Weather Center API"""

    BASE_URL = "https://aviationweather.gov/api/data"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'AndurilLatticeWeatherIntegration/1.0'
        })

    def get_metar_data(self, icao_codes: List[str]) -> Dict[str, Dict]:
        """
        Retrieve METAR data for specified airports

        Args:
            icao_codes: List of ICAO airport codes

        Returns:
            Dictionary mapping ICAO codes to METAR data
        """
        try:
            # Join ICAO codes for API request
            stations_param = ",".join(icao_codes)

            # API endpoint for METAR data
            url = f"{self.BASE_URL}/metar"
            params = {
                'ids': stations_param,
                'format': 'json',
                'taf': 'false',
                'hours': '2'  # Get last 2 hours of data
            }

            logger.info(f"Requesting METAR data for {len(icao_codes)} airports")
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()

            # Parse response
            data = response.json()

            # Process METAR data
            metar_dict = {}
            for metar_data in data:
                icao = metar_data.get('icaoId', '').upper()
                if icao in icao_codes:
                    metar_dict[icao] = self._process_metar_data(metar_data)

            logger.info(f"Successfully retrieved METAR data for {len(metar_dict)} airports")
            return metar_dict

        except requests.RequestException as e:
            logger.error(f"Failed to retrieve METAR data: {e}")
            return {}
        except Exception as e:
            logger.error(f"Error processing METAR data: {e}")
            return {}

    def get_taf_data(self, icao_codes: List[str]) -> Dict[str, Dict]:
        """
        Retrieve TAF (Terminal Aerodrome Forecast) data for specified airports

        Args:
            icao_codes: List of ICAO airport codes

        Returns:
            Dictionary mapping ICAO codes to TAF data
        """
        try:
            stations_param = ",".join(icao_codes)

            url = f"{self.BASE_URL}/taf"
            params = {
                'ids': stations_param,
                'format': 'json'
            }

            logger.info(f"Requesting TAF data for {len(icao_codes)} airports")
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()

            taf_dict = {}
            for taf_data in data:
                icao = taf_data.get('icaoId', '').upper()
                if icao in icao_codes:
                    taf_dict[icao] = self._process_taf_data(taf_data)

            logger.info(f"Successfully retrieved TAF data for {len(taf_dict)} airports")
            return taf_dict

        except requests.RequestException as e:
            logger.error(f"Failed to retrieve TAF data: {e}")
            return {}
        except Exception as e:
            logger.error(f"Error processing TAF data: {e}")
            return {}

    def _process_metar_data(self, metar_data: Dict) -> Dict:
        """Process raw METAR data from API"""
        try:
            raw_text = metar_data.get('rawOb', '')

            # Parse METAR using python-metar library
            try:
                metar_obj = Metar.Metar(raw_text)

                # Extract key weather information
                visibility_miles = None
                if metar_obj.vis:
                    visibility_miles = metar_obj.vis.value('SM')

                ceiling_feet = None
                if metar_obj.sky:
                    for layer in metar_obj.sky:
                        if layer[0] in ['BKN', 'OVC']:  # Broken or Overcast
                            if layer[1]:
                                ceiling_feet = layer[1].value('FT')
                                break

                # Determine flight conditions
                flight_condition = FlightConditions.determine_flight_conditions(
                    visibility_miles or 10.0, ceiling_feet
                )

                return {
                    'raw_text': raw_text,
                    'parsed_time': metar_data.get('obsTime'),
                    'temperature_c': metar_obj.temp.value('C') if metar_obj.temp else None,
                    'dewpoint_c': metar_obj.dewpt.value('C') if metar_obj.dewpt else None,
                    'wind_direction': metar_obj.wind_dir.value() if metar_obj.wind_dir else None,
                    'wind_speed_kt': metar_obj.wind_speed.value('KT') if metar_obj.wind_speed else None,
                    'visibility_miles': visibility_miles,
                    'ceiling_feet': ceiling_feet,
                    'pressure_mb': metar_obj.press.value('MB') if metar_obj.press else None,
                    'flight_condition': flight_condition,
                    'weather_conditions': str(metar_obj.weather) if metar_obj.weather else None,
                    'sky_conditions': self._format_sky_conditions(metar_obj.sky),
                }

            except Exception as parse_error:
                logger.warning(f"Failed to parse METAR: {parse_error}")
                return {
                    'raw_text': raw_text,
                    'parsed_time': metar_data.get('obsTime'),
                    'flight_condition': 'UNKNOWN',
                    'parse_error': str(parse_error)
                }

        except Exception as e:
            logger.error(f"Error processing METAR data: {e}")
            return {'error': str(e)}

    def _process_taf_data(self, taf_data: Dict) -> Dict:
        """Process raw TAF data from API"""
        try:
            return {
                'raw_text': taf_data.get('rawTAF', ''),
                'issued_time': taf_data.get('bulletinTime'),
                'valid_from': taf_data.get('validTimeFrom'),
                'valid_to': taf_data.get('validTimeTo'),
            }
        except Exception as e:
            logger.error(f"Error processing TAF data: {e}")
            return {'error': str(e)}

    def _format_sky_conditions(self, sky_layers) -> str:
        """Format sky condition layers into readable string"""
        if not sky_layers:
            return "Clear"

        conditions = []
        for layer in sky_layers:
            coverage = layer[0]
            altitude = layer[1].value('FT') if layer[1] else 'unknown'
            conditions.append(f"{coverage} {altitude}ft")

        return ", ".join(conditions)

class LatticeWeatherIntegration:
    """Main integration class for publishing weather entities to Lattice"""

    def __init__(self):
        # Get configuration from environment variables
        self.lattice_url = os.getenv('LATTICE_URL')
        self.environment_token = os.getenv('ENVIRONMENT_TOKEN')
        self.sandboxes_token = os.getenv('SANDBOXES_TOKEN')

        # Validate configuration
        if not self.lattice_url or not self.environment_token:
            raise ValueError(
                "LATTICE_URL and ENVIRONMENT_TOKEN environment variables must be set"
            )

        # Set up metadata for gRPC calls
        self.metadata = {
            'authorization': f"Bearer {self.environment_token}",
        }

        if self.sandboxes_token:
            self.metadata['anduril-sandbox-authorization'] = f"Bearer {self.sandboxes_token}"

        # Initialize clients
        self.metar_client = MetarApiClient()
        self.airports = NewEnglandAirports.get_airports()

        logger.info(f"Initialized Lattice integration for {len(self.airports)} airports")

    async def publish_weather_entity(self, icao: str, airport_info: Dict, 
                                   metar_data: Dict, taf_data: Optional[Dict] = None) -> bool:
        """
        Publish a weather entity to Lattice for a specific airport

        Args:
            icao: ICAO airport code
            airport_info: Airport information dictionary
            metar_data: METAR weather data
            taf_data: Optional TAF forecast data

        Returns:
            True if successful, False otherwise
        """
        try:
            channel = Channel(host=self.lattice_url, port=443, ssl=True)
            stub = EntityManagerApiStub(channel)

            # Create unique entity ID for this airport
            entity_id = f"weather-{icao.lower()}-{uuid4()}"

            # Get current time
            current_time = datetime.now(timezone.utc)

            # Create entity name
            flight_condition = metar_data.get('flight_condition', 'UNKNOWN')
            entity_name = f"{airport_info['name']} ({icao}) - {flight_condition}"

            # Create description with weather summary
            description_parts = [
                f"Airport: {airport_info['name']}",
                f"Location: {airport_info['city']}, {airport_info['state']}",
                f"Flight Conditions: {flight_condition}",
            ]

            if 'temperature_c' in metar_data and metar_data['temperature_c'] is not None:
                temp_f = (metar_data['temperature_c'] * 9/5) + 32
                description_parts.append(f"Temperature: {temp_f:.1f}°F ({metar_data['temperature_c']:.1f}°C)")

            if 'wind_speed_kt' in metar_data and metar_data['wind_speed_kt'] is not None:
                wind_dir = metar_data.get('wind_direction', 'VRB')
                description_parts.append(f"Wind: {wind_dir}° at {metar_data['wind_speed_kt']} knots")

            if 'visibility_miles' in metar_data and metar_data['visibility_miles'] is not None:
                description_parts.append(f"Visibility: {metar_data['visibility_miles']} miles")

            description = " | ".join(description_parts)

            # Create Lattice entity
            entity = Entity(
                entity_id=entity_id,
                created_time=current_time,
                expiry_time=current_time + timedelta(hours=2),  # Expire in 2 hours
                aliases=Aliases(name=entity_name),
                description=description,

                # Set military view (neutral/informational)
                mil_view=MilView(
                    disposition=Disposition.ASSUMED_FRIENDLY,
                    environment=Environment.SURFACE
                ),

                # Set location
                location=Location(
                    position=Position(
                        latitude_degrees=airport_info['lat'],
                        longitude_degrees=airport_info['lon'],
                        altitude_hae_meters=0.0  # Airport elevation (simplified)
                    )
                ),

                # Set ontology - use sensor point of interest for weather stations
                ontology=Ontology(
                    template=Template.SENSOR_POINT_OF_INTEREST,
                    platform_type="WEATHER_STATION"
                ),

                # Set provenance
                provenance=Provenance(
                    integration_name="metar_weather_integration",
                    data_type="aviation_weather",
                    source_update_time=current_time
                ),

                is_live=True
            )

            # Publish entity
            request = PublishEntityRequest(entity=entity)
            response = await stub.publish_entity(request, metadata=self.metadata)

            channel.close()

            logger.info(f"Successfully published weather entity for {icao}: {entity_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to publish weather entity for {icao}: {e}")
            return False

    async def run_integration(self, update_interval_minutes: int = 30):
        """
        Run the weather integration continuously

        Args:
            update_interval_minutes: How often to update weather data
        """
        logger.info(f"Starting METAR to Lattice integration with {update_interval_minutes}-minute updates")

        while True:
            try:
                # Get all ICAO codes
                icao_codes = list(self.airports.keys())

                # Retrieve METAR data
                logger.info("Retrieving METAR data...")
                metar_data = self.metar_client.get_metar_data(icao_codes)

                # Retrieve TAF data
                logger.info("Retrieving TAF data...")
                taf_data = self.metar_client.get_taf_data(icao_codes)

                # Publish entities for each airport with weather data
                successful_publishes = 0
                total_airports = len(icao_codes)

                for icao in icao_codes:
                    airport_info = self.airports[icao]
                    metar_info = metar_data.get(icao)
                    taf_info = taf_data.get(icao)

                    if metar_info and not metar_info.get('error'):
                        success = await self.publish_weather_entity(
                            icao, airport_info, metar_info, taf_info
                        )
                        if success:
                            successful_publishes += 1
                    else:
                        logger.warning(f"No valid METAR data for {icao}")

                logger.info(
                    f"Published {successful_publishes}/{total_airports} weather entities to Lattice"
                )

                # Wait for next update cycle
                logger.info(f"Waiting {update_interval_minutes} minutes until next update...")
                await asyncio.sleep(update_interval_minutes * 60)

            except KeyboardInterrupt:
                logger.info("Integration stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in integration loop: {e}")
                logger.info("Retrying in 5 minutes...")
                await asyncio.sleep(300)  # Wait 5 minutes before retrying

def main():
    """Main entry point"""
    print("METAR to Lattice Weather Integration")
    print("=" * 50)
    print()

    # Check environment variables
    required_env_vars = ['LATTICE_URL', 'ENVIRONMENT_TOKEN']
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]

    if missing_vars:
        print("Error: The following environment variables must be set:")
        for var in missing_vars:
            print(f"  - {var}")
        print()
        print("Example:")
        print("  export LATTICE_URL='your-lattice-instance.com'")
        print("  export ENVIRONMENT_TOKEN='your-bearer-token'")
        print("  export SANDBOXES_TOKEN='your-sandbox-token'  # Optional, for sandboxes")
        sys.exit(1)

    try:
        # Create and run integration
        integration = LatticeWeatherIntegration()

        # Run the integration
        asyncio.run(integration.run_integration(update_interval_minutes=30))

    except Exception as e:
        logger.error(f"Failed to start integration: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
