# Create requirements.txt file
requirements_content = '''# Anduril Lattice SDK
anduril-lattice-sdk>=1.8.0

# gRPC and networking
grpclib>=0.4.3
certifi>=2023.7.22

# HTTP requests
requests>=2.31.0

# METAR parsing
metar>=1.11.0

# Additional utilities
python-dateutil>=2.8.2
'''

with open('requirements.txt', 'w') as f:
    f.write(requirements_content)

print("Created requirements.txt")

# Create a configuration template file
config_template = '''# METAR to Lattice Integration Configuration Template
# Copy this file to config.yml and fill in your values

# Lattice Configuration
lattice:
  url: "your-lattice-instance.com"  # Your Lattice URL (without https://)
  environment_token: "your-environment-bearer-token"  # Your environment token
  sandboxes_token: "your-sandbox-token"  # Optional: for Lattice Sandboxes

# Integration Settings
integration:
  update_interval_minutes: 30  # How often to update weather data
  entity_expiry_hours: 2      # How long entities remain valid
  
# Logging Configuration
logging:
  level: "INFO"  # DEBUG, INFO, WARNING, ERROR
  file: "metar_integration.log"  # Log file path

# Airport Selection (optional - leave empty to use all New England airports)
airports:
  # Uncomment and modify to limit to specific airports
  # include_only:
  #   - KBOS  # Boston Logan
  #   - KMHT  # Manchester
  #   - KBDL  # Bradley/Hartford
  
  # Uncomment to exclude specific airports
  # exclude:
  #   - KPVC  # Provincetown (seasonal)
'''

with open('config_template.yml', 'w') as f:
    f.write(config_template)

print("Created config_template.yml")

# Create setup script
setup_script = '''#!/bin/bash
# Setup script for METAR to Lattice Integration

echo "Setting up METAR to Lattice Integration..."

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Create config file from template if it doesn't exist
if [ ! -f "config.yml" ]; then
    echo "Creating config.yml from template..."
    cp config_template.yml config.yml
    echo "Please edit config.yml with your Lattice credentials"
fi

echo "Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit config.yml with your Lattice credentials"
echo "2. Set environment variables:"
echo "   export LATTICE_URL='your-lattice-instance.com'"
echo "   export ENVIRONMENT_TOKEN='your-bearer-token'"
echo "   export SANDBOXES_TOKEN='your-sandbox-token'  # Optional"
echo "3. Run the integration:"
echo "   python metar_lattice_integration.py"
'''

with open('setup.sh', 'w') as f:
    f.write(setup_script)

print("Created setup.sh")

# Create a comprehensive README
readme_content = '''# METAR to Lattice Weather Integration

A Python application that integrates METAR (Meteorological Aerodrome Reports) airport weather conditions with the Anduril Lattice SDK. This integration retrieves real-time weather data for New England airports and publishes Lattice entities representing airports with their current weather conditions and flight categories (VFR, MVFR, IFR, LIFR).

## Features

- **Real-time Weather Data**: Retrieves current METAR and TAF reports from the FAA Aviation Weather Center
- **Flight Condition Classification**: Automatically determines VFR, MVFR, IFR, or LIFR conditions based on visibility and ceiling
- **Comprehensive Airport Coverage**: Includes 19+ major New England airports across all 6 states
- **Lattice Integration**: Publishes weather data as Lattice entities with proper geolocation and metadata
- **Automatic Updates**: Continuously monitors weather conditions with configurable update intervals
- **Error Handling**: Robust error handling with logging and automatic retry logic

## New England Airports Included

### Massachusetts
- KBOS: General Edward Lawrence Logan International Airport (Boston)
- KORH: Worcester Regional Airport
- KBED: Laurence G. Hanscom Field (Bedford)
- KACK: Nantucket Memorial Airport
- KMVT: Martha's Vineyard Airport
- KHYA: Barnstable Municipal Airport (Hyannis)

### New Hampshire
- KMHT: Manchester-Boston Regional Airport
- KLEB: Lebanon Municipal Airport
- KCON: Concord Municipal Airport

### Connecticut
- KBDL: Bradley International Airport (Hartford/Windsor Locks)
- KHVN: Tweed New Haven Airport
- KGON: Groton-New London Airport

### Rhode Island
- KPVD: Theodore Francis Green Airport (Providence/Warwick)

### Vermont
- KBTV: Patrick Leahy Burlington International Airport
- KMPV: Edward F. Knapp State Airport (Montpelier)

### Maine
- KBGR: Bangor International Airport
- KPWM: Portland International Jetport
- KAUG: Augusta State Airport
- KBHB: Hancock County-Bar Harbor Airport

## Flight Condition Classifications

The system automatically determines flight conditions based on FAA standards:

- **VFR (Visual Flight Rules)**: Ceiling > 3,000' AGL and visibility > 5 miles
- **MVFR (Marginal VFR)**: Ceiling 1,000-3,000' AGL and/or visibility 3-5 miles
- **IFR (Instrument Flight Rules)**: Ceiling 500-999' AGL and/or visibility 1-3 miles
- **LIFR (Low IFR)**: Ceiling < 500' AGL and/or visibility < 1 mile

## Prerequisites

- Python 3.9 or higher
- Access to an Anduril Lattice environment
- Valid Lattice API credentials (Environment Token)
- Internet connection for accessing FAA weather data

## Installation

1. **Clone or download the integration files**

2. **Run the setup script**:
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```

3. **Or install manually**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

## Configuration

### Environment Variables

Set the following environment variables:

```bash
export LATTICE_URL="your-lattice-instance.com"
export ENVIRONMENT_TOKEN="your-bearer-token"
export SANDBOXES_TOKEN="your-sandbox-token"  # Optional, for Lattice Sandboxes
```

### Alternative Configuration

You can also copy `config_template.yml` to `config.yml` and edit it with your settings.

## Usage

### Basic Usage

```bash
# Activate virtual environment
source .venv/bin/activate

# Run the integration
python metar_lattice_integration.py
```

### Advanced Usage

The integration will:
1. Connect to the FAA Aviation Weather Center API
2. Retrieve current METAR and TAF data for all New England airports
3. Parse weather data and determine flight conditions
4. Create Lattice entities for each airport with weather information
5. Publish entities to your Lattice environment
6. Repeat every 30 minutes (configurable)

### Sample Output

```
METAR to Lattice Weather Integration
==================================================

2025-06-15 03:40:12 - INFO - Initialized Lattice integration for 19 airports
2025-06-15 03:40:12 - INFO - Starting METAR to Lattice integration with 30-minute updates
2025-06-15 03:40:12 - INFO - Retrieving METAR data...
2025-06-15 03:40:14 - INFO - Successfully retrieved METAR data for 18 airports
2025-06-15 03:40:14 - INFO - Retrieving TAF data...
2025-06-15 03:40:16 - INFO - Successfully retrieved TAF data for 17 airports
2025-06-15 03:40:18 - INFO - Successfully published weather entity for KBOS: General Edward Lawrence Logan International Airport (KBOS) - VFR
2025-06-15 03:40:19 - INFO - Successfully published weather entity for KMHT: Manchester-Boston Regional Airport (KMHT) - MVFR
...
2025-06-15 03:40:45 - INFO - Published 18/19 weather entities to Lattice
```

## Data Sources

- **METAR Data**: FAA Aviation Weather Center (aviationweather.gov)
- **TAF Data**: FAA Aviation Weather Center (aviationweather.gov)
- **Airport Information**: Compiled from official FAA records

## Lattice Entity Structure

Each airport weather entity includes:

- **Entity Type**: Sensor Point of Interest (weather station)
- **Location**: Precise airport coordinates
- **Metadata**: Airport name, ICAO code, city, state
- **Weather Data**: 
  - Flight conditions (VFR/MVFR/IFR/LIFR)
  - Temperature and dewpoint
  - Wind direction and speed
  - Visibility and ceiling
  - Raw METAR report
  - TAF forecast (when available)

## Error Handling

The integration includes robust error handling:

- **Network failures**: Automatic retry with exponential backoff
- **API rate limiting**: Respects FAA API guidelines
- **Parsing errors**: Graceful handling of malformed weather data
- **Lattice connectivity**: Automatic reconnection attempts

## Logging

All activities are logged with configurable levels:
- **INFO**: Normal operations and successful publishes
- **WARNING**: Missing data or minor issues
- **ERROR**: Failed API calls or publish attempts
- **DEBUG**: Detailed troubleshooting information

## Customization

### Adding Additional Airports

To add more airports, edit the `NewEnglandAirports.AIRPORTS` dictionary in the main file:

```python
"KXXX": {
    "name": "Airport Name",
    "city": "City",
    "state": "ST",
    "lat": 00.0000,
    "lon": -00.0000
}
```

### Modifying Update Frequency

Change the `update_interval_minutes` parameter in the `run_integration()` call:

```python
await integration.run_integration(update_interval_minutes=15)  # Update every 15 minutes
```

### Filtering Airports

Modify the integration to include only specific airports:

```python
# Only include major airports
major_airports = ['KBOS', 'KMHT', 'KBDL', 'KPVD', 'KBTV', 'KBGR', 'KPWM']
icao_codes = [code for code in icao_codes if code in major_airports]
```

## Troubleshooting

### Common Issues

1. **"LATTICE_URL and ENVIRONMENT_TOKEN environment variables must be set"**
   - Ensure environment variables are properly exported
   - Check that tokens are valid and not expired

2. **"Failed to retrieve METAR data"**
   - Check internet connectivity
   - Verify FAA weather API is accessible
   - Check for API rate limiting

3. **"Failed to publish weather entity"**
   - Verify Lattice URL and credentials
   - Check network connectivity to Lattice
   - Ensure proper SSL/TLS configuration

### Debug Mode

Enable debug logging by setting the environment variable:

```bash
export PYTHONLOG=DEBUG
```

## API Rate Limits

The integration respects FAA Aviation Weather Center API guidelines:
- Maximum 1 request per second
- Batch requests for multiple airports
- Uses appropriate User-Agent headers

## Security Considerations

- Store Lattice credentials securely
- Use environment variables or secure configuration files
- Rotate tokens regularly
- Monitor for unauthorized access

## Contributing

This integration was developed as part of the Anduril Lattice SDK Developer Relations program. For questions or support, contact your Anduril representative.

## License

This software is provided under the Anduril SDK Terms of Use. See the Lattice SDK documentation for details.

## Support

For technical support:
1. Check the troubleshooting section above
2. Review Lattice SDK documentation
3. Contact your Anduril representative
4. Check the Anduril Developer Portal

---

**Note**: This integration is designed for demonstration and development purposes. For production use, additional considerations such as high availability, monitoring, and security hardening may be required.
'''

with open('README.md', 'w') as f:
    f.write(readme_content)

print("Created comprehensive README.md")

# Create a simple test script
test_script = '''#!/usr/bin/env python3
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
    print("\\nTesting Airport Database:")
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
    print("\\nTesting METAR API Client:")
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
        print(f"\\nSkipping METAR API test due to error: {e}")
    
    print("\\nTest suite completed.")

if __name__ == "__main__":
    main()
'''

with open('test_integration.py', 'w') as f:
    f.write(test_script)

print("Created test_integration.py")

print("\nAll files created successfully!")
print("\nFiles generated:")
print("- metar_lattice_integration.py (main program)")
print("- requirements.txt")
print("- config_template.yml") 
print("- setup.sh")
print("- README.md")
print("- test_integration.py")