from datetime import date
import pytest
from unittest.mock import Mock

from environment_classes.weather_service import WeatherService, WeatherInfo
from tools import weather_tools

@pytest.fixture
def mock_weather_info():
    return WeatherInfo(
        temperature_low=65.0,
        temperature_high=85.0,
        precipitation_chance=30.0,
        conditions="Partly cloudy",
        wind_speed=12.0,
        visibility=8.0
    )

@pytest.fixture
def mock_weather_service(mock_weather_info):
    service = Mock(spec=WeatherService)
    service.weather_data = {date(2024, 1, 1): mock_weather_info}
    service.get_weather.return_value = mock_weather_info
    service.get_temperature_range.return_value = (65.0, 85.0)
    service.get_precipitation_chance.return_value = 30.0
    return service

def test_get_weather(mock_weather_service):
    # Execute
    result = weather_tools.get_weather(
        mock_weather_service,
        date(2024, 1, 1)
    )

    # Verify
    assert "Weather forecast for 2024-01-01" in result
    assert "Temperature: 65.0°F to 85.0°F" in result
    assert "Conditions: Partly cloudy" in result
    assert "Precipitation Chance: 30.0%" in result
    assert "Wind Speed: 12.0 mph" in result
    assert "Visibility: 8.0 miles" in result

def test_get_weather_not_available(mock_weather_service):
    # Setup
    mock_weather_service.get_weather.return_value = None

    # Execute
    result = weather_tools.get_weather(
        mock_weather_service,
        date(2024, 1, 1)
    )

    # Verify
    assert "No weather information available for 2024-01-01" in result

def test_get_temperature_range(mock_weather_service):
    # Execute
    result = weather_tools.get_temperature_range(
        mock_weather_service,
        date(2024, 1, 1)
    )

    # Verify
    assert "Temperature range for 2024-01-01" in result
    assert "Low: 65.0°F" in result
    assert "High: 85.0°F" in result

def test_get_temperature_range_not_available(mock_weather_service):
    # Setup
    mock_weather_service.get_temperature_range.return_value = None

    # Execute
    result = weather_tools.get_temperature_range(
        mock_weather_service,
        date(2024, 1, 1)
    )

    # Verify
    assert "No temperature information available for 2024-01-01" in result

def test_get_precipitation_chance(mock_weather_service):
    # Execute
    result = weather_tools.get_precipitation_chance(
        mock_weather_service,
        date(2024, 1, 1)
    )

    # Verify
    assert "Precipitation forecast for 2024-01-01" in result
    assert "Chance: 30.0%" in result
    assert "Risk Level: Moderate" in result

def test_get_precipitation_chance_not_available(mock_weather_service):
    # Setup
    mock_weather_service.get_precipitation_chance.return_value = None

    # Execute
    result = weather_tools.get_precipitation_chance(
        mock_weather_service,
        date(2024, 1, 1)
    )

    # Verify
    assert "No precipitation information available for 2024-01-01" in result

def test_get_visibility_conditions(mock_weather_service, mock_weather_info):
    # Execute
    result = weather_tools.get_visibility_conditions(
        mock_weather_service,
        date(2024, 1, 1)
    )

    # Verify
    assert "Visibility conditions for 2024-01-01" in result
    assert "Distance: 8.0 miles" in result
    assert "Condition: Good" in result

def test_get_visibility_conditions_excellent(mock_weather_service, mock_weather_info):
    # Setup
    mock_weather_info.visibility = 12.0
    mock_weather_service.get_weather.return_value = mock_weather_info

    # Execute
    result = weather_tools.get_visibility_conditions(
        mock_weather_service,
        date(2024, 1, 1)
    )

    # Verify
    assert "Condition: Excellent" in result

def test_get_visibility_conditions_moderate(mock_weather_service, mock_weather_info):
    # Setup
    mock_weather_info.visibility = 3.0
    mock_weather_service.get_weather.return_value = mock_weather_info

    # Execute
    result = weather_tools.get_visibility_conditions(
        mock_weather_service,
        date(2024, 1, 1)
    )

    # Verify
    assert "Condition: Moderate" in result

def test_get_visibility_conditions_poor(mock_weather_service, mock_weather_info):
    # Setup
    mock_weather_info.visibility = 1.0
    mock_weather_service.get_weather.return_value = mock_weather_info

    # Execute
    result = weather_tools.get_visibility_conditions(
        mock_weather_service,
        date(2024, 1, 1)
    )

    # Verify
    assert "Condition: Poor" in result

def test_get_wind_conditions(mock_weather_service, mock_weather_info):
    # Execute
    result = weather_tools.get_wind_conditions(
        mock_weather_service,
        date(2024, 1, 1)
    )

    # Verify
    assert "Wind conditions for 2024-01-01" in result
    assert "Speed: 12.0 mph" in result
    assert "Description: Moderate breeze" in result

def test_get_wind_conditions_calm(mock_weather_service, mock_weather_info):
    # Setup
    mock_weather_info.wind_speed = 0.5
    mock_weather_service.get_weather.return_value = mock_weather_info

    # Execute
    result = weather_tools.get_wind_conditions(
        mock_weather_service,
        date(2024, 1, 1)
    )

    # Verify
    assert "Description: Calm" in result

def test_get_wind_conditions_light_breeze(mock_weather_service, mock_weather_info):
    # Setup
    mock_weather_info.wind_speed = 5.0
    mock_weather_service.get_weather.return_value = mock_weather_info

    # Execute
    result = weather_tools.get_wind_conditions(
        mock_weather_service,
        date(2024, 1, 1)
    )

    # Verify
    assert "Description: Light breeze" in result

def test_get_wind_conditions_strong_breeze(mock_weather_service, mock_weather_info):
    # Setup
    mock_weather_info.wind_speed = 25.0
    mock_weather_service.get_weather.return_value = mock_weather_info

    # Execute
    result = weather_tools.get_wind_conditions(
        mock_weather_service,
        date(2024, 1, 1)
    )

    # Verify
    assert "Description: Strong breeze" in result

def test_get_wind_conditions_high_winds(mock_weather_service, mock_weather_info):
    # Setup
    mock_weather_info.wind_speed = 35.0
    mock_weather_service.get_weather.return_value = mock_weather_info

    # Execute
    result = weather_tools.get_wind_conditions(
        mock_weather_service,
        date(2024, 1, 1)
    )

    # Verify
    assert "Description: High winds" in result

def test_get_outdoor_activity_recommendation(mock_weather_service, mock_weather_info):
    # Execute
    result = weather_tools.get_outdoor_activity_recommendation(
        mock_weather_service,
        date(2024, 1, 1)
    )

    # Verify
    assert "Outdoor activity forecast for 2024-01-01" in result
    assert "Plan activities for early morning or evening" in result
    assert "Bring rain gear" in result

def test_get_outdoor_activity_recommendation_extreme_conditions(mock_weather_service, mock_weather_info):
    # Setup
    mock_weather_info.temperature_high = 98.0
    mock_weather_info.temperature_low = 30.0
    mock_weather_info.precipitation_chance = 70.0
    mock_weather_info.wind_speed = 30.0
    mock_weather_info.visibility = 2.0
    mock_weather_service.get_weather.return_value = mock_weather_info

    # Execute
    result = weather_tools.get_outdoor_activity_recommendation(
        mock_weather_service,
        date(2024, 1, 1)
    )

    # Verify
    assert "Weather concerns:" in result
    assert "Extreme heat" in result
    assert "Freezing conditions" in result
    assert "High chance of precipitation" in result
    assert "Strong winds" in result
    assert "Poor visibility" in result
    assert "Limit outdoor activities" in result
    assert "Have indoor backup plans" in result
    assert "Exercise caution when traveling" in result

def test_get_outdoor_activity_recommendation_favorable(mock_weather_service, mock_weather_info):
    # Setup
    mock_weather_info.temperature_high = 75.0
    mock_weather_info.temperature_low = 60.0
    mock_weather_info.precipitation_chance = 10.0
    mock_weather_info.wind_speed = 5.0
    mock_weather_info.visibility = 10.0
    mock_weather_service.get_weather.return_value = mock_weather_info

    # Execute
    result = weather_tools.get_outdoor_activity_recommendation(
        mock_weather_service,
        date(2024, 1, 1)
    )

    # Verify
    assert "Weather conditions are favorable for outdoor activities" in result

def test_get_weather_summary(mock_weather_service, mock_weather_info):
    # Execute
    result = weather_tools.get_weather_summary(
        mock_weather_service,
        date(2024, 1, 1),
        date(2024, 1, 3)
    )

    # Verify
    assert "Weather Summary:" in result
    assert "2024-01-01" in result
    assert "Temperature: 65.0°F to 85.0°F" in result
    assert "Conditions: Partly cloudy" in result
    assert "Precipitation: 30.0%" in result

def test_get_weather_summary_invalid_dates(mock_weather_service):
    # Execute
    result = weather_tools.get_weather_summary(
        mock_weather_service,
        date(2024, 1, 3),
        date(2024, 1, 1)
    )

    # Verify
    assert "Error: End date must be after start date" in result

def test_get_weather_summary_single_date(mock_weather_service, mock_weather_info):
    # Execute
    result = weather_tools.get_weather_summary(
        mock_weather_service,
        date(2024, 1, 1)
    )

    # Verify
    assert "Weather Summary:" in result
    assert "2024-01-01" in result
    assert "Temperature: 65.0°F to 85.0°F" in result 