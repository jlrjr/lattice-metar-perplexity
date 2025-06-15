# Now add the main LatticeWeatherIntegration class with the new health components
code_part3 = """
class LatticeWeatherIntegration:
    \"\"\"Main class for integrating METAR weather data with Lattice\"\"\"
    
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
        \"\"\"Start the integration loop\"\"\"
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
        \"\"\"
        Publish weather entities to Lattice.
        
        Args:
            metar_data: Dictionary of METAR data by airport ICAO code
            
        Returns:
            Number of entities successfully published
        \"\"\"
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
        \"\"\"
        Create a Lattice entity for an airport with weather data.
        
        Args:
            icao: ICAO code of the airport
            airport: Airport information
            weather: Weather data for the airport
            
        Returns:
            Lattice entity representing the airport's weather
        \"\"\"
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
                    id=f"{icao}_temperature",
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
                    id=f"{icao}_wind_speed",
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
                    id=f"{icao}_visibility",
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
            entity_id=f"weather_{icao}_{int(time_now.timestamp())}",
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
        \"\"\"Map flight condition to health status\"\"\"
        if condition == "VFR":
            return HealthStatus.HEALTHY
        elif condition == "MVFR":
            return HealthStatus.WARN
        elif condition == "IFR":
            return HealthStatus.ERROR
        elif condition == "LIFR":
            return HealthStatus.ERROR
        else:
            return HealthStatus.UNKNOWN
    
    def _get_health_status_for_temperature(self, temp_c: float) -> HealthStatus:
        \"\"\"Map temperature to health status\"\"\"
        if temp_c < -20 or temp_c > 40:
            return HealthStatus.ERROR
        elif temp_c < -10 or temp_c > 35:
            return HealthStatus.WARN
        else:
            return HealthStatus.HEALTHY
    
    def _get_health_status_for_wind(self, wind_kt: float) -> HealthStatus:
        \"\"\"Map wind speed to health status\"\"\"
        if wind_kt > 30:
            return HealthStatus.ERROR
        elif wind_kt > 15:
            return HealthStatus.WARN
        else:
            return HealthStatus.HEALTHY
    
    def _get_health_status_for_visibility(self, visibility_miles: float) -> HealthStatus:
        \"\"\"Map visibility to health status\"\"\"
        if visibility_miles < 1:
            return HealthStatus.ERROR
        elif visibility_miles < 5:
            return HealthStatus.WARN
        else:
            return HealthStatus.HEALTHY
    
    async def publish_entity(self, entity: Entity) -> None:
        \"\"\"
        Publish an entity to Lattice.
        
        Args:
            entity: Entity to publish
        \"\"\"
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
    \"\"\"Main entry point\"\"\"
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
"""

# Append to the file
with open("metar_lattice_integration_modified.py", "a") as file:
    file.write(code_part3)

print("Added LatticeWeatherIntegration class with health components and disposition mapping")

# Verify the file is complete
import os
file_size = os.path.getsize("metar_lattice_integration_modified.py")
print(f"Complete file size: {file_size} bytes")

# Show a summary of the modifications made
print("\nSummary of modifications:")
print("1. Added FlightConditions.get_disposition_for_condition() to map flight conditions to Lattice dispositions")
print("2. Modified disposition setting in entity creation:")
print("   - VFR = DISPOSITION_ASSUMED_FRIENDLY")
print("   - MVFR = DISPOSITION_SUSPICIOUS")
print("   - IFR/LIFR = DISPOSITION_HOSTILE")
print("3. Added health components for:")
print("   - flight_condition")
print("   - temperature_c")
print("   - wind_speed_kt")
print("   - visibility_miles")
print("4. Added helper methods to determine health status for each component")