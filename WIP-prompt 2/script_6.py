# Let's run the test manually to see what's working
import os
import sys

# Create a simplified test to validate our logic
def test_flight_conditions_logic():
    """Test the flight condition logic directly"""
    
    # Define the logic as in our implementation
    def determine_flight_conditions(visibility_miles: float, ceiling_feet: int = None) -> str:
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
    
    def get_disposition_for_condition(flight_condition: str) -> str:
        if flight_condition == "VFR":
            return "ASSUMED_FRIENDLY"
        elif flight_condition == "MVFR":
            return "SUSPICIOUS"
        else:  # IFR or LIFR
            return "HOSTILE"

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

    all_passed = True
    for visibility, ceiling, expected in test_cases:
        result = determine_flight_conditions(visibility, ceiling)
        status = "✓" if result == expected else "✗"
        if result != expected:
            all_passed = False
        ceiling_str = f"{ceiling}ft" if ceiling else "Clear"
        print(f"{status} Visibility: {visibility}mi, Ceiling: {ceiling_str} → {result} (expected {expected})")

    print(f"\nFlight Conditions Test: {'PASSED' if all_passed else 'FAILED'}")

    print("\nTesting Disposition Mapping:")
    print("-" * 30)

    conditions = ["VFR", "MVFR", "IFR", "LIFR"]
    expected_dispositions = {
        "VFR": "ASSUMED_FRIENDLY",
        "MVFR": "SUSPICIOUS", 
        "IFR": "HOSTILE",
        "LIFR": "HOSTILE"
    }

    disposition_passed = True
    for condition in conditions:
        disposition = get_disposition_for_condition(condition)
        expected = expected_dispositions[condition]
        status = "✓" if disposition == expected else "✗"
        if disposition != expected:
            disposition_passed = False
        print(f"{status} {condition} → {disposition} (expected {expected})")

    print(f"\nDisposition Mapping Test: {'PASSED' if disposition_passed else 'FAILED'}")

    # Test health status logic
    def get_health_status_for_condition(condition):
        if condition == "VFR":
            return "HEALTHY"
        elif condition == "MVFR":
            return "WARN"
        elif condition in ["IFR", "LIFR"]:
            return "ERROR"
        else:
            return "UNKNOWN"
    
    def get_health_status_for_temperature(temp_c):
        if temp_c < -20 or temp_c > 40:
            return "ERROR"
        elif temp_c < -10 or temp_c > 35:
            return "WARN"
        else:
            return "HEALTHY"
    
    def get_health_status_for_wind(wind_kt):
        if wind_kt > 30:
            return "ERROR"
        elif wind_kt > 15:
            return "WARN"
        else:
            return "HEALTHY"
    
    def get_health_status_for_visibility(visibility_miles):
        if visibility_miles < 1:
            return "ERROR"
        elif visibility_miles < 5:
            return "WARN"
        else:
            return "HEALTHY"

    print("\nTesting Health Component Logic:")
    print("-" * 32)

    # Test health component mappings
    health_tests = [
        ("Flight Condition", [
            ("VFR", "HEALTHY"),
            ("MVFR", "WARN"),
            ("IFR", "ERROR"),
            ("LIFR", "ERROR")
        ], get_health_status_for_condition),
        ("Temperature", [
            (20, "HEALTHY"),
            (-15, "WARN"),
            (45, "ERROR"),
            (-25, "ERROR")
        ], get_health_status_for_temperature),
        ("Wind Speed", [
            (10, "HEALTHY"),
            (20, "WARN"),
            (35, "ERROR")
        ], get_health_status_for_wind),
        ("Visibility", [
            (10, "HEALTHY"),
            (3, "WARN"),
            (0.5, "ERROR")
        ], get_health_status_for_visibility)
    ]

    health_passed = True
    for test_name, test_cases, test_func in health_tests:
        print(f"\n{test_name} Health:")
        for test_value, expected in test_cases:
            result = test_func(test_value)
            status = "✓" if result == expected else "✗"
            if result != expected:
                health_passed = False
            unit = "°C" if test_name == "Temperature" else ("kt" if test_name == "Wind Speed" else ("mi" if test_name == "Visibility" else ""))
            print(f"  {status} {test_value}{unit} → {result}")

    print(f"\nHealth Components Test: {'PASSED' if health_passed else 'FAILED'}")

    # Complete scenario test
    print("\nTesting Complete Weather Scenarios:")
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

    scenario_passed = True
    for scenario in scenarios:
        print(f"\n{scenario['name']}:")
        print(f"  Visibility: {scenario['visibility']}mi, Ceiling: {scenario['ceiling']}ft")
        print(f"  Temperature: {scenario['temperature']}°C, Wind: {scenario['wind']}kt")
        
        # Test flight condition
        condition = determine_flight_conditions(scenario['visibility'], scenario['ceiling'])
        condition_ok = condition == scenario['expected_condition']
        print(f"  Flight Condition: {condition} {'✓' if condition_ok else '✗'}")
        
        # Test disposition
        disposition = get_disposition_for_condition(condition)
        disposition_ok = disposition == scenario['expected_disposition']
        print(f"  Disposition: {disposition} {'✓' if disposition_ok else '✗'}")
        
        # Overall status
        overall_ok = condition_ok and disposition_ok
        if not overall_ok:
            scenario_passed = False
        print(f"  Result: {'✓ PASS' if overall_ok else '✗ FAIL'}")

    print(f"\nScenario Tests: {'PASSED' if scenario_passed else 'FAILED'}")

    # Overall test result
    all_tests_passed = all_passed and disposition_passed and health_passed and scenario_passed
    print("\n" + "=" * 55)
    print(f"OVERALL TEST RESULT: {'✓ ALL TESTS PASSED' if all_tests_passed else '✗ SOME TESTS FAILED'}")
    print("=" * 55)

    return all_tests_passed

# Run the test
test_result = test_flight_conditions_logic()
print(f"\nTest completed with result: {test_result}")