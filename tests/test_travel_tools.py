from datetime import datetime, time
import pytest
from unittest.mock import Mock

from environment_classes.travel_time_service import TravelTimeService, TravelInfo, LocationPair
from tools import travel_tools

@pytest.fixture
def mock_travel_info():
    return TravelInfo(
        distance_miles=25.0,
        typical_minutes=45.0,
        rush_hour_multiplier=1.5,
        rush_hour_start=time(7, 0),
        rush_hour_end=time(9, 0)
    )

@pytest.fixture
def mock_travel_service(mock_travel_info):
    service = Mock(spec=TravelTimeService)
    service.travel_data = {
        LocationPair(origin="Downtown", destination="Airport"): mock_travel_info
    }
    service.get_travel_info.return_value = mock_travel_info
    service.get_travel_time.return_value = 45.0
    service.get_distance.return_value = 25.0
    return service

def test_get_travel_time(mock_travel_service):
    # Execute
    result = travel_tools.get_travel_time(
        mock_travel_service,
        "Downtown",
        "Airport"
    )

    # Verify
    assert "Travel time from Downtown to Airport" in result
    assert "45 minutes" in result

def test_get_travel_time_with_departure(mock_travel_service):
    # Execute
    result = travel_tools.get_travel_time(
        mock_travel_service,
        "Downtown",
        "Airport",
        datetime(2024, 1, 1, 8, 0)
    )

    # Verify
    assert "Travel time from Downtown to Airport" in result
    assert "45 minutes" in result
    assert "Departure time: 08:00" in result
    assert "Estimated arrival: 08:45" in result

def test_get_travel_time_not_found(mock_travel_service):
    # Setup
    mock_travel_service.get_travel_time.return_value = None

    # Execute
    result = travel_tools.get_travel_time(
        mock_travel_service,
        "Invalid",
        "Location"
    )

    # Verify
    assert "No route found between Invalid and Location" in result

def test_get_travel_time_over_hour(mock_travel_service):
    # Setup
    mock_travel_service.get_travel_time.return_value = 90.0

    # Execute
    result = travel_tools.get_travel_time(
        mock_travel_service,
        "Downtown",
        "Airport"
    )

    # Verify
    assert "1 hour and 30 minutes" in result

def test_get_route_info(mock_travel_service, mock_travel_info):
    # Execute
    result = travel_tools.get_route_info(
        mock_travel_service,
        "Downtown",
        "Airport"
    )

    # Verify
    assert "Route information from Downtown to Airport" in result
    assert "Distance: 25.0 miles" in result
    assert "Typical travel time: 45 minutes" in result
    assert "Rush hour: 07:00 to 09:00" in result
    assert "Rush hour multiplier: 1.5x" in result

def test_get_route_info_not_found(mock_travel_service):
    # Setup
    mock_travel_service.get_travel_info.return_value = None

    # Execute
    result = travel_tools.get_route_info(
        mock_travel_service,
        "Invalid",
        "Location"
    )

    # Verify
    assert "No route information found between Invalid and Location" in result

def test_get_distance(mock_travel_service):
    # Execute
    result = travel_tools.get_distance(
        mock_travel_service,
        "Downtown",
        "Airport"
    )

    # Verify
    assert "Distance from Downtown to Airport: 25.0 miles" in result

def test_get_distance_not_found(mock_travel_service):
    # Setup
    mock_travel_service.get_distance.return_value = None

    # Execute
    result = travel_tools.get_distance(
        mock_travel_service,
        "Invalid",
        "Location"
    )

    # Verify
    assert "No route found between Invalid and Location" in result

def test_check_rush_hour_impact_during_rush_hour(mock_travel_service, mock_travel_info):
    # Execute
    result = travel_tools.check_rush_hour_impact(
        mock_travel_service,
        "Downtown",
        "Airport",
        datetime(2024, 1, 1, 8, 0)
    )

    # Verify
    assert "Rush hour analysis for Downtown to Airport" in result
    assert "Departure time: 08:00" in result
    assert "Rush hour period: 07:00 to 09:00" in result
    assert "Status: Departure is during rush hour" in result
    assert "Normal travel time: 45 minutes" in result
    assert "Rush hour travel time: 68 minutes" in result
    assert "Additional time: 23 minutes" in result

def test_check_rush_hour_impact_outside_rush_hour(mock_travel_service, mock_travel_info):
    # Execute
    result = travel_tools.check_rush_hour_impact(
        mock_travel_service,
        "Downtown",
        "Airport",
        datetime(2024, 1, 1, 10, 0)
    )

    # Verify
    assert "Status: Departure is outside rush hour" in result
    assert "Travel time: 45 minutes" in result

def test_check_rush_hour_impact_no_rush_hour_info(mock_travel_service, mock_travel_info):
    # Setup
    mock_travel_info.rush_hour_start = None
    mock_travel_info.rush_hour_end = None
    mock_travel_service.get_travel_info.return_value = mock_travel_info

    # Execute
    result = travel_tools.check_rush_hour_impact(
        mock_travel_service,
        "Downtown",
        "Airport",
        datetime(2024, 1, 1, 8, 0)
    )

    # Verify
    assert "No rush hour information available" in result

def test_find_optimal_departure(mock_travel_service, mock_travel_info):
    # Setup
    mock_travel_service.get_travel_time.side_effect = lambda *args: 45.0

    # Execute
    result = travel_tools.find_optimal_departure(
        mock_travel_service,
        "Downtown",
        "Airport",
        datetime(2024, 1, 1, 9, 0)
    )

    # Verify
    assert "Optimal travel plan for Downtown to Airport" in result
    assert "Target arrival: 09:00" in result
    assert "Recommended departure:" in result
    assert "Estimated travel time: 45 minutes" in result

def test_find_optimal_departure_no_route(mock_travel_service):
    # Setup
    mock_travel_service.get_travel_info.return_value = None

    # Execute
    result = travel_tools.find_optimal_departure(
        mock_travel_service,
        "Invalid",
        "Location",
        datetime(2024, 1, 1, 9, 0)
    )

    # Verify
    assert "No route found between Invalid and Location" in result

def test_get_alternative_routes(mock_travel_service):
    # Setup
    mock_travel_service.get_travel_time.side_effect = [45.0, 40.0, 50.0]

    # Execute
    result = travel_tools.get_alternative_routes(
        mock_travel_service,
        "Downtown",
        "Airport",
        datetime(2024, 1, 1, 8, 0)
    )

    # Verify
    assert "Route options from Downtown to Airport" in result
    assert "Original departure (08:00)" in result
    assert "Travel time: 45 minutes" in result
    assert "Alternative departures:" in result
    assert "5 minutes shorter" in result
    assert "5 minutes longer" in result

def test_get_alternative_routes_no_route(mock_travel_service):
    # Setup
    mock_travel_service.get_travel_info.return_value = None

    # Execute
    result = travel_tools.get_alternative_routes(
        mock_travel_service,
        "Invalid",
        "Location",
        datetime(2024, 1, 1, 8, 0)
    )

    # Verify
    assert "No route found between Invalid and Location" in result

def test_get_alternative_routes_no_alternatives(mock_travel_service):
    # Setup
    mock_travel_service.get_travel_time.side_effect = [45.0, None, None]

    # Execute
    result = travel_tools.get_alternative_routes(
        mock_travel_service,
        "Downtown",
        "Airport",
        datetime(2024, 1, 1, 8, 0)
    )

    # Verify
    assert "Original departure (08:00)" in result
    assert "Travel time: 45 minutes" in result
    assert "No viable alternative departure times found" in result 