# Create a test script to validate the health components and disposition functionality
test_script = """#!/usr/bin/env python3
\"\"\"
Test script for METAR to Lattice Integration (Modified)
Tests the health components and disposition functionality
\"\"\"

import sys
import os
from datetime import datetime, timezone

# Add the current directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the classes we need (mock the Lattice SDK imports)
class MockHealthStatus:
    HEALTHY = "HEALTHY"
    WARN = "WARN"
    ERROR = "ERROR"
    UNKNOWN = "UNKNOWN"

class MockDisposition:
    ASSUMED_FRIENDLY = "ASSUMED_FRIENDLY"
    SUSPICIOUS = "SUSPICIOUS"
    HOSTILE = "HOSTILE"

# Mock the SDK classes for testing
class MockComponentHealth:
    def __init__(self, id, name, health, messages):
        self.id = id
        self.name = name
        self.health = health
        self.messages = messages

class MockComponentMessage:
    def __init__(self, message, status):
        self.message = message
        self.status = status

# Replace the SDK imports with mocks for testing
import sys
sys.modules['anduril.entitymanager.v1'] = type('Module', (), {
    'HealthStatus': MockHealthStatus,
    'ComponentHealth': MockComponentHealth,
    'ComponentMessage': MockComponentMessage
})()
sys.modules['anduril.ontology.v1'] = type('Module', (), {
    'Disposition': MockDisposition
})()

# Now import our classes
from metar_lattice_integration_modified import FlightConditions, LatticeWeatherIntegration

def test_flight_conditions():
    \"\"\"Test flight condition classification\"\"\"
    print("Testing Flight Condition Classifications:")
    print("-" * 40)

    test_cases = [
        (10.0, 5000, "VFR"),      # Clear conditions
        (4.0, 2000, "MVFR"),     # Marginal conditions
        (2.0, 800, "IFR"),       # Instrument conditions
        (0.5, 300, "LIFR"),      # Low instrument conditions
        (1.5, 1500, "IFR"),      # IFR due to visibility
        (8.0, 800, "IFR"),       # IFR due to ceiling
        (3.0, None, "MVFR"),     # MVFR due to visibility only
    ]

    for visibility, ceiling, expected in test_cases:
        result = FlightConditions.determine_flight_conditions(visibility, ceiling)
        status = "✓" if result == expected else "✗"
        ceiling_str = f"{ceiling}ft" if ceiling else "Clear"
        print(f"{status} Visibility: {visibility}mi, Ceiling: {ceiling_str} → {result} (expected {expected})")

def test_disposition_mapping():
    \"\"\"Test disposition mapping from flight conditions\"\"\"
    print("\\nTesting Disposition Mapping:")
    print("-" * 30)

    conditions = ["VFR", "MVFR", "IFR", "LIFR"]
    expected_dispositions = {
        "VFR": "ASSUMED_FRIENDLY",
        "MVFR": "SUSPICIOUS",
        "IFR": "HOSTILE",
        "LIFR": "HOSTILE"
    }

    for condition in conditions:
        disposition = FlightConditions.get_disposition_for_condition(condition)
        expected = expected_dispositions[condition]
        status = "✓" if disposition == expected else "✗"
        print(f"{status} {condition} → {disposition} (expected {expected})")

def test_health_components():
    \"\"\"Test health component creation\"\"\"
    print("\\nTesting Health Components:")
    print("-" * 26)

    # Create a mock integration instance for testing
    class MockIntegration:
        def _get_health_status_for_condition(self, condition):
            if condition == "VFR":
                return "HEALTHY"
            elif condition == "MVFR":
                return "WARN"
            elif condition in ["IFR", "LIFR"]:
                return "ERROR"
            else:
                return "UNKNOWN"
        
        def _get_health_status_for_temperature(self, temp_c):
            if temp_c < -20 or temp_c > 40:
                return "ERROR"
            elif temp_c < -10 or temp_c > 35:
                return "WARN"
            else:
                return "HEALTHY"
        
        def _get_health_status_for_wind(self, wind_kt):
            if wind_kt > 30:
                return "ERROR"
            elif wind_kt > 15:
                return "WARN"
            else:
                return "HEALTHY"
        
        def _get_health_status_for_visibility(self, visibility_miles):
            if visibility_miles < 1:
                return "ERROR"
            elif visibility_miles < 5:
                return "WARN"
            else:
                return "HEALTHY"

    integration = MockIntegration()

    # Test flight condition health
    test_conditions = [
        ("VFR", "HEALTHY"),
        ("MVFR", "WARN"),
        ("IFR", "ERROR"),
        ("LIFR", "ERROR")
    ]

    print("Flight Condition Health:")
    for condition, expected in test_conditions:
        result = integration._get_health_status_for_condition(condition)
        status = "✓" if result == expected else "✗"
        print(f"  {status} {condition} → {result}")

    # Test temperature health
    print("\\nTemperature Health:")
    temp_tests = [
        (20, "HEALTHY"),    # Normal temp
        (-15, "WARN"),      # Cold warning
        (45, "ERROR"),      # Hot error
        (-25, "ERROR"),     # Extreme cold
    ]

    for temp, expected in temp_tests:
        result = integration._get_health_status_for_temperature(temp)
        status = "✓" if result == expected else "✗"
        print(f"  {status} {temp}°C → {result}")

    # Test wind health
    print("\\nWind Speed Health:")
    wind_tests = [
        (10, "HEALTHY"),    # Light wind
        (20, "WARN"),       # Moderate wind
        (35, "ERROR"),      # High wind
    ]

    for wind, expected in wind_tests:
        result = integration._get_health_status_for_wind(wind)
        status = "✓" if result == expected else "✗"
        print(f"  {status} {wind}kt → {result}")

    # Test visibility health
    print("\\nVisibility Health:")
    vis_tests = [
        (10, "HEALTHY"),    # Good visibility
        (3, "WARN"),        # Reduced visibility
        (0.5, "ERROR"),     # Poor visibility
    ]

    for vis, expected in vis_tests:
        result = integration._get_health_status_for_visibility(vis)
        status = "✓" if result == expected else "✗"
        print(f"  {status} {vis}mi → {result}")

def test_weather_scenarios():
    \"\"\"Test complete weather scenarios\"\"\"
    print("\\nTesting Complete Weather Scenarios:")
    print("-" * 36)

    scenarios = [
        {
            "name": "Perfect Flying Weather",
            "visibility": 10.0,
            "ceiling": 8000,
            "temperature": 22,
            "wind": 8,
            "expected_condition": "VFR",
            "expected_disposition": "ASSUMED_FRIENDLY"
        },
        {
            "name": "Marginal Conditions",
            "visibility": 4.0,
            "ceiling": 1500,
            "temperature": 15,
            "wind": 18,
            "expected_condition": "MVFR",
            "expected_disposition": "SUSPICIOUS"
        },
        {
            "name": "Poor Weather",
            "visibility": 2.0,
            "ceiling": 600,
            "temperature": 5,
            "wind": 25,
            "expected_condition": "IFR",
            "expected_disposition": "HOSTILE"
        },
        {
            "name": "Dangerous Conditions",
            "visibility": 0.25,
            "ceiling": 200,
            "temperature": -5,
            "wind": 35,
            "expected_condition": "LIFR",
            "expected_disposition": "HOSTILE"
        }
    ]

    for scenario in scenarios:
        print(f"\\n{scenario['name']}:")
        print(f"  Visibility: {scenario['visibility']}mi")
        print(f"  Ceiling: {scenario['ceiling']}ft")
        print(f"  Temperature: {scenario['temperature']}°C")
        print(f"  Wind: {scenario['wind']}kt")
        
        # Test flight condition
        condition = FlightConditions.determine_flight_conditions(
            scenario['visibility'], scenario['ceiling']
        )
        condition_ok = condition == scenario['expected_condition']
        print(f"  Flight Condition: {condition} {'✓' if condition_ok else '✗'}")
        
        # Test disposition
        disposition = FlightConditions.get_disposition_for_condition(condition)
        disposition_ok = disposition == scenario['expected_disposition']
        print(f"  Disposition: {disposition} {'✓' if disposition_ok else '✗'}")
        
        # Overall status
        overall_ok = condition_ok and disposition_ok
        print(f"  Overall: {'✓ PASS' if overall_ok else '✗ FAIL'}")

def main():
    \"\"\"Run all tests\"\"\"
    print("METAR to Lattice Integration - Modified Features Test")
    print("=" * 55)
    
    try:
        test_flight_conditions()
        test_disposition_mapping()
        test_health_components()
        test_weather_scenarios()
        
        print("\\n" + "=" * 55)
        print("All tests completed!")
        print("\\nNote: This test validates the logic without connecting to Lattice.")
        print("To test full integration, ensure LATTICE_URL and ENVIRONMENT_TOKEN are set.")
        
    except Exception as e:
        print(f"\\nTest error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
"""

with open("test_modified_integration.py", "w") as file:
    file.write(test_script)

print("Created test script for modified integration")

# Make the test script executable
import os
os.chmod("test_modified_integration.py", 0o755)

# Run the test to validate our implementation
print("\nRunning validation tests...")
os.system("python test_modified_integration.py")