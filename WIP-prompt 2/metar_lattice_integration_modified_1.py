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

