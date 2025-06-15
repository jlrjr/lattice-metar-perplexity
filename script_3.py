# Create a sample usage script that demonstrates how to use the integration
sample_usage = '''#!/usr/bin/env python3
"""
Sample Usage Script for METAR to Lattice Integration
Shows how to use the integration with different configurations
"""

import asyncio
import os
from datetime import datetime
from metar_lattice_integration import (
    LatticeWeatherIntegration, 
    MetarApiClient, 
    NewEnglandAirports,
    FlightConditions
)

async def sample_basic_usage():
    """Basic usage example - single weather data retrieval"""
    print("=== Basic Usage Example ===")
    
    # Initialize METAR client
    client = MetarApiClient()
    
    # Get weather for Boston Logan
    airports = ['KBOS']
    print(f"Getting weather for {airports}")
    
    metar_data = client.get_metar_data(airports)
    
    for icao, data in metar_data.items():
        if 'error' not in data:
            print(f"\\nAirport: {icao}")
            print(f"Flight Condition: {data.get('flight_condition', 'Unknown')}")
            print(f"Temperature: {data.get('temperature_c', 'N/A')}°C")
            print(f"Visibility: {data.get('visibility_miles', 'N/A')} miles")
            print(f"Wind: {data.get('wind_direction', 'N/A')}° at {data.get('wind_speed_kt', 'N/A')} knots")
            print(f"Raw METAR: {data.get('raw_text', 'N/A')}")

async def sample_multiple_airports():
    """Example with multiple airports"""
    print("\\n=== Multiple Airports Example ===")
    
    client = MetarApiClient()
    
    # Get weather for major New England airports
    major_airports = ['KBOS', 'KMHT', 'KBDL', 'KPVD', 'KBTV', 'KBGR']
    print(f"Getting weather for {len(major_airports)} major airports")
    
    metar_data = client.get_metar_data(major_airports)
    
    print(f"\\nWeather Summary:")
    print("-" * 80)
    print(f"{'ICAO':<6} {'Condition':<8} {'Temp(°C)':<8} {'Visibility':<12} {'Wind':<15}")
    print("-" * 80)
    
    for icao in major_airports:
        data = metar_data.get(icao, {})
        if 'error' not in data:
            condition = data.get('flight_condition', 'Unknown')
            temp = f"{data.get('temperature_c', 'N/A')}"
            vis = f"{data.get('visibility_miles', 'N/A')} mi"
            wind_dir = data.get('wind_direction', 'N/A')
            wind_speed = data.get('wind_speed_kt', 'N/A')
            wind = f"{wind_dir}°@{wind_speed}kt"
            
            print(f"{icao:<6} {condition:<8} {temp:<8} {vis:<12} {wind:<15}")
        else:
            print(f"{icao:<6} {'ERROR':<8} {'N/A':<8} {'N/A':<12} {'N/A':<15}")

def sample_flight_conditions():
    """Example of flight condition classification"""
    print("\\n=== Flight Condition Classification Examples ===")
    
    test_scenarios = [
        {"visibility": 10.0, "ceiling": 5000, "description": "Clear day"},
        {"visibility": 4.0, "ceiling": 2500, "description": "Hazy conditions"},
        {"visibility": 2.0, "ceiling": 800, "description": "Overcast low clouds"},
        {"visibility": 0.5, "ceiling": 200, "description": "Fog/low visibility"},
        {"visibility": 6.0, "ceiling": 1500, "description": "Broken clouds"},
    ]
    
    print(f"{'Visibility':<12} {'Ceiling':<10} {'Condition':<10} {'Description'}")
    print("-" * 60)
    
    for scenario in test_scenarios:
        vis = scenario["visibility"]
        ceil = scenario["ceiling"]
        desc = scenario["description"]
        condition = FlightConditions.determine_flight_conditions(vis, ceil)
        
        print(f"{vis} miles{'':<4} {ceil} ft{'':<4} {condition:<10} {desc}")

async def sample_lattice_integration():
    """Example of full Lattice integration (requires credentials)"""
    print("\\n=== Lattice Integration Example ===")
    
    # Check if credentials are available
    if not os.getenv('LATTICE_URL') or not os.getenv('ENVIRONMENT_TOKEN'):
        print("Skipping Lattice integration - credentials not configured")
        print("To run this example, set:")
        print("  export LATTICE_URL='your-lattice-instance.com'")
        print("  export ENVIRONMENT_TOKEN='your-bearer-token'")
        return
    
    try:
        # Initialize integration
        integration = LatticeWeatherIntegration()
        
        # Get a few airports for demo
        test_airports = ['KBOS', 'KMHT']
        
        # Get weather data
        client = MetarApiClient()
        metar_data = client.get_metar_data(test_airports)
        taf_data = client.get_taf_data(test_airports)
        
        # Publish to Lattice
        airports_db = NewEnglandAirports.get_airports()
        
        for icao in test_airports:
            if icao in metar_data and 'error' not in metar_data[icao]:
                airport_info = airports_db[icao]
                metar_info = metar_data[icao]
                taf_info = taf_data.get(icao)
                
                print(f"Publishing weather entity for {icao}...")
                success = await integration.publish_weather_entity(
                    icao, airport_info, metar_info, taf_info
                )
                
                if success:
                    print(f"✓ Successfully published {icao}")
                else:
                    print(f"✗ Failed to publish {icao}")
        
    except Exception as e:
        print(f"Error in Lattice integration: {e}")

def sample_airport_database():
    """Example of using the airport database"""
    print("\\n=== Airport Database Example ===")
    
    airports = NewEnglandAirports.get_airports()
    
    print(f"Total airports in database: {len(airports)}")
    
    # Group by state
    by_state = {}
    for icao, info in airports.items():
        state = info['state']
        if state not in by_state:
            by_state[state] = []
        by_state[state].append((icao, info))
    
    for state in sorted(by_state.keys()):
        airports_in_state = by_state[state]
        print(f"\\n{state} ({len(airports_in_state)} airports):")
        for icao, info in airports_in_state:
            print(f"  {icao}: {info['name']} - {info['city']}")

async def main():
    """Run all sample examples"""
    print("METAR to Lattice Integration - Sample Usage")
    print("=" * 60)
    print(f"Run time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run examples
    sample_airport_database()
    sample_flight_conditions()
    
    try:
        await sample_basic_usage()
        await sample_multiple_airports()
        await sample_lattice_integration()
    except Exception as e:
        print(f"\\nNote: Some examples require internet connectivity: {e}")
    
    print("\\n" + "=" * 60)
    print("Sample usage completed!")
    print("\\nTo run the full integration:")
    print("  python metar_lattice_integration.py")

if __name__ == "__main__":
    asyncio.run(main())
'''

with open('sample_usage.py', 'w') as f:
    f.write(sample_usage)

print("Created sample_usage.py")

# Create a quick start guide
quick_start = '''# Quick Start Guide

## Prerequisites Check

1. **Python Version**: Ensure Python 3.9 or higher
   ```bash
   python3 --version
   ```

2. **Lattice Credentials**: Obtain from your Anduril representative
   - Lattice URL (e.g., `your-instance.lattice.com`)
   - Environment Bearer Token
   - Sandbox Token (if using Lattice Sandboxes)

## Installation (2 minutes)

```bash
# Clone/download the integration files
# Navigate to the integration directory

# Run setup
chmod +x setup.sh
./setup.sh

# Activate virtual environment
source .venv/bin/activate
```

## Configuration (1 minute)

```bash
# Set environment variables
export LATTICE_URL="your-lattice-instance.com"
export ENVIRONMENT_TOKEN="your-bearer-token"
export SANDBOXES_TOKEN="your-sandbox-token"  # Optional
```

## Test Installation (30 seconds)

```bash
# Test without Lattice connection
python test_integration.py

# Test with sample data
python sample_usage.py
```

## Run Integration (immediate)

```bash
# Start the integration
python metar_lattice_integration.py
```

Expected output:
```
METAR to Lattice Weather Integration
==================================================

2025-06-15 03:40:12 - INFO - Initialized Lattice integration for 19 airports
2025-06-15 03:40:12 - INFO - Starting METAR to Lattice integration with 30-minute updates
2025-06-15 03:40:14 - INFO - Successfully retrieved METAR data for 18 airports
2025-06-15 03:40:45 - INFO - Published 18/19 weather entities to Lattice
2025-06-15 03:40:45 - INFO - Waiting 30 minutes until next update...
```

## Verify in Lattice

1. Log into your Lattice environment
2. Look for weather entities with names like:
   - "General Edward Lawrence Logan International Airport (KBOS) - VFR"
   - "Manchester-Boston Regional Airport (KMHT) - MVFR"
3. Each entity will show:
   - Airport location on the map
   - Current flight conditions
   - Weather details in entity properties

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Environment variables not set" | Check `export` commands above |
| "Failed to retrieve METAR data" | Check internet connectivity |
| "Failed to publish entity" | Verify Lattice URL and tokens |
| Missing airports | Check FAA weather data availability |

## Next Steps

- Customize airport list in `metar_lattice_integration.py`
- Adjust update frequency (default: 30 minutes)
- Add monitoring and alerting
- Integrate with other weather sources

Total setup time: **< 5 minutes**
'''

with open('QUICKSTART.md', 'w') as f:
    f.write(quick_start)

print("Created QUICKSTART.md")

# Create a Dockerfile for containerized deployment
dockerfile_content = '''# Dockerfile for METAR to Lattice Integration
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Create non-root user
RUN useradd -m -u 1000 lattice && chown -R lattice:lattice /app
USER lattice

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD python -c "import requests; requests.get('https://aviationweather.gov', timeout=5)"

# Run the integration
CMD ["python", "metar_lattice_integration.py"]
'''

with open('Dockerfile', 'w') as f:
    f.write(dockerfile_content)

print("Created Dockerfile")

# Create docker-compose file for easier deployment
docker_compose = '''version: '3.8'

services:
  metar-lattice:
    build: .
    environment:
      - LATTICE_URL=${LATTICE_URL}
      - ENVIRONMENT_TOKEN=${ENVIRONMENT_TOKEN}
      - SANDBOXES_TOKEN=${SANDBOXES_TOKEN}
    restart: unless-stopped
    volumes:
      - ./logs:/app/logs
    networks:
      - lattice-network

networks:
  lattice-network:
    driver: bridge

# Usage:
# 1. Create .env file with your credentials:
#    echo "LATTICE_URL=your-instance.com" > .env
#    echo "ENVIRONMENT_TOKEN=your-token" >> .env
#    echo "SANDBOXES_TOKEN=your-sandbox-token" >> .env
# 
# 2. Run with docker-compose:
#    docker-compose up -d
'''

with open('docker-compose.yml', 'w') as f:
    f.write(docker_compose)

print("Created docker-compose.yml")

print("\nAll supporting files created!")
print("\nComplete file list:")
print("- metar_lattice_integration.py (main program)")
print("- requirements.txt")
print("- config_template.yml") 
print("- setup.sh")
print("- README.md")
print("- test_integration.py")
print("- sample_usage.py")
print("- QUICKSTART.md")
print("- Dockerfile")
print("- docker-compose.yml")
print("- metar_lattice_architecture.png (diagram)")
print("- new_england_airports.png (airport map)")