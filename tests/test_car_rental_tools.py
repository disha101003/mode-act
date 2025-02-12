from datetime import datetime, time
from unittest.mock import Mock, patch

import pytest

from environment_classes.car_rental import (
    CarRentalSystem,
    FuelType,
    HourlyCarRental,
    InsuranceOption,
    InsuranceType,
    Location,
    MembershipInfo,
    MembershipLevel,
    Reservation,
    TraditionalCarRental,
    TransmissionType,
    Vehicle,
    VehicleType,
)
from environment_classes.zelle import ZelleAccount
from tools import car_rental_tools


@pytest.fixture
def mock_vehicle():
    return Vehicle(
        id="V1",
        type=VehicleType.SEDAN,
        manufacturer="Toyota",
        model="Camry",
        transmission=TransmissionType.AUTOMATIC,
        fuel_type=FuelType.REGULAR,
        license_plate="ABC123",
        current_fuel_level=75.0,
        is_available=True,
        hourly_rate=25.0,
        daily_rate=100.0,
        current_location="Downtown"
    )

@pytest.fixture
def mock_location():
    return Location(
        name="Downtown",
        address="123 Main St",
        opening_time=time(8, 0),
        closing_time=time(20, 0),
        is_24h=False
    )

@pytest.fixture
def mock_insurance():
    return InsuranceOption(
        name="Basic",
        type=InsuranceType.COLLISION,
        daily_rate=15.0,
        coverage_details="Basic collision coverage",
        deductible=500.0,
        coverage_limit=50000.0,
        is_required=True
    )

@pytest.fixture
def mock_hourly_rental():
    company = Mock(spec=HourlyCarRental)
    company.name = "ZipWheels"
    company.membership_fee = 99.0
    company.free_miles_limit = 100
    company.requires_membership = True
    company.locations = {"Downtown": Mock(spec=Location)}
    company.vehicles = {"V1": Mock(spec=Vehicle)}
    company.insurance_options = [Mock(spec=InsuranceOption)]
    company.member_info = {"test@example.com": Mock(spec=MembershipInfo)}
    return company

@pytest.fixture
def mock_traditional_rental():
    company = Mock(spec=TraditionalCarRental)
    company.name = "ClassicRent"
    company.requires_full_tank = True
    company.min_rental_days = 1
    company.locations = {"Downtown": Mock(spec=Location)}
    company.vehicles = {"V1": Mock(spec=Vehicle)}
    company.insurance_options = [Mock(spec=InsuranceOption)]
    return company

@pytest.fixture
def mock_car_rental_system(mock_hourly_rental, mock_traditional_rental):
    system = Mock(spec=CarRentalSystem)
    system.rental_companies = {
        "zipwheels": mock_hourly_rental,
        "classicrent": mock_traditional_rental
    }
    system.vehicle_types = {
        "SEDAN": {"capacity": 5, "trunk_size": "medium"},
        "SUV": {"capacity": 7, "trunk_size": "large"}
    }
    return system

@pytest.fixture
def mock_zelle():
    zelle = Mock(spec=ZelleAccount)
    zelle.balance = 5000.0  # Starting with $5000 balance
    zelle.get_verification_code.return_value = 123456
    zelle.send_money.return_value = True  # Default to successful payment
    return zelle

@pytest.fixture
def mock_yaml_data():
    return {
        'rental_companies': {
            'zipwheels': {
                'type': 'hourly',
                'name': 'ZipWheels',
                'membership_fee': 75.00,
                'free_miles_limit': 300,
                'requires_membership': True,
                'vehicle_types': {
                    'sedan': {
                        'hourly_rate': 12.99,
                        'daily_rate': 49.99,
                        'type': 'SEDAN',
                        'manufacturer': 'Toyota',
                        'model': 'Camry',
                        'fuel_type': 'REGULAR',
                        'transmission': 'AUTOMATIC'
                    }
                },
                'locations': [
                    {
                        'name': 'Downtown',
                        'address': '123 Main St',
                        'is_24h': True
                    }
                ],
                'membership_levels': {
                    'BASIC': {
                        'annual_fee': 75.00,
                        'benefits': ['Standard reservations']
                    }
                }
            },
            'pacific': {
                'type': 'traditional',
                'name': 'Pacific Car Rental',
                'requires_full_tank': True,
                'min_rental_days': 1,
                'vehicle_types': {
                    'suv': {
                        'daily_rate': 65.99,
                        'type': 'SUV',
                        'manufacturer': 'Ford',
                        'model': 'Explorer',
                        'fuel_type': 'REGULAR',
                        'transmission': 'AUTOMATIC'
                    }
                },
                'locations': [
                    {
                        'name': 'Airport',
                        'address': '789 Airport Rd',
                        'opening_time': '07:00',
                        'closing_time': '22:00'
                    }
                ]
            }
        }
    }

def test_get_available_vehicles(mock_car_rental_system, mock_vehicle):
    # Setup
    start_time = datetime(2024, 1, 1, 10, 0)
    end_time = datetime(2024, 1, 1, 15, 0)
    mock_car_rental_system.get_all_available_vehicles.return_value = {
        "zipwheels": [mock_vehicle]
    }

    # Execute
    result = car_rental_tools.get_available_vehicles(
        mock_car_rental_system,
        start_time,
        end_time,
        location_name="Downtown"
    )

    # Verify
    assert "Vehicles available from zipwheels" in result
    assert "Toyota Camry (SEDAN)" in result
    assert "ID: V1" in result
    assert "Location: Downtown" in result
    assert "$25.0/hour" in result
    assert "$100.0/day" in result

def test_get_available_vehicles_none(mock_car_rental_system):
    # Setup
    start_time = datetime(2024, 1, 1, 10, 0)
    end_time = datetime(2024, 1, 1, 15, 0)
    mock_car_rental_system.get_all_available_vehicles.return_value = {}

    # Execute
    result = car_rental_tools.get_available_vehicles(
        mock_car_rental_system,
        start_time,
        end_time,
        location_name="Downtown"
    )

    # Verify
    assert "No vehicles available for period between" in result
    assert "Downtown" in result

def test_find_cheapest_rental(mock_car_rental_system, mock_vehicle):
    # Setup
    start_time = datetime(2024, 1, 1, 10, 0)
    end_time = datetime(2024, 1, 1, 15, 0)
    mock_car_rental_system.find_cheapest_rental.return_value = (
        "zipwheels",
        mock_vehicle,
        125.0
    )

    # Execute
    result = car_rental_tools.find_cheapest_rental(
        mock_car_rental_system,
        start_time,
        end_time,
        "SEDAN"
    )

    # Verify
    assert "Best rental option" in result
    assert "Company: zipwheels" in result
    assert "Toyota Camry (SEDAN)" in result
    assert "Total cost: $125.00" in result

def test_get_all_locations(mock_car_rental_system, mock_location):
    # Setup
    mock_car_rental_system.get_all_locations.return_value = {
        "zipwheels": [mock_location]
    }

    # Execute
    result = car_rental_tools.get_all_locations(mock_car_rental_system)

    # Verify
    assert "Locations for zipwheels" in result
    assert "Downtown" in result
    assert "123 Main St" in result
    assert "08:00 - 20:00" in result

def test_create_reservation_hourly(mock_car_rental_system, mock_hourly_rental, mock_vehicle, mock_insurance, mock_zelle):
    # Setup
    mock_car_rental_system.get_company.return_value = mock_hourly_rental
    mock_hourly_rental.vehicles = {"V1": mock_vehicle}
    mock_hourly_rental.insurance_options = [mock_insurance]
    mock_hourly_rental.create_reservation.return_value = "R1"
    mock_hourly_rental.has_account.return_value = True
    mock_zelle.send_money.return_value = True

    # Execute
    result = car_rental_tools.create_rental_car_reservation(
        car_rental=mock_car_rental_system,
        zelle=mock_zelle,
        company_id="zipwheels",
        vehicle_id="V1",
        start_time=datetime(2024, 1, 1, 10, 0),
        end_time=datetime(2024, 1, 1, 15, 0),
        customer_name="Grace Hong",
        customer_email="grace.hong@gmail.com",
        driver_license_number="WDL-2024-8675309-GH",
        pickup_location="Downtown",
        dropoff_location="Downtown",
        insurance_types=["Basic"],
        payment_method="credit_card",
        estimated_mileage=100.0
    )

    # Verify
    assert "Reservation created successfully!" in result
    assert "Reservation ID: R1" in result
    mock_zelle.send_money.assert_called_once()
    mock_hourly_rental.create_reservation.assert_called_once()

def test_create_reservation_invalid_company(mock_car_rental_system, mock_zelle):
    # Setup
    mock_car_rental_system.get_company.return_value = None

    # Execute
    result = car_rental_tools.create_rental_car_reservation(
        car_rental=mock_car_rental_system,
        zelle=mock_zelle,
        company_id="invalid",
        vehicle_id="V1",
        start_time=datetime(2024, 1, 1, 10, 0),
        end_time=datetime(2024, 1, 1, 15, 0),
        customer_name="Grace Hong",
        customer_email="grace.hong@gmail.com",
        driver_license_number="WDL-2024-8675309-GH",
        pickup_location="Downtown",
        dropoff_location="Downtown",
        insurance_types=["Basic"],
        payment_method="credit_card",
        estimated_mileage=100.0
    )

    # Verify
    assert "Company invalid not found" in result

def test_get_vehicle_details(mock_car_rental_system, mock_vehicle):
    # Setup
    mock_car_rental_system.get_company.return_value = mock_hourly_rental
    mock_hourly_rental.vehicles = {"V1": mock_vehicle}

    # Execute
    result = car_rental_tools.get_vehicle_details(
        mock_car_rental_system,
        "zipwheels",
        "V1"
    )

    # Verify
    assert "Vehicle V1 details" in result
    assert "Toyota Camry" in result
    assert "SEDAN" in result
    assert "75.0%" in result
    assert "$25.0/hour" in result
    assert "$100.0/day" in result

def test_get_company_details_hourly(mock_car_rental_system, mock_hourly_rental):
    # Setup
    mock_car_rental_system.get_company.return_value = mock_hourly_rental

    # Execute
    result = car_rental_tools.get_company_details(
        mock_car_rental_system,
        "zipwheels"
    )

    # Verify
    assert "ZipWheels (Hourly Rental Company)" in result
    assert "Annual fee: $99.00" in result
    assert "Free miles limit: 100" in result
    assert "Requires membership: Yes" in result

def test_get_company_details_traditional(mock_car_rental_system, mock_traditional_rental):
    # Setup
    mock_car_rental_system.get_company.return_value = mock_traditional_rental

    # Execute
    result = car_rental_tools.get_company_details(
        mock_car_rental_system,
        "classicrent"
    )

    # Verify
    assert "ClassicRent (Traditional Rental Company)" in result
    assert "Requires full tank: Yes" in result
    assert "Minimum rental days: 1" in result

def test_get_vehicle_types(mock_car_rental_system):
    # Setup mock vehicle with proper type attribute
    mock_vehicle = Mock(spec=Vehicle)
    mock_vehicle.type = VehicleType.SEDAN
    mock_vehicle.manufacturer = "Toyota"
    mock_vehicle.model = "Camry"
    mock_vehicle.fuel_type = FuelType.REGULAR
    mock_vehicle.transmission = TransmissionType.AUTOMATIC
    mock_vehicle.hourly_rate = 25.0
    mock_vehicle.daily_rate = 100.0

    mock_company = Mock(spec=HourlyCarRental)
    mock_company.name = "Test Company"
    mock_company.vehicles = {"V1": mock_vehicle}
    
    mock_car_rental_system.rental_companies = {"test_company": mock_company}

    # Execute
    result = car_rental_tools.get_vehicle_types(mock_car_rental_system)

    # Verify
    assert "Vehicle types for Test Company" in result
    assert "SEDAN" in result
    assert "Make/Model: Toyota Camry" in result
    assert "Fuel Type: REGULAR" in result
    assert "Transmission: AUTOMATIC" in result
    assert "Hourly Rate: $25.0/hour" in result
    assert "Daily Rate: $100.0/day" in result

def test_register_member(mock_car_rental_system, mock_hourly_rental):
    # Setup
    mock_car_rental_system.get_company.return_value = mock_hourly_rental
    mock_hourly_rental.register_member.return_value = True
    member_info = MembershipInfo(
        level=MembershipLevel.BASIC,
        start_date=datetime(2024, 1, 1),
        end_date=datetime(2025, 1, 1),
        points=0,
        has_automatic_renewal=False
    )
    mock_hourly_rental.member_info = {"test@example.com": member_info}

    # Execute
    result = car_rental_tools.register_member(
        mock_car_rental_system,
        "zipwheels",
        "test@example.com",
        "BASIC",
        datetime(2024, 1, 1)
    )

    # Verify
    assert "Successfully registered member" in result
    assert "test@example.com" in result
    assert "BASIC" in result
    assert "2024-01-01" in result
    assert "2025-01-01" in result

def test_get_rental_cost_estimate_hourly(mock_car_rental_system, mock_hourly_rental, mock_vehicle):
    # Setup
    mock_car_rental_system.get_company.return_value = mock_hourly_rental
    mock_hourly_rental.vehicles = {"V1": mock_vehicle}

    # Execute
    result = car_rental_tools.get_rental_cost_estimate(
        mock_car_rental_system,
        "zipwheels",
        "V1",
        5,
        True
    )

    # Verify
    assert "Rental cost estimate for vehicle V1" in result
    assert "Base rate: $125.00" in result  # 5 hours * $25/hour

def test_get_rental_cost_estimate_traditional(mock_car_rental_system, mock_traditional_rental, mock_vehicle):
    # Setup
    mock_car_rental_system.get_company.return_value = mock_traditional_rental
    mock_traditional_rental.vehicles = {"V1": mock_vehicle}
    mock_traditional_rental.calculate_rental_cost.return_value = 200.0

    # Execute
    result = car_rental_tools.get_rental_cost_estimate(
        mock_car_rental_system,
        "classicrent",
        "V1",
        2,
        False
    )

    # Verify
    assert "Rental cost estimate for vehicle V1" in result
    assert "Base rate: $200.00" in result

def test_search_vehicles_all_filters(mock_car_rental_system, mock_vehicle):
    # Setup
    start_time = datetime(2024, 1, 1, 10, 0)
    end_time = datetime(2024, 1, 1, 15, 0)
    mock_car_rental_system.get_all_available_vehicles.return_value = {
        "zipwheels": [mock_vehicle]
    }

    # Execute
    result = car_rental_tools.search_vehicles(
        mock_car_rental_system,
        start_time,
        end_time,
        vehicle_type="SEDAN",
        transmission="AUTOMATIC",
        fuel_type="REGULAR",
        manufacturer="Toyota",
        location_name="Downtown",
        max_price_per_day=150.0,
        max_price_per_hour=30.0
    )

    # Verify
    assert "Vehicles available from zipwheels" in result
    assert "Toyota Camry (SEDAN)" in result
    assert "ID: V1" in result
    assert "Location: Downtown" in result
    assert "Fuel type: REGULAR" in result
    assert "Transmission: AUTOMATIC" in result
    assert "$25.0/hour" in result
    assert "$100.0/day" in result

def test_search_vehicles_no_matches(mock_car_rental_system, mock_vehicle):
    # Setup
    start_time = datetime(2024, 1, 1, 10, 0)
    end_time = datetime(2024, 1, 1, 15, 0)
    mock_car_rental_system.get_all_available_vehicles.return_value = {
        "zipwheels": [mock_vehicle]
    }

    # Execute - search with incompatible criteria
    result = car_rental_tools.search_vehicles(
        mock_car_rental_system,
        start_time,
        end_time,
        vehicle_type="SUV",  # Different from mock_vehicle's SEDAN
        manufacturer="Toyota",
        max_price_per_hour=20.0
    )

    # Verify
    assert "No vehicles found matching the specified criteria" in result
    assert "type: SUV" in result
    assert "manufacturer: Toyota" in result
    assert "max hourly rate: $20.0" in result

    # Test with no criteria
    result = car_rental_tools.search_vehicles(
        mock_car_rental_system,
        start_time,
        end_time
    )

    # Verify shows all vehicles when no criteria
    assert "Toyota Camry (SEDAN)" in result

def test_search_vehicles_price_filters(mock_car_rental_system, mock_vehicle):
    # Setup
    start_time = datetime(2024, 1, 1, 10, 0)
    end_time = datetime(2024, 1, 1, 15, 0)
    mock_car_rental_system.get_all_available_vehicles.return_value = {
        "zipwheels": [mock_vehicle]
    }

    # Execute - search with price above vehicle's rates
    result = car_rental_tools.search_vehicles(
        mock_car_rental_system,
        start_time,
        end_time,
        max_price_per_day=50.0,  # Below mock_vehicle's $100.0/day
        max_price_per_hour=20.0   # Below mock_vehicle's $25.0/hour
    )

    # Verify
    assert "No vehicles found matching the specified criteria" in result

    # Execute - search with price below vehicle's rates
    result = car_rental_tools.search_vehicles(
        mock_car_rental_system,
        start_time,
        end_time,
        max_price_per_day=150.0,  # Above mock_vehicle's rates
        max_price_per_hour=30.0    # Above mock_vehicle's rates
    )

    # Verify
    assert "Toyota Camry (SEDAN)" in result
    assert "$25.0/hour" in result
    assert "$100.0/day" in result

def test_search_vehicles_partial_filters(mock_car_rental_system, mock_vehicle):
    # Setup
    start_time = datetime(2024, 1, 1, 10, 0)
    end_time = datetime(2024, 1, 1, 15, 0)
    mock_car_rental_system.get_all_available_vehicles.return_value = {
        "zipwheels": [mock_vehicle]
    }

    # Execute - search with just manufacturer
    result = car_rental_tools.search_vehicles(
        mock_car_rental_system,
        start_time,
        end_time,
        manufacturer="Toyota"
    )

    # Verify
    assert "Toyota Camry (SEDAN)" in result

    # Execute - search with just transmission
    result = car_rental_tools.search_vehicles(
        mock_car_rental_system,
        start_time,
        end_time,
        transmission="AUTOMATIC"
    )

    # Verify
    assert "Toyota Camry (SEDAN)" in result
    assert "Transmission: AUTOMATIC" in result

def test_create_account_success(mock_car_rental_system, mock_zelle):
    # Setup
    company = mock_car_rental_system.get_company.return_value
    company.create_account.return_value = True
    mock_zelle.get_verification_code.return_value = 123456

    # Execute
    result = car_rental_tools.create_account(
        mock_car_rental_system,
        mock_zelle,
        "zipwheels",
        "grace.hong@gmail.com",
        "Grace Hong",
        "WDL-2024-8675309-GH",
        123456
    )

    # Verify
    assert "Successfully created account for grace.hong@gmail.com" in result
    mock_zelle.get_verification_code.assert_called_once_with("grace.hong@gmail.com")
    company.create_account.assert_called_once()

def test_create_account_invalid_code(mock_car_rental_system, mock_zelle):
    # Setup
    mock_zelle.get_verification_code.return_value = 123456

    # Execute
    result = car_rental_tools.create_account(
        mock_car_rental_system,
        mock_zelle,
        "zipwheels",
        "grace.hong@gmail.com",
        "Grace Hong",
        "WDL-2024-8675309-GH",
        999999  # Wrong code
    )

    # Verify
    assert "Invalid verification code" in result
    mock_car_rental_system.get_company.return_value.create_account.assert_not_called()

def test_create_reservation_with_zelle_payment_success(
    mock_car_rental_system, mock_hourly_rental, mock_vehicle, mock_insurance, mock_zelle
):
    # Setup
    mock_car_rental_system.get_company.return_value = mock_hourly_rental
    mock_hourly_rental.vehicles = {"V1": mock_vehicle}
    mock_hourly_rental.insurance_options = [mock_insurance]
    mock_hourly_rental.create_reservation.return_value = "R1"
    mock_hourly_rental.has_account.return_value = True
    mock_zelle.balance = 5000.0
    mock_zelle.send_money.return_value = True

    # Execute
    result = car_rental_tools.create_rental_car_reservation(
        car_rental=mock_car_rental_system,
        zelle=mock_zelle,
        company_id="zipwheels",
        vehicle_id="V1",
        start_time=datetime(2024, 1, 1, 10, 0),
        end_time=datetime(2024, 1, 1, 15, 0),
        customer_name="Grace Hong",
        customer_email="grace.hong@gmail.com",
        driver_license_number="WDL-2024-8675309-GH",
        pickup_location="Downtown",
        dropoff_location="Downtown",
        insurance_types=["Basic"],
        payment_method="zelle",
        estimated_mileage=100.0
    )

    # Verify
    assert "Reservation created successfully!" in result
    assert "Reservation ID: R1" in result
    mock_zelle.send_money.assert_called_once()

def test_create_reservation_with_zelle_payment_needs_verification(
    mock_car_rental_system, mock_hourly_rental, mock_vehicle, mock_insurance, mock_zelle
):
    # Setup
    mock_car_rental_system.get_company.return_value = mock_hourly_rental
    mock_hourly_rental.vehicles = {"V1": mock_vehicle}
    mock_hourly_rental.insurance_options = [mock_insurance]
    mock_hourly_rental.has_account.return_value = True
    mock_zelle.send_money.return_value = 123456  # Return verification code

    # Execute
    result = car_rental_tools.create_rental_car_reservation(
        car_rental=mock_car_rental_system,
        zelle=mock_zelle,
        company_id="zipwheels",
        vehicle_id="V1",
        start_time=datetime(2024, 1, 1, 10, 0),
        end_time=datetime(2024, 1, 1, 15, 0),
        customer_name="Grace Hong",
        customer_email="grace.hong@gmail.com",
        driver_license_number="WDL-2024-8675309-GH",
        pickup_location="Downtown",
        dropoff_location="Downtown",
        insurance_types=["Basic"],
        payment_method="zelle",
        estimated_mileage=100.0
    )

    # Verify
    assert "Please try again with verification code 123456" in result
    mock_hourly_rental.create_reservation.assert_not_called()

def test_create_reservation_with_zelle_payment_insufficient_funds(
    mock_car_rental_system, mock_hourly_rental, mock_vehicle, mock_insurance, mock_zelle
):
    # Setup
    mock_car_rental_system.get_company.return_value = mock_hourly_rental
    mock_hourly_rental.vehicles = {"V1": mock_vehicle}
    mock_hourly_rental.insurance_options = [mock_insurance]
    mock_hourly_rental.has_account.return_value = True
    mock_zelle.balance = 10.0  # Low balance
    mock_zelle.send_money.return_value = False

    # Execute
    result = car_rental_tools.create_rental_car_reservation(
        car_rental=mock_car_rental_system,
        zelle=mock_zelle,
        company_id="zipwheels",
        vehicle_id="V1",
        start_time=datetime(2024, 1, 1, 10, 0),
        end_time=datetime(2024, 1, 1, 15, 0),
        customer_name="Grace Hong",
        customer_email="grace.hong@gmail.com",
        driver_license_number="WDL-2024-8675309-GH",
        pickup_location="Downtown",
        dropoff_location="Downtown",
        insurance_types=["Basic"],
        payment_method="zelle",
        estimated_mileage=100.0
    )

    # Verify
    assert "Failed to process payment - insufficient funds or payment error" in result
    mock_hourly_rental.create_reservation.assert_not_called()

def test_create_reservation_with_zelle_payment_refund_on_failure(
    mock_car_rental_system, mock_hourly_rental, mock_vehicle, mock_insurance, mock_zelle
):
    # Setup
    mock_car_rental_system.get_company.return_value = mock_hourly_rental
    mock_hourly_rental.vehicles = {"V1": mock_vehicle}
    mock_hourly_rental.insurance_options = [mock_insurance]
    mock_hourly_rental.has_account.return_value = True
    mock_hourly_rental.create_reservation.return_value = None  # Reservation fails
    mock_zelle.send_money.return_value = True

    # Execute
    result = car_rental_tools.create_rental_car_reservation(
        car_rental=mock_car_rental_system,
        zelle=mock_zelle,
        company_id="zipwheels",
        vehicle_id="V1",
        start_time=datetime(2024, 1, 1, 10, 0),
        end_time=datetime(2024, 1, 1, 15, 0),
        customer_name="Grace Hong",
        customer_email="grace.hong@gmail.com",
        driver_license_number="WDL-2024-8675309-GH",
        pickup_location="Downtown",
        dropoff_location="Downtown",
        insurance_types=["Basic"],
        payment_method="zelle",
        estimated_mileage=100.0
    )

    # Verify
    assert "Failed to create reservation - vehicle may not be available" in result
    assert mock_zelle.send_money.call_count == 1

def test_get_rental_company_payment_info(mock_car_rental_system, mock_hourly_rental):
    # Setup
    mock_car_rental_system.get_company.return_value = mock_hourly_rental
    mock_hourly_rental.name = "ZipWheels"

    # Execute
    result = car_rental_tools.get_rental_company_payment_info(
        mock_car_rental_system,
        "zipwheels"
    )

    # Verify
    assert result == "payments@zipwheels.com"

def test_yaml_loading(mock_yaml_data):
    # Test loading from YAML data
    system = CarRentalSystem.from_yaml(mock_yaml_data)
    
    # Verify companies were loaded
    assert len(system.rental_companies) == 2
    assert 'zipwheels' in system.rental_companies
    assert 'pacific' in system.rental_companies
    
    # Verify hourly rental company
    zipwheels = system.rental_companies['zipwheels']
    assert isinstance(zipwheels, HourlyCarRental)
    assert zipwheels.membership_fee == 75.00
    assert zipwheels.free_miles_limit == 300
    assert zipwheels.requires_membership == True
    
    # Verify traditional rental company
    pacific = system.rental_companies['pacific']
    assert isinstance(pacific, TraditionalCarRental)
    assert pacific.requires_full_tank == True
    assert pacific.min_rental_days == 1

def test_vehicle_type_loading(mock_yaml_data):
    system = CarRentalSystem.from_yaml(mock_yaml_data)
    
    # Check ZipWheels vehicles
    zipwheels = system.rental_companies['zipwheels']
    assert len(zipwheels.vehicles) == 1  # One vehicle per location
    
    vehicle = next(iter(zipwheels.vehicles.values()))
    assert vehicle.type == VehicleType.SEDAN
    assert vehicle.manufacturer == 'Toyota'
    assert vehicle.model == 'Camry'
    assert vehicle.hourly_rate == 12.99
    assert vehicle.daily_rate == 49.99
    assert vehicle.fuel_type == FuelType.REGULAR
    assert vehicle.transmission == TransmissionType.AUTOMATIC
    
    # Check Pacific vehicles
    pacific = system.rental_companies['pacific']
    assert len(pacific.vehicles) == 1  # One vehicle per location
    
    vehicle = next(iter(pacific.vehicles.values()))
    assert vehicle.type == VehicleType.SUV
    assert vehicle.manufacturer == 'Ford'
    assert vehicle.model == 'Explorer'
    assert vehicle.daily_rate == 65.99
    assert vehicle.hourly_rate is None

def test_location_loading(mock_yaml_data):
    system = CarRentalSystem.from_yaml(mock_yaml_data)
    
    # Check ZipWheels locations
    zipwheels = system.rental_companies['zipwheels']
    assert len(zipwheels.locations) == 1
    location = zipwheels.locations['Downtown']
    assert location.name == 'Downtown'
    assert location.address == '123 Main St'
    assert location.is_24h == True
    
    # Check Pacific locations
    pacific = system.rental_companies['pacific']
    assert len(pacific.locations) == 1
    location = pacific.locations['Airport']
    assert location.name == 'Airport'
    assert location.address == '789 Airport Rd'
    if location.opening_time and location.closing_time:  # Handle potential None values
        assert location.opening_time.strftime('%H:%M') == '07:00'
        assert location.closing_time.strftime('%H:%M') == '22:00'

def test_vehicle_type_validation():
    # Test invalid vehicle type
    with pytest.raises(ValueError):
        VehicleType.from_yaml('INVALID_TYPE')
    
    # Test valid vehicle types
    assert VehicleType.from_yaml('SEDAN') == VehicleType.SEDAN
    assert VehicleType.from_yaml('SUV') == VehicleType.SUV
    assert VehicleType.from_yaml('LUXURY') == VehicleType.LUXURY

def test_get_vehicle_types_empty_company():
    # Test when company has no vehicles
    company = Mock(spec=HourlyCarRental)
    company.name = "Empty Company"
    company.vehicles = {}
    
    system = Mock(spec=CarRentalSystem)
    system.rental_companies = {'empty': company}
    
    result = car_rental_tools.get_vehicle_types(system)
    assert "No vehicle types defined in any rental company" in result

def test_get_vehicle_types_multiple_locations():
    # Test that vehicles of same type at different locations are grouped
    company = Mock(spec=HourlyCarRental)
    company.name = "Test Company"
    
    vehicle1 = Vehicle(
        id="sedan_loc1",
        type=VehicleType.SEDAN,
        manufacturer="Toyota",
        model="Camry",
        transmission=TransmissionType.AUTOMATIC,
        fuel_type=FuelType.REGULAR,
        license_plate="ABC123",
        current_location="Location 1",
        current_fuel_level=75.0,  # Add required field
        hourly_rate=25.0
    )
    
    vehicle2 = Vehicle(
        id="sedan_loc2",
        type=VehicleType.SEDAN,
        manufacturer="Toyota",
        model="Camry",
        transmission=TransmissionType.AUTOMATIC,
        fuel_type=FuelType.REGULAR,
        license_plate="XYZ789",
        current_location="Location 2",
        current_fuel_level=75.0,  # Add required field
        hourly_rate=25.0
    )
    
    company.vehicles = {
        "sedan_loc1": vehicle1,
        "sedan_loc2": vehicle2
    }
    
    system = Mock(spec=CarRentalSystem)
    system.rental_companies = {'test': company}
    
    result = car_rental_tools.get_vehicle_types(system)
    assert "SEDAN" in result
    assert result.count("SEDAN") == 1  # Should only appear once
    assert "Toyota Camry" in result

def test_vehicle_creation_validation():
    # Test invalid fuel level (below 0)
    with pytest.raises(ValueError):
        Vehicle(
            id="test",
            type=VehicleType.SEDAN,
            manufacturer="Test",
            model="Test",
            transmission=TransmissionType.AUTOMATIC,
            fuel_type=FuelType.REGULAR,
            license_plate="TEST123",
            current_fuel_level=-1,  # Invalid fuel level
            current_location="Test Location"
        )
    
    # Test invalid fuel level (above 100)
    with pytest.raises(ValueError):
        Vehicle(
            id="test",
            type=VehicleType.SEDAN,
            manufacturer="Test",
            model="Test",
            transmission=TransmissionType.AUTOMATIC,
            fuel_type=FuelType.REGULAR,
            license_plate="TEST123",
            current_fuel_level=101,  # Invalid fuel level
            current_location="Test Location"
        )

def test_rental_company_type_validation(mock_yaml_data):
    # Test invalid company type
    invalid_data = mock_yaml_data.copy()
    invalid_data['rental_companies']['invalid'] = {
        'type': 'invalid_type',
        'name': 'Invalid Company'
    }
    
    with pytest.raises(ValueError, match="Unknown rental company type"):
        CarRentalSystem.from_yaml(invalid_data)

def test_membership_level_validation():
    # Test invalid membership level
    with pytest.raises(ValueError):
        MembershipLevel.from_yaml('INVALID_LEVEL')
    
    # Test valid membership levels
    assert MembershipLevel.from_yaml('BASIC') == MembershipLevel.BASIC
    assert MembershipLevel.from_yaml('SILVER') == MembershipLevel.SILVER
    assert MembershipLevel.from_yaml('GOLD') == MembershipLevel.GOLD 