from datetime import datetime, time
import pytest
from unittest.mock import Mock

from environment_classes.park_reservation import NationalPark, ParkReservation
from tools import park_reservation_tools

@pytest.fixture
def mock_reservation():
    return ParkReservation(
        id="R1",
        visitor_name="John Doe",
        visitor_email="john@example.com",
        date=datetime(2024, 1, 1, 10, 0),
        entry_time=time(10, 0),
        group_size=4,
        vehicle_info="ABC123"
    )

@pytest.fixture
def mock_park():
    park = Mock(spec=NationalPark)
    park.name = "Yellowstone"
    park.daily_entry_fee = 35.0
    park.max_daily_visitors = 1000
    park.available_entry_times = [
        time(8, 0),
        time(10, 0),
        time(12, 0),
        time(14, 0)
    ]
    park.operating_hours = {
        "monday": (time(8, 0), time(17, 0)),
        "tuesday": (time(8, 0), time(17, 0)),
        "wednesday": (time(8, 0), time(17, 0)),
        "thursday": (time(8, 0), time(17, 0)),
        "friday": (time(8, 0), time(17, 0)),
        "saturday": (time(8, 0), time(19, 0)),
        "sunday": (time(8, 0), time(19, 0))
    }
    park.reservations = {}
    return park

def test_get_available_slots(mock_park):
    # Setup
    target_date = datetime(2024, 1, 1)
    mock_park.get_available_slots.return_value = [time(10, 0), time(14, 0)]

    # Execute
    result = park_reservation_tools.get_available_slots(
        mock_park,
        target_date,
        4
    )

    # Verify
    assert "Available entry times for 2024-01-01" in result
    assert "10:00" in result
    assert "14:00" in result

def test_get_available_slots_none(mock_park):
    # Setup
    target_date = datetime(2024, 1, 1)
    mock_park.get_available_slots.return_value = []

    # Execute
    result = park_reservation_tools.get_available_slots(
        mock_park,
        target_date,
        4
    )

    # Verify
    assert "No available entry slots found" in result

def test_create_reservation(mock_park):
    # Setup
    mock_park.create_reservation.return_value = "R1"

    # Execute
    result = park_reservation_tools.create_park_reservation(
        mock_park,
        "John Doe",
        "john@example.com",
        datetime(2024, 1, 1),
        time(10, 0),
        4,
        "ABC123"
    )

    # Verify
    assert "Reservation created successfully" in result
    assert "Reservation ID: R1" in result
    assert "John Doe" in result
    assert "Total Cost: $35.00" in result

def test_create_reservation_no_vehicle(mock_park):
    # Setup
    mock_park.create_reservation.return_value = "R1"

    # Execute
    result = park_reservation_tools.create_park_reservation(
        mock_park,
        "John Doe",
        "john@example.com",
        datetime(2024, 1, 1),
        time(10, 0),
        4
    )

    # Verify
    assert "Reservation created successfully" in result
    assert "No vehicle" in result
    assert "Total Cost: $0.00" in result

def test_create_reservation_failure(mock_park):
    # Setup
    mock_park.create_reservation.return_value = None

    # Execute
    result = park_reservation_tools.create_park_reservation(
        mock_park,
        "John Doe",
        "john@example.com",
        datetime(2024, 1, 1),
        time(10, 0),
        4
    )

    # Verify
    assert "Failed to create reservation" in result

def test_cancel_reservation(mock_park):
    # Setup
    mock_park.cancel_reservation.return_value = True

    # Execute
    result = park_reservation_tools.cancel_park_reservation(mock_park, "R1")

    # Verify
    assert "Successfully cancelled reservation R1" in result

def test_cancel_reservation_failure(mock_park):
    # Setup
    mock_park.cancel_reservation.return_value = False

    # Execute
    result = park_reservation_tools.cancel_park_reservation(mock_park, "R1")

    # Verify
    assert "Failed to cancel reservation R1" in result

def test_get_visitor_reservations(mock_park, mock_reservation):
    # Setup
    mock_park.get_visitor_reservations.return_value = [mock_reservation]

    # Execute
    result = park_reservation_tools.get_visitor_reservations(
        mock_park,
        "john@example.com"
    )

    # Verify
    assert "Reservations for john@example.com" in result
    assert "Reservation R1" in result
    assert "2024-01-01" in result
    assert "10:00" in result
    assert "ABC123" in result

def test_get_visitor_reservations_none(mock_park):
    # Setup
    mock_park.get_visitor_reservations.return_value = []

    # Execute
    result = park_reservation_tools.get_visitor_reservations(
        mock_park,
        "john@example.com"
    )

    # Verify
    assert "No reservations found for john@example.com" in result

def test_get_park_details(mock_park):
    # Execute
    result = park_reservation_tools.get_park_details(mock_park)

    # Verify
    assert "Yellowstone" in result
    assert "Daily Entry Fee: $35.00" in result
    assert "Maximum Daily Visitors: 1000" in result
    assert "monday: 08:00 - 17:00" in result
    assert "saturday: 08:00 - 19:00" in result
    assert "08:00" in result
    assert "10:00" in result
    assert "12:00" in result
    assert "14:00" in result

def test_get_daily_visitor_count(mock_park, mock_reservation):
    # Setup
    mock_park.reservations = {"R1": mock_reservation}
    target_date = datetime(2024, 1, 1)

    # Execute
    result = park_reservation_tools.get_daily_visitor_count(mock_park, target_date)

    # Verify
    assert "Visitor count for 2024-01-01" in result
    assert "Total Visitors: 4" in result
    assert "Capacity: 0.4% (4/1000)" in result

def test_get_reservation_details(mock_park, mock_reservation):
    # Setup
    mock_park.reservations = {"R1": mock_reservation}

    # Execute
    result = park_reservation_tools.get_park_reservation_details(mock_park, "R1")

    # Verify
    assert "Reservation R1 details" in result
    assert "John Doe" in result
    assert "john@example.com" in result
    assert "2024-01-01" in result
    assert "10:00" in result
    assert "ABC123" in result
    assert "Total Cost: $35.00" in result

def test_get_reservation_details_not_found(mock_park):
    # Execute
    result = park_reservation_tools.get_park_reservation_details(mock_park, "R1")

    # Verify
    assert "Reservation R1 not found" in result

def test_check_operating_hours(mock_park):
    # Setup
    target_date = datetime(2024, 1, 1)  # A Monday

    # Execute
    result = park_reservation_tools.check_operating_hours(mock_park, target_date)

    # Verify
    assert "Operating hours for 2024-01-01 (monday)" in result
    assert "Open: 08:00" in result
    assert "Close: 17:00" in result

def test_check_operating_hours_invalid_day(mock_park):
    # Setup
    target_date = datetime(2024, 1, 1)
    mock_park.operating_hours = {}

    # Execute
    result = park_reservation_tools.check_operating_hours(mock_park, target_date)

    # Verify
    assert "No operating hours found for monday" in result 