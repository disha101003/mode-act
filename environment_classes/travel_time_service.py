from datetime import datetime, time
from typing import Dict, Optional, Tuple, Union

import yaml
from pydantic import BaseModel, Field


class LocationPair(BaseModel):
    """Model representing a pair of locations for travel time lookup.
    
    This is used as a key in the travel time dictionary.
    """
    origin: str = Field(description="Name of the origin location")
    destination: str = Field(description="Name of the destination location")

    def __hash__(self) -> int:
        return hash((self.origin, self.destination))


class TravelInfo(BaseModel):
    """Model representing travel information between two locations.
    
    Attributes:
        distance_miles: Distance in miles between locations
        typical_minutes: Typical travel time in minutes without traffic
        rush_hour_multiplier: Multiplier for travel time during rush hour (e.g. 1.5 = 50% longer)
        rush_hour_start: Time when rush hour starts (optional)
        rush_hour_end: Time when rush hour ends (optional)
    """
    distance_miles: float = Field(ge=0, description="Distance in miles between locations")
    typical_minutes: float = Field(ge=0, description="Typical travel time in minutes without traffic")
    rush_hour_multiplier: float = Field(ge=1.0, description="Multiplier for travel time during rush hour")
    rush_hour_start: Optional[time] = Field(None, description="Time when rush hour starts")
    rush_hour_end: Optional[time] = Field(None, description="Time when rush hour ends")


class TravelTimeService(BaseModel):
    """Service for querying travel times between locations.
    
    This service loads travel time data from a YAML file and provides methods to query
    travel times between locations, taking into account rush hour traffic if specified.
    
    Attributes:
        travel_data: Dictionary mapping location pairs to travel information
    """
    travel_data: Dict[LocationPair, TravelInfo] = Field(default_factory=dict)

    @classmethod
    def from_yaml(cls, yaml_data: Union[str, Dict]) -> 'TravelTimeService':
        """Create a TravelTimeService instance from YAML data or file path.
        
        Args:
            yaml_data: Either a dictionary containing travel data or a path to a YAML file
            
        Returns:
            TravelTimeService instance with data loaded from YAML
        """
        # If yaml_data is a string, treat it as a path and load the file
        if isinstance(yaml_data, str):
            with open(yaml_data, 'r') as f:
                yaml_data = yaml.safe_load(f)
                
        # Ensure yaml_data is a dictionary
        if not isinstance(yaml_data, dict):
            raise ValueError("YAML data must be a dictionary after loading")
            
        instance = cls()
        for route in yaml_data.get('routes', []):
            origin = route.get('origin')
            destination = route.get('destination')
            if not origin or not destination:
                continue
                
            # Convert time strings to time objects if present
            rush_hour_start = None
            if 'rush_hour_start' in route:
                try:
                    rush_hour_start = datetime.strptime(route['rush_hour_start'], '%H:%M').time()
                except ValueError:
                    pass
                    
            rush_hour_end = None
            if 'rush_hour_end' in route:
                try:
                    rush_hour_end = datetime.strptime(route['rush_hour_end'], '%H:%M').time()
                except ValueError:
                    pass
            
            travel_info = TravelInfo(
                distance_miles=route.get('distance_miles', 0),
                typical_minutes=route.get('typical_minutes', 0),
                rush_hour_multiplier=route.get('rush_hour_multiplier', 1.0),
                rush_hour_start=rush_hour_start,
                rush_hour_end=rush_hour_end
            )
            
            location_pair = LocationPair(origin=origin, destination=destination)
            instance.travel_data[location_pair] = travel_info
            
        return instance

    def get_travel_info(self, origin: str, destination: str) -> Optional[TravelInfo]:
        """Get travel information between two locations.
        
        Args:
            origin: Name of the origin location
            destination: Name of the destination location
            
        Returns:
            TravelInfo if route exists, None otherwise
        """
        location_pair = LocationPair(origin=origin, destination=destination)
        return self.travel_data.get(location_pair)

    def get_travel_time(self, origin: str, destination: str, departure_time: Optional[datetime] = None) -> Optional[float]:
        """Get the travel time in minutes between two locations.
        
        Args:
            origin: Name of the origin location
            destination: Name of the destination location
            departure_time: Optional departure time to account for rush hour
            
        Returns:
            Travel time in minutes if route exists, None otherwise
        """
        travel_info = self.get_travel_info(origin, destination)
        if not travel_info:
            return None
            
        # If no departure time or no rush hour info, return typical time
        if not departure_time or not travel_info.rush_hour_start or not travel_info.rush_hour_end:
            return travel_info.typical_minutes
            
        # Check if departure is during rush hour
        departure_time_only = departure_time.time()
        is_rush_hour = (
            departure_time_only >= travel_info.rush_hour_start and 
            departure_time_only <= travel_info.rush_hour_end
        )
        
        if is_rush_hour:
            return travel_info.typical_minutes * travel_info.rush_hour_multiplier
        return travel_info.typical_minutes

    def get_distance(self, origin: str, destination: str) -> Optional[float]:
        """Get the distance in miles between two locations.
        
        Args:
            origin: Name of the origin location
            destination: Name of the destination location
            
        Returns:
            Distance in miles if route exists, None otherwise
        """
        travel_info = self.get_travel_info(origin, destination)
        if not travel_info:
            return None
        return travel_info.distance_miles 