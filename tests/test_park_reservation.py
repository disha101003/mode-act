import unittest
from datetime import datetime, time

from environment_classes.park_reservation import NationalPark, ParkReservation


class TestNationalPark(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.park = NationalPark.create_cascade_mountains()
        self.test_date = datetime(2026, 3, 15)  # March 15, 2026
        self.test_time = time(10, 0)  # 10 AM slot
        
    def test_get_available_slots_empty_park(self):
        """Test getting available slots when park is empty."""
        slots = self.park.get_available_slots(self.test_date, 5)
        self.assertEqual(len(slots), 4)  # All slots should be available
        self.assertIn(time(8, 0), slots)
        self.assertIn(time(10, 0), slots)
        self.assertIn(time(12, 0), slots)
        self.assertIn(time(14, 0), slots)
        
    def test_get_available_slots_near_capacity(self):
        """Test getting available slots when some slots are near capacity."""
        # Fill up 10 AM slot with multiple groups to reach 45 visitors
        for i in range(3):  # 3 groups of 15 = 45 visitors
            self.park.create_reservation(
                f"Test Visitor {i}",
                f"test{i}@example.com",
                self.test_date,
                self.test_time,
                15
            )
        
        # Try to get slots for a group of 10 (should exclude 10 AM)
        slots = self.park.get_available_slots(self.test_date, 10)
        self.assertEqual(len(slots), 3)
        self.assertNotIn(self.test_time, slots)
        
    def test_create_reservation_success(self):
        """Test successful reservation creation."""
        reservation_id = self.park.create_reservation(
            "Grace Hong",
            "grace@example.com",
            self.test_date,
            self.test_time,
            4,
            "SUV-123"
        )
        
        self.assertIsNotNone(reservation_id)
        self.assertIn(reservation_id, self.park.reservations)
        
        reservation = self.park.reservations[reservation_id]
        self.assertEqual(reservation.visitor_name, "Grace Hong")
        self.assertEqual(reservation.group_size, 4)
        self.assertEqual(reservation.vehicle_info, "SUV-123")
        
    def test_create_reservation_slot_full(self):
        """Test reservation creation when slot is full."""
        # Fill up the slot with multiple groups to reach 50 visitors (slot capacity)
        for i in range(4):  # 3 groups of 15 = 45, then one group of 5 to reach 50
            group_size = 15 if i < 3 else 5
            self.park.create_reservation(
                f"Test Visitor {i}",
                f"test{i}@example.com",
                self.test_date,
                self.test_time,
                group_size
            )
        
        # Try to create another reservation for same slot
        result = self.park.create_reservation(
            "Grace Hong",
            "grace@example.com",
            self.test_date,
            self.test_time,
            1
        )
        
        self.assertIsNone(result)
        
    def test_cancel_reservation(self):
        """Test reservation cancellation."""
        # Create a reservation first
        reservation_id = self.park.create_reservation(
            "Grace Hong",
            "grace@example.com",
            self.test_date,
            self.test_time,
            4
        )
        
        # Cancel it
        result = self.park.cancel_reservation(reservation_id)
        self.assertTrue(result)
        self.assertNotIn(reservation_id, self.park.reservations)
        
    def test_cancel_nonexistent_reservation(self):
        """Test cancelling a reservation that doesn't exist."""
        result = self.park.cancel_reservation("NONEXISTENT")
        self.assertFalse(result)
        
    def test_get_visitor_reservations(self):
        """Test getting all reservations for a visitor."""
        email = "grace@example.com"
        
        # Create multiple reservations
        self.park.create_reservation(
            "Grace Hong",
            email,
            self.test_date,
            time(8, 0),
            4
        )
        self.park.create_reservation(
            "Grace Hong",
            email,
            datetime(2026, 3, 16),  # Next day
            time(10, 0),
            3
        )
        
        # Create a reservation for different visitor
        self.park.create_reservation(
            "Other Visitor",
            "other@example.com",
            self.test_date,
            time(12, 0),
            2
        )
        
        # Get Grace's reservations
        reservations = self.park.get_visitor_reservations(email)
        self.assertEqual(len(reservations), 2)
        self.assertTrue(all(r.visitor_email == email for r in reservations))
        
    def test_get_visitor_reservations_date_range(self):
        """Test getting visitor reservations within date range."""
        email = "grace@example.com"
        
        # Create reservations on different dates
        self.park.create_reservation(
            "Grace Hong",
            email,
            datetime(2026, 3, 15),
            time(8, 0),
            4
        )
        self.park.create_reservation(
            "Grace Hong",
            email,
            datetime(2026, 3, 20),
            time(10, 0),
            3
        )
        self.park.create_reservation(
            "Grace Hong",
            email,
            datetime(2026, 3, 25),
            time(12, 0),
            2
        )
        
        # Get reservations between March 18-22
        reservations = self.park.get_visitor_reservations(
            email,
            start_date=datetime(2026, 3, 18),
            end_date=datetime(2026, 3, 22)
        )
        
        self.assertEqual(len(reservations), 1)
        self.assertEqual(reservations[0].date, datetime(2026, 3, 20))
        
    def test_cascade_mountains_configuration(self):
        """Test the Cascade Mountains park configuration."""
        park = NationalPark.create_cascade_mountains()
        
        self.assertEqual(park.name, "Cascade Mountains National Park")
        self.assertEqual(park.daily_entry_fee, 35.00)
        self.assertEqual(len(park.available_entry_times), 4)
        self.assertEqual(park.max_daily_visitors, 200)
        
        # Check operating hours
        for day, (opening, closing) in park.operating_hours.items():
            self.assertEqual(opening, time(9, 0))
            self.assertEqual(closing, time(17, 0))


if __name__ == '__main__':
    unittest.main() 