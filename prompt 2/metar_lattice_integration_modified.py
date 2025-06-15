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
