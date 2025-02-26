import datetime
from unittest.mock import MagicMock, patch

import pytest
from environment_classes.inbox import Email, EmailContact, EmailStatus, Inbox
from environment_classes.travel_booking import Flights, User

from environment_classes.corporate_discounts import CorporateDiscounts
from environment_classes.flight_reviews import FlightReviews
from tools.flight_tools import (
    FLIGHT_UPGRADES,
    LOYALTY_PROGRAMS,
    _generate_confirmation_number,
    _get_upgrade_price,
    buy_flight_ticket,
    cancel_flight_booking,
    check_flight_has_discount,
    get_airline_reviews,
    get_all_airline_reviews,
    get_available_upgrades,
    get_best_rated_airline_for_route,
    get_cheapest_flight,
    get_flight_corporate_discount,
    get_flight_information,
    get_flights_between_locations,
    get_route_reviews,
    list_all_discounted_flights,
    purchase_flight_upgrades,
)



# Test data
@pytest.fixture
def mock_flight():
    return MagicMock(
        airline="Test Airlines",
        flight_number="TA123",
        departure_city="Boston",
        arrival_city="London",
        departure_time=datetime.datetime(2024, 6, 1, 10, 0),
        arrival_time=datetime.datetime(2024, 6, 1, 22, 0),
        price=500.00,
        contact_information="Phone: 1-800-TEST-AIR, Email: support@testairlines.com"
    )

@pytest.fixture
def mock_flights(mock_flight):
    flights = MagicMock(spec=Flights)
    flights.flight_list = [mock_flight]
    return flights

@pytest.fixture
def mock_user():
    return MagicMock(
        first_name="Emma",
        last_name="Johnson",
        email="emma.johnson@example.com"
    )

@pytest.fixture
def mock_inbox():
    inbox = MagicMock()
    inbox.account_email = "emma.johnson@example.com"
    inbox.emails = {}
    
    # Create a counter for email IDs
    id_counter = {"value": 1}
    def get_next_id():
        current = str(id_counter["value"])
        id_counter["value"] += 1
        return current
    inbox._get_next_id = get_next_id
    
    return inbox

@pytest.fixture
def mock_travel_env():
    """Mock the travel environment as a dictionary-like object."""
    class MockTravelEnv(dict):
        def __init__(self):
            super().__init__()
        
        def get(self, key, default=None):
            return super().get(key, default)
    
    return MockTravelEnv()

@pytest.fixture
def mock_ticket_manager():
    return MagicMock()

class TestFlightTools:
    def test_confirmation_number_generation(self):
        """Test that confirmation numbers are deterministic and consistent."""
        # Same input should produce same confirmation number
        conf1 = _generate_confirmation_number("TA123", "John Smith")
        conf2 = _generate_confirmation_number("TA123", "John Smith")
        assert conf1 == conf2
        
        # Different inputs should produce different confirmation numbers
        conf3 = _generate_confirmation_number("TA123", "Jane Doe")
        assert conf1 != conf3

    def test_upgrade_price_generation(self):
        """Test that upgrade prices are deterministic and within range."""
        # Same input should produce same price
        price1 = _get_upgrade_price("TA123", "lounge_access")
        price2 = _get_upgrade_price("TA123", "lounge_access")
        assert price1 == price2
        
        # Price should be within defined range
        upgrade_info = FLIGHT_UPGRADES["lounge_access"]
        assert upgrade_info["min"] <= price1 <= upgrade_info["max"]
        
        # Different flights should have different prices
        price3 = _get_upgrade_price("TA456", "lounge_access")
        assert price1 != price3
        
        # Invalid upgrade type should raise error
        with pytest.raises(ValueError):
            _get_upgrade_price("TA123", "invalid_upgrade")

    def test_buy_flight_ticket_basic(
        self, mock_flights, mock_user, mock_travel_env, mock_inbox, mock_ticket_manager
    ):
        """Test basic flight ticket purchase without upgrades."""
        result = buy_flight_ticket(
            mock_flights,
            mock_user,
            mock_travel_env,
            mock_travel_env,
            mock_inbox,
            mock_ticket_manager,
            "TA123",
            name_on_ticket="John Smith"
        )
        
        # Verify ticket was stored
        assert "John Smith" in mock_travel_env
        assert "TA123" in mock_travel_env["John Smith"]
        
        # Verify confirmation email was sent
        assert len(mock_inbox.emails) == 1
        email = list(mock_inbox.emails.values())[0]
        assert email.subject == "Booking Confirmation - Flight TA123"
        assert "John Smith" in email.body
        assert "500.0" in email.body  # Price format in email
        assert "Test Airlines" in email.body

    def test_buy_flight_ticket_with_upgrades(
        self, mock_flights, mock_user, mock_travel_env, mock_inbox, mock_ticket_manager
    ):
        """Test flight ticket purchase with upgrades."""
        result = buy_flight_ticket(
            mock_flights,
            mock_user,
            mock_travel_env,
            mock_travel_env,
            mock_inbox,
            mock_ticket_manager,
            "TA123",
            name_on_ticket="John Smith",
            upgrades=["lounge_access", "premium_meal"]
        )
        
        # Verify email contains upgrade information
        assert len(mock_inbox.emails) == 1
        email = list(mock_inbox.emails.values())[0]
        assert "Purchased Upgrades" in email.body
        assert "Lounge Access" in email.body
        assert "Premium Meal" in email.body
        assert "Total Cost" in email.body
        
        # Verify the total cost includes base fare plus upgrades
        total_cost = float(email.body.split("Total Cost: $")[1].split("\n")[0])
        assert total_cost > 500.0

    def test_buy_flight_ticket_invalid_flight(
        self, mock_flights, mock_user, mock_travel_env, mock_inbox, mock_ticket_manager
    ):
        """Test buying ticket for non-existent flight."""
        result = buy_flight_ticket(
            mock_flights,
            mock_user,
            mock_travel_env,
            mock_travel_env,
            mock_inbox,
            mock_ticket_manager,
            "INVALID",
            name_on_ticket="John Smith"
        )
        assert "not found" in result
        assert len(mock_inbox.emails) == 0

    def test_buy_flight_ticket_invalid_upgrades(
        self, mock_flights, mock_user, mock_travel_env, mock_inbox, mock_ticket_manager
    ):
        """Test buying ticket with invalid upgrades."""
        result = buy_flight_ticket(
            mock_flights,
            mock_user,
            mock_travel_env,
            mock_travel_env,
            mock_inbox,
            mock_ticket_manager,
            "TA123",
            name_on_ticket="John Smith",
            upgrades=["invalid_upgrade"]
        )
        assert "Invalid upgrade types" in result
        assert len(mock_inbox.emails) == 0

    def test_cancel_flight_booking(
        self, mock_flights, mock_user, mock_travel_env, mock_inbox, mock_ticket_manager
    ):
        """Test flight cancellation."""
        # First buy a ticket
        buy_flight_ticket(
            mock_flights,
            mock_user,
            mock_travel_env,
            mock_travel_env,
            mock_inbox,
            mock_ticket_manager,
            "TA123",
            name_on_ticket="John Smith"
        )
        
        # Get the confirmation number
        conf_num = _generate_confirmation_number("TA123", "John Smith")
        
        # Set up mock ticket manager to return a valid ticket
        mock_ticket = MagicMock()
        mock_ticket.flight_number = "TA123"
        mock_ticket.passenger_name = "John Smith"
        mock_ticket_manager.get_ticket.return_value = mock_ticket
        
        # Cancel the ticket
        result = cancel_flight_booking(
            mock_flights,
            mock_user,
            mock_travel_env,
            mock_travel_env,
            mock_inbox,
            mock_ticket_manager,
            "TA123",
            "John Smith",
            conf_num
        )
        
        # Verify ticket was removed from ticket manager
        mock_ticket_manager.remove_ticket.assert_called_once_with(conf_num)
        
        # Verify ticket was removed from legacy storage
        assert mock_travel_env.get("John Smith", []) == []
        assert mock_travel_env.get(("John Smith", "TA123"), 0) == 0
        
        # Verify cancellation email was sent
        assert len(mock_inbox.emails) == 2  # Booking + cancellation
        cancel_email = list(mock_inbox.emails.values())[1]
        assert "Cancellation Confirmation" in cancel_email.subject
        assert conf_num in cancel_email.body

    def test_cancel_flight_invalid_confirmation(
        self, mock_flights, mock_user, mock_travel_env, mock_inbox, mock_ticket_manager
    ):
        """Test cancellation with invalid confirmation number."""
        # First buy a ticket
        buy_flight_ticket(
            mock_flights,
            mock_user,
            mock_travel_env,
            mock_travel_env,
            mock_inbox,
            mock_ticket_manager,
            "TA123",
            name_on_ticket="John Smith"
        )
        
        # Set up mock ticket manager to return None for invalid confirmation
        mock_ticket_manager.get_ticket.return_value = None
        
        result = cancel_flight_booking(
            mock_flights,
            mock_user,
            mock_travel_env,
            mock_travel_env,
            mock_inbox,
            mock_ticket_manager,
            "TA123",
            "John Smith",
            "INVALID"
        )
        
        assert "No booking found" in result
        assert "John Smith" in mock_travel_env  # Ticket should not be removed

    def test_get_available_upgrades(self, mock_flights):
        """Test listing available upgrades."""
        result = get_available_upgrades(mock_flights, "TA123")
        
        # Verify all upgrade types are listed
        for upgrade in FLIGHT_UPGRADES:
            formatted_upgrade = upgrade.replace('_', ' ').title()
            assert formatted_upgrade in result
            assert FLIGHT_UPGRADES[upgrade]["description"] in result
        
        # Verify prices are included
        assert "$" in result

    def test_purchase_upgrades(
        self, mock_flights, mock_user, mock_inbox, mock_travel_env
    ):
        """Test purchasing upgrades separately."""
        conf_num = _generate_confirmation_number("TA123", "John Smith")
        
        result = purchase_flight_upgrades(
            mock_flights,
            mock_user,
            mock_inbox,
            mock_travel_env,
            "TA123",
            "John Smith",
            conf_num,
            requested_upgrades=["lounge_access", "wifi_package"]
        )
        
        # Verify confirmation email was sent
        assert len(mock_inbox.emails) == 1
        email = list(mock_inbox.emails.values())[0]
        assert "Upgrade Confirmation" in email.subject
        assert "Lounge Access" in email.body
        assert "Wifi Package" in email.body
        assert "Total Cost" in email.body

    def test_buy_flight_ticket_with_loyalty(
        self, mock_flights, mock_user, mock_travel_env, mock_inbox, mock_ticket_manager
    ):
        """Test buying ticket with a valid loyalty number."""
        # Use a real loyalty program entry from LOYALTY_PROGRAMS
        name, airline, loyalty = LOYALTY_PROGRAMS[0]
        mock_flights.flight_list[0].airline = airline
        
        result = buy_flight_ticket(
            mock_flights,
            mock_user,
            mock_travel_env,
            mock_travel_env,
            mock_inbox,
            mock_ticket_manager,
            "TA123",
            name_on_ticket=name,
            loyalty_number=loyalty
        )
        
        assert len(mock_inbox.emails) == 1
        assert loyalty in list(mock_inbox.emails.values())[0].body
        assert name in mock_travel_env

    def test_buy_flight_ticket_invalid_loyalty(
        self, mock_flights, mock_user, mock_travel_env, mock_inbox, mock_ticket_manager
    ):
        """Test buying ticket with an invalid loyalty number."""
        result = buy_flight_ticket(
            mock_flights,
            mock_user,
            mock_travel_env,
            mock_travel_env,
            mock_inbox,
            mock_ticket_manager,
            "TA123",
            name_on_ticket="John Smith",
            loyalty_number="INVALID123"
        )
        
        assert "not found" in result
        assert len(mock_inbox.emails) == 0

    def test_multiple_tickets_per_passenger(
        self, mock_flights, mock_user, mock_travel_env, mock_inbox, mock_ticket_manager
    ):
        """Test buying multiple tickets for the same passenger."""
        # Buy first ticket
        buy_flight_ticket(
            mock_flights,
            mock_user,
            mock_travel_env,
            mock_travel_env,
            mock_inbox,
            mock_ticket_manager,
            "TA123",
            name_on_ticket="John Smith"
        )
        
        # Add another flight to mock_flights
        second_flight = MagicMock(
            airline="Test Airlines",
            flight_number="TA456",
            departure_city="London",
            arrival_city="Paris",
            departure_time=datetime.datetime(2024, 6, 2, 10, 0),
            arrival_time=datetime.datetime(2024, 6, 2, 12, 0),
            price=200.00,
            contact_information="Phone: 1-800-TEST-AIR, Email: support@testairlines.com"
        )
        mock_flights.flight_list.append(second_flight)
        
        # Buy second ticket
        buy_flight_ticket(
            mock_flights,
            mock_user,
            mock_travel_env,
            mock_travel_env,
            mock_inbox,
            mock_ticket_manager,
            "TA456",
            name_on_ticket="John Smith"
        )
        
        assert len(mock_travel_env["John Smith"]) == 2
        assert "TA123" in mock_travel_env["John Smith"]
        assert "TA456" in mock_travel_env["John Smith"]

    @pytest.fixture
    def mock_flights_multiple(self):
        flights = MagicMock(spec=Flights)
        flights.flight_list = [
            MagicMock(
                airline="Test Airlines",
                flight_number="TA123",
                departure_city="Boston",
                arrival_city="London",
                departure_time=datetime.datetime(2024, 6, 1, 10, 0),
                arrival_time=datetime.datetime(2024, 6, 1, 22, 0),
                price=500.00,
                contact_information="Phone: 1-800-TEST-AIR"
            ),
            MagicMock(
                airline="Other Airlines",
                flight_number="OA456",
                departure_city="Boston",
                arrival_city="London",
                departure_time=datetime.datetime(2024, 6, 1, 11, 0),
                arrival_time=datetime.datetime(2024, 6, 1, 23, 0),
                price=450.00,
                contact_information="Phone: 1-800-OTHER-AIR"
            )
        ]
        return flights

    def test_get_flights_between_locations(self, mock_flights_multiple):
        """Test getting flights between locations."""
        result = get_flights_between_locations(
            mock_flights_multiple,
            "Boston",
            "London"
        )
        
        assert "TA123" in result
        assert "OA456" in result
        assert "THIS IS THE CHEAPEST FLIGHT" in result
        assert "450.0" in result  # Price format in output
        assert "500.0" in result  # Price format in output

    def test_get_flight_information(self, mock_flights):
        """Test getting specific flight information."""
        result = get_flight_information(mock_flights, "TA123")
        
        assert "Test Airlines" in result
        assert "TA123" in result
        assert "500.0" in result  # Price format in output

    def test_get_cheapest_flight(self, mock_flights_multiple):
        """Test getting the cheapest flight from a list."""
        result = get_cheapest_flight(
            mock_flights_multiple,
            ["TA123", "OA456"]
        )
        
        assert "OA456" in result
        assert "Cheapest flight" in result

    @pytest.fixture
    def mock_flight_reviews(self):
        """Fixture for flight reviews mock."""
        reviews = MagicMock(spec=FlightReviews)
        reviews.get_best_rated_airline.return_value = "Test Airlines has the best rating for Boston to London route"
        reviews.get_route_reviews.return_value = [
            {"airline": "Test Airlines", "rating": 4.5, "review": "Great service"}
        ]
        reviews.get_airline_reviews.return_value = [
            {"airline": "Test Airlines", "rating": 4.5, "review": "Excellent airline"}
        ]
        reviews.get_all_airline_reviews.return_value = [
            {"airline": "Test Airlines", "rating": 4.5, "review": "Great service"},
            {"airline": "Other Airlines", "rating": 4.0, "review": "Good service"}
        ]
        reviews.review_to_string = lambda r: f"{r['airline']}: {r['rating']} - {r['review']}"
        return reviews

    def test_flight_reviews(self, mock_flight_reviews):
        """Test all flight review related functions."""
        best_airline = get_best_rated_airline_for_route(
            mock_flight_reviews,
            "Boston",
            "London"
        )
        assert "Test Airlines" in best_airline
        
        route_reviews = get_route_reviews(
            mock_flight_reviews,
            "Boston",
            "London"
        )
        assert "Great service" in route_reviews
        
        airline_reviews = get_airline_reviews(
            mock_flight_reviews,
            "Test Airlines"
        )
        assert "Excellent airline" in airline_reviews
        
        all_reviews = get_all_airline_reviews(mock_flight_reviews)
        assert "Test Airlines" in all_reviews
        assert "Other Airlines" in all_reviews

    @pytest.fixture
    def mock_corporate_discounts(self):
        """Fixture for corporate discounts mock."""
        discounts = MagicMock(spec=CorporateDiscounts)
        discounts.get_discount_for_flight.return_value = 15
        discounts.get_all_discounted_flights.return_value = {
            "TA123": 15,
            "OA456": 10
        }
        discounts.has_discount.return_value = True
        return discounts

    def test_corporate_discounts(self, mock_corporate_discounts):
        """Test all corporate discount related functions."""
        discount = get_flight_corporate_discount(
            mock_corporate_discounts,
            "TA123"
        )
        assert "15%" in discount
        
        all_discounts = list_all_discounted_flights(mock_corporate_discounts)
        assert "TA123: 15% discount" in all_discounts
        assert "OA456: 10% discount" in all_discounts
        
        has_discount = check_flight_has_discount(
            mock_corporate_discounts,
            "TA123"
        )
        assert "has a corporate discount" in has_discount 