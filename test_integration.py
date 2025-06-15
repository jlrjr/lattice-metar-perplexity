#!/usr/bin/env python3
"""
Test script for METAR to Lattice Integration
Tests the weather data retrieval and parsing functionality without Lattice
"""

import asyncio
import sys
import os

# Add the current directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from metar_lattice_integration import MetarApiClient, NewEnglandAirports, FlightConditions

def test_flight_conditions():
    """Test flight condition classification"""
    print("Testing Flight Condition Classifications:")
    print("-" * 40)

    test_cases = [
        (10.0, 5000, "VFR"),      # Clear conditions
        (4.0, 2000, "MVFR"),     # Marginal conditions
        (2.0, 800, "IFR"),       # Instrument conditions
        (0.5, 300, "LIFR"),      # Low instrument conditions
    ]

    for visibility, ceiling, expected in test_cases:
        result = FlightConditions.determine_flight_conditions(visibility, ceiling)
        status = "✓" if result == expected else "✗"
        print(f"{status} Visibility: {visibility}mi, Ceiling: {ceiling}ft → {result} (expected {expected})")

def test_airports():
    """Test airport database"""
    print("\nTesting Airport Database:")
    print("-" * 30)

    airports = NewEnglandAirports.get_airports()
    print(f"Total airports: {len(airports)}")

    # Group by state
    by_state = {}
    for icao, info in airports.items():
        state = info['state']
        if state not in by_state:
            by_state[state] = 0
        by_state[state] += 1

    for state, count in sorted(by_state.items()):
        print(f"  {state}: {count} airports")

async def test_metar_api():
    """Test METAR API client"""
    print("\nTesting METAR API Client:")
    print("-" * 28)

    client = MetarApiClient()

    # Test with a few major airports
    test_airports = ['KBOS', 'KMHT', 'KBDL']

    try:
        print(f"Requesting METAR data for: {', '.join(test_airports)}")
        metar_data = client.get_metar_data(test_airports)

        print(f"Received data for {len(metar_data)} airports:")

        for icao, data in metar_data.items():
            if 'error' not in data:
                fc = data.get('flight_condition', 'UNKNOWN')
                temp = data.get('temperature_c')
                visibility = data.get('visibility_miles')
                print(f"  {icao}: {fc}, {temp}°C, {visibility}mi visibility")
            else:
                print(f"  {icao}: Error - {data['error']}")

    except Exception as e:
        print(f"Error testing METAR API: {e}")

def main():
    """Run all tests"""
    print("METAR to Lattice Integration - Test Suite")
    print("=" * 50)

    test_flight_conditions()
    test_airports()

    # Only run API test if we have internet connectivity
    try:
        asyncio.run(test_metar_api())
    except Exception as e:
        print(f"\nSkipping METAR API test due to error: {e}")

    print("\nTest suite completed.")

if __name__ == "__main__":
    main()
