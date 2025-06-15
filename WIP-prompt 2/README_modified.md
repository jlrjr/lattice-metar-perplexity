# METAR to Lattice Weather Integration (Modified)

A Python application that integrates METAR (Meteorological Aerodrome Reports) airport weather conditions with the Anduril Lattice SDK. This modified version includes enhanced entity health components and color-coded entity dispositions based on flight conditions.

## New Features in This Version

### Entity Health Components
The integration now creates detailed health components for each weather station entity, monitoring:

- **Flight Condition**: Overall flight safety status (VFR, MVFR, IFR, LIFR)
- **Temperature**: Current temperature readings with extreme temperature alerts
- **Wind Speed**: Wind conditions with high wind warnings
- **Visibility**: Current visibility with low visibility alerts

### Color-Coded Entity Dispositions
Entities are now assigned dispositions based on flight conditions to provide visual indicators in the Lattice interface:

- **VFR (Visual Flight Rules)**: `DISPOSITION_ASSUMED_FRIENDLY` (Green) - Safe flying conditions
- **MVFR (Marginal VFR)**: `DISPOSITION_SUSPICIOUS` (Yellow) - Marginal conditions requiring caution  
- **IFR (Instrument Flight Rules)**: `DISPOSITION_HOSTILE` (Red) - Poor conditions requiring instruments
- **LIFR (Low IFR)**: `DISPOSITION_HOSTILE` (Red) - Dangerous conditions with severe restrictions

## Health Status Mapping

### Flight Condition Health
- `HEALTHY`: VFR conditions - safe for visual flight
- `WARN`: MVFR conditions - marginal conditions, caution advised
- `ERROR`: IFR/LIFR conditions - poor/dangerous conditions

### Temperature Health
- `HEALTHY`: -10°C to 35°C (14°F to 95°F)
- `WARN`: -20°C to -10°C or 35°C to 40°C (-4°F to 14°F or 95°F to 104°F)
- `ERROR`: Below -20°C or above 40°C (below -4°F or above 104°F)

### Wind Speed Health
- `HEALTHY`: 0-15 knots - calm to moderate winds
- `WARN`: 16-30 knots - strong winds, caution for small aircraft
- `ERROR`: Over 30 knots - high winds, dangerous for most aircraft

### Visibility Health
- `HEALTHY`: Over 5 miles - excellent visibility
- `WARN`: 1-5 miles - reduced visibility
- `ERROR`: Under 1 mile - severely limited visibility

## Features

- **Real-time Weather Data**: Retrieves current METAR and TAF reports from the FAA Aviation Weather Center
- **Flight Condition Classification**: Automatically determines VFR, MVFR, IFR, or LIFR conditions based on visibility and ceiling
- **Comprehensive Airport Coverage**: Includes 19+ major New England airports across all 6 states
- **Enhanced Lattice Integration**: Publishes weather data as Lattice entities with health components and color-coded dispositions
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

## Installation

```bash
# Install requirements
pip install -r requirements_modified.txt

# Set environment variables
export LATTICE_URL="your-lattice-instance.com"
export ENVIRONMENT_TOKEN="your-bearer-token"
export SANDBOXES_TOKEN="your-sandbox-token"  # Optional
```

## Usage

```bash
# Run the modified integration
python metar_lattice_integration_modified.py
```

## Viewing Results in Lattice

In the Lattice interface, you'll now see:

1. **Weather Station Entities**: Each airport appears as a sensor point of interest
2. **Color-Coded Icons**: Entity colors reflect flight conditions
   - Green for VFR (safe conditions)
   - Yellow for MVFR (marginal conditions)
   - Red for IFR/LIFR (poor/dangerous conditions)
3. **Health Components**: Detailed health status for each weather parameter
4. **Entity Details**: Complete weather information in entity properties

## Key Modifications from Original

1. **Enhanced Disposition Setting**: Entities now use appropriate disposition values based on flight conditions
2. **Health Component Integration**: Four new health components monitor critical weather parameters
3. **Visual Indicators**: Color-coding provides immediate assessment of conditions
4. **Improved User Experience**: Health status messages provide detailed explanations
5. **Better Operational Awareness**: Multiple health dimensions provide comprehensive weather assessment

## Example Entity Structure

Each weather entity now includes:

```python
entity = Entity(
    # Basic entity information
    entity_id="weather_KBOS_1234567890",
    description="General Edward Lawrence Logan International Airport (KBOS) - MVFR",

    # Location and classification  
    location=Location(...),
    mil_view=MilView(
        disposition=Disposition.SUSPICIOUS,  # Yellow for MVFR
        environment=Environment.AIR
    ),

    # Health components
    health=Health(
        health_status=HealthStatus.WARN,
        components=[
            ComponentHealth(id="KBOS_flight_condition", ...),
            ComponentHealth(id="KBOS_temperature", ...),
            ComponentHealth(id="KBOS_wind_speed", ...),
            ComponentHealth(id="KBOS_visibility", ...)
        ]
    ),

    # Metadata
    provenance=Provenance(...)
)
```

## Configuration

The integration is configured through environment variables:

- `LATTICE_URL`: Your Lattice environment URL
- `ENVIRONMENT_TOKEN`: Bearer token for authentication
- `SANDBOXES_TOKEN`: Optional sandbox token for development

## Logging

The application provides detailed logging for:
- Weather data retrieval
- Entity creation and publishing
- Health component status changes
- Error conditions and recovery

## Troubleshooting

### Common Issues

1. **Authentication Errors**: Verify `LATTICE_URL` and `ENVIRONMENT_TOKEN` are set correctly
2. **Weather Data Issues**: Check internet connectivity and FAA API availability
3. **Entity Publishing Failures**: Verify Lattice connectivity and credentials

### Health Component Debugging

Each health component includes detailed messages explaining current status and thresholds.

## Support

For questions about this integration, contact Anduril Developer Relations.
