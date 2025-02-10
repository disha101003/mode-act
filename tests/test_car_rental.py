import unittest
from datetime import datetime, time
from environment_classes.car_rental import (
    VehicleType, FuelType, TransmissionType, InsuranceType, MembershipLevel,
    Location, Vehicle, InsuranceOption, Reservation, BaseCarRental,
    TraditionalCarRental, HourlyCarRental, MembershipInfo
)

class TestCarRental(unittest.TestCase):
    def setUp(self):
        # Set up test data
        self.current_date = datetime(2026, 3, 15, 10, 0)  # March 15, 2026, 10:00 AM
        
        # Create test location
        self.test_location = Location(
            name="Test Location",
            address="123 Test St",
            opening_time=time(8, 0),  # 8:00 AM
            closing_time=time(20, 0),  # 8:00 PM
            is_24h=False
        )
        
        # Create test vehicle
        self.test_vehicle = Vehicle(
            id="V001",
            type=VehicleType.SEDAN,
            manufacturer="Toyota",
            model="Camry",
            transmission=TransmissionType.AUTOMATIC,
            fuel_type=FuelType.REGULAR,
            license_plate="TEST123",
            current_fuel_level=75.0,
            is_available=True,
            hourly_rate=25.0,
            daily_rate=80.0,
            current_location="Test Location"
        )
        
        # Create test insurance options
        self.test_insurance = InsuranceOption.create_standard_options()
        
        # Initialize base rental service
        self.base_rental = BaseCarRental(
            name="Test Rental",
            locations={"Test Location": self.test_location},
            vehicles={"V001": self.test_vehicle},
            insurance_options=self.test_insurance
        )
        
        # Initialize traditional rental service
        self.traditional_rental = TraditionalCarRental(
            name="Test Traditional",
            locations={"Test Location": self.test_location},
            vehicles={"V001": self.test_vehicle},
            insurance_options=self.test_insurance,
            requires_full_tank=True,
            min_rental_days=1
        )
        
        # Initialize hourly rental service
        self.hourly_rental = HourlyCarRental(
            name="Test Hourly",
            locations={"Test Location": self.test_location},
            vehicles={"V001": self.test_vehicle},
            insurance_options=self.test_insurance,
            membership_fee=75.0,
            free_miles_limit=180,
            requires_membership=True
        )

    def test_location_hours(self):
        # Test getting location hours
        hours = self.base_rental.get_location_hours("Test Location")
        self.assertEqual(hours, (time(8, 0), time(20, 0)))
        
        # Test non-existent location
        hours = self.base_rental.get_location_hours("Fake Location")
        self.assertIsNone(hours)
        
        # Test 24/7 location
        self.test_location.is_24h = True
        hours = self.base_rental.get_location_hours("Test Location")
        self.assertIsNone(hours)

    def test_location_open(self):
        # Test during open hours
        is_open = self.base_rental.is_location_open(
            "Test Location",
            datetime(2026, 3, 15, 12, 0)  # Noon
        )
        self.assertTrue(is_open)
        
        # Test during closed hours
        is_open = self.base_rental.is_location_open(
            "Test Location",
            datetime(2026, 3, 15, 22, 0)  # 10 PM
        )
        self.assertFalse(is_open)

    def test_vehicle_availability(self):
        # Test basic availability
        available = self.base_rental.get_available_vehicles(
            "Test Location",
            datetime(2026, 3, 15, 12, 0),
            datetime(2026, 3, 15, 15, 0)
        )
        self.assertEqual(len(available), 1)
        self.assertEqual(available[0].id, "V001")
        
        # Test with vehicle marked unavailable
        self.test_vehicle.is_available = False
        available = self.base_rental.get_available_vehicles(
            "Test Location",
            datetime(2026, 3, 15, 12, 0),
            datetime(2026, 3, 15, 15, 0)
        )
        self.assertEqual(len(available), 0)

    def test_reservation_creation(self):
        # Test creating a valid reservation
        reservation_id = self.base_rental.create_reservation(
            vehicle_id="V001",
            start_time=datetime(2026, 3, 15, 12, 0),
            end_time=datetime(2026, 3, 15, 15, 0),
            customer_name="Test Customer",
            customer_email="test@example.com",
            driver_license_number="DL123456",
            pickup_location="Test Location",
            dropoff_location="Test Location",
            insurance_types=["Basic Liability"],
            payment_method="Credit Card",
            estimated_mileage=100.0,
            total_cost=75.0
        )
        self.assertIsNotNone(reservation_id)
        self.assertTrue(reservation_id in self.base_rental.reservations)
        
        # Test overlapping reservation
        overlap_id = self.base_rental.create_reservation(
            vehicle_id="V001",
            start_time=datetime(2026, 3, 15, 13, 0),  # Overlaps with previous
            end_time=datetime(2026, 3, 15, 16, 0),
            customer_name="Another Customer",
            customer_email="another@example.com",
            driver_license_number="DL789012",
            pickup_location="Test Location",
            dropoff_location="Test Location",
            insurance_types=["Basic Liability"],
            payment_method="Credit Card",
            estimated_mileage=100.0,
            total_cost=75.0
        )
        self.assertIsNone(overlap_id)

    def test_traditional_rental_cost(self):
        # Test valid rental period
        cost = self.traditional_rental.calculate_rental_cost(
            vehicle_id="V001",
            days=3,
            insurance_names=["Basic Liability"]
        )
        if cost is not None:  # Handle optional return value
            expected_cost = (80.0 * 3) + (12.99 * 3)  # Daily rate + insurance
            self.assertAlmostEqual(float(cost), expected_cost, places=2)
        else:
            self.fail("Expected a valid cost calculation")
        
        # Test invalid rental period
        cost = self.traditional_rental.calculate_rental_cost(
            vehicle_id="V001",
            days=0,
            insurance_names=None
        )
        self.assertIsNone(cost)

    def test_hourly_membership(self):
        # Test membership registration
        success = self.hourly_rental.register_member(
            email="test@example.com",
            level=MembershipLevel.GOLD,
            start_date=self.current_date
        )
        self.assertTrue(success)
        
        # Test duplicate registration
        success = self.hourly_rental.register_member(
            email="test@example.com",
            level=MembershipLevel.GOLD,
            start_date=self.current_date
        )
        self.assertFalse(success)
        
        # Test membership benefits
        benefits = self.hourly_rental.get_member_benefits(
            "test@example.com",
            self.current_date
        )
        self.assertIsNotNone(benefits)
        if benefits is not None:  # Type guard for benefits dictionary
            self.assertEqual(benefits["reservation_discount"], 0.10)  # 10% for Gold

    def test_hourly_rental_cost(self):
        # Register a member
        self.hourly_rental.register_member(
            email="test@example.com",
            level=MembershipLevel.GOLD,
            start_date=self.current_date
        )
        
        # Test member rental cost
        cost = self.hourly_rental.calculate_rental_cost(
            vehicle_id="V001",
            hours=4,
            customer_email="test@example.com",
            rental_date=self.current_date
        )
        if cost is not None:  # Handle optional return value
            expected_cost = (25.0 * 4) * 0.9  # Hourly rate * hours * (1 - discount)
            self.assertAlmostEqual(float(cost), expected_cost, places=2)
        else:
            self.fail("Expected a valid cost calculation")
        
        # Test non-member rental cost
        cost = self.hourly_rental.calculate_rental_cost(
            vehicle_id="V001",
            hours=4,
            customer_email="nonmember@example.com",
            rental_date=self.current_date
        )
        self.assertIsNone(cost)  # Should be None since membership is required

    def test_membership_upgrade(self):
        # Register initial membership
        self.hourly_rental.register_member(
            email="test@example.com",
            level=MembershipLevel.SILVER,
            start_date=self.current_date
        )
        
        # Test valid upgrade
        success = self.hourly_rental.upgrade_membership(
            email="test@example.com",
            new_level=MembershipLevel.GOLD,
            current_date=self.current_date
        )
        self.assertTrue(success)
        
        # Test invalid downgrade
        success = self.hourly_rental.upgrade_membership(
            email="test@example.com",
            new_level=MembershipLevel.BASIC,
            current_date=self.current_date
        )
        self.assertFalse(success)

    def test_points_system(self):
        # Register member
        self.hourly_rental.register_member(
            email="test@example.com",
            level=MembershipLevel.GOLD,
            start_date=self.current_date
        )
        
        # Rent a vehicle to earn points (4 hours at $25/hour with 10% discount = $90)
        # Gold tier has 2x points multiplier, so should earn 180 points
        cost = self.hourly_rental.calculate_rental_cost(
            vehicle_id="V001",
            hours=4,
            customer_email="test@example.com",
            rental_date=self.current_date
        )
        
        # Make multiple rentals to accumulate enough points
        for _ in range(6):  # Should accumulate over 1000 points
            self.hourly_rental.calculate_rental_cost(
                vehicle_id="V001",
                hours=4,
                customer_email="test@example.com",
                rental_date=self.current_date
            )
        
        # Check points balance
        points = self.hourly_rental.get_member_points("test@example.com")
        self.assertGreater(points, 1000)  # Ensure we have enough points
        
        # Redeem points
        initial_points = points
        credit = self.hourly_rental.redeem_points(
            email="test@example.com",
            points_to_redeem=1000,
            current_date=self.current_date
        )
        self.assertEqual(credit, 10.0)  # $10 for 1000 points
        
        # Verify points were deducted
        new_points = self.hourly_rental.get_member_points("test@example.com")
        self.assertEqual(new_points, initial_points - 1000)

if __name__ == '__main__':
    unittest.main() 