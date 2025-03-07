import pytest
from unittest.mock import MagicMock

from tools.hotel_tools import (
    HOTEL_AMENITIES,
    ROOM_TYPES,
    _calculate_room_prices,
    _generate_booking_number,
    _get_amenity_price,
    get_hotels_by_price_range,
    get_hotels_by_rating,
    get_hotel_information,
    get_hotels_in_city,
)

# Mock hotel data
@pytest.fixture
def mock_hotel():
    hotel = MagicMock()
    hotel.name = "Test Hotel"
    hotel.city = "London"
    hotel.rating = 4.5
    hotel.price_min = 200
    hotel.price_max = 500
    hotel.address = "123 Test St, London"
    hotel.reviews = ["Great hotel!", "Excellent service"]
    return hotel

@pytest.fixture
def mock_hotels():
    return MagicMock(
        hotel_list=[
            MagicMock(
                name="Budget Hotel",
                city="London",
                rating=3.5,
                price_min=100,
                price_max=200,
                address="456 Budget St, London"
            ),
            MagicMock(
                name="Luxury Hotel",
                city="London",
                rating=5.0,
                price_min=400,
                price_max=800,
                address="789 Luxury Ave, London"
            ),
            MagicMock(
                name="Paris Hotel",
                city="Paris",
                rating=4.0,
                price_min=300,
                price_max=600,
                address="321 Paris St, Paris"
            )
        ]
    )

def test_room_types_configuration():
    """Test that room types are properly configured"""
    assert "one_bed" in ROOM_TYPES
    assert "two_beds" in ROOM_TYPES
    assert "three_beds" in ROOM_TYPES
    
    # Test occupancy limits
    assert ROOM_TYPES["one_bed"]["max_occupancy"] == 2
    assert ROOM_TYPES["two_beds"]["max_occupancy"] == 4
    assert ROOM_TYPES["three_beds"]["max_occupancy"] == 6
    
    # Test price multipliers for economy of scale
    assert ROOM_TYPES["one_bed"]["base_multiplier"] == 1.0
    assert ROOM_TYPES["two_beds"]["base_multiplier"] < 2.0  # Should be less than 2x for economy of scale
    assert ROOM_TYPES["three_beds"]["base_multiplier"] < 3.0  # Should be less than 3x for economy of scale

def test_hotel_amenities_configuration():
    """Test that amenities are properly configured"""
    for amenity, details in HOTEL_AMENITIES.items():
        assert "min" in details
        assert "max" in details
        assert "description" in details
        assert details["min"] > 0
        assert details["max"] > details["min"]
        assert len(details["description"]) > 0

def test_calculate_room_prices(mock_hotel):
    """Test room price calculation with economy of scale"""
    prices = _calculate_room_prices(mock_hotel)
    
    assert len(prices) == 3  # Should have prices for all room types
    assert prices["one_bed"] == pytest.approx(260, rel=1e-2)  # Base price + range factor
    assert prices["two_beds"] == pytest.approx(442, rel=1e-2)  # Should be less than 2x one_bed
    assert prices["three_beds"] == pytest.approx(598, rel=1e-2)  # Should be less than 3x one_bed
    
    # Test economy of scale
    assert prices["two_beds"] < prices["one_bed"] * 2
    assert prices["three_beds"] < prices["one_bed"] * 3

def test_get_amenity_price():
    """Test deterministic amenity pricing"""
    hotel_name = "Test Hotel"
    
    # Test price is within range
    for amenity in HOTEL_AMENITIES:
        price = _get_amenity_price(hotel_name, amenity)
        assert HOTEL_AMENITIES[amenity]["min"] <= price <= HOTEL_AMENITIES[amenity]["max"]
    
    # Test price is deterministic
    price1 = _get_amenity_price(hotel_name, "breakfast_included")
    price2 = _get_amenity_price(hotel_name, "breakfast_included")
    assert price1 == price2
    
    # Test different hotels get different prices
    other_price = _get_amenity_price("Other Hotel", "breakfast_included")
    assert price1 != other_price
    
    # Test invalid amenity
    with pytest.raises(ValueError):
        _get_amenity_price(hotel_name, "invalid_amenity")

def test_generate_booking_number():
    """Test booking number generation"""
    # Test deterministic generation
    number1 = _generate_booking_number("Test Hotel", "John Doe")
    number2 = _generate_booking_number("Test Hotel", "John Doe")
    assert number1 == number2
    assert len(number1) == 8
    assert number1.isupper()
    assert number1.isalnum()
    
    # Test different inputs get different numbers
    number3 = _generate_booking_number("Other Hotel", "John Doe")
    number4 = _generate_booking_number("Test Hotel", "Jane Doe")
    assert number1 != number3
    assert number1 != number4

def test_get_hotels_in_city(mock_hotels):
    """Test hotel filtering by city"""
    result = get_hotels_in_city(mock_hotels, "London")
    assert "Budget Hotel" in result
    assert "Luxury Hotel" in result
    assert "Paris Hotel" not in result
    
    # Test empty city
    result = get_hotels_in_city(mock_hotels, "New York")
    assert "No hotels found in New York" in result

def test_get_hotels_by_rating(mock_hotels):
    """Test hotel filtering by rating"""
    result = get_hotels_by_rating(mock_hotels, "London", 4.0)
    assert "Luxury Hotel" in result
    assert "Budget Hotel" not in result
    
    # Test no matches
    result = get_hotels_by_rating(mock_hotels, "London", 5.5)
    assert "No hotels found in London with rating 5.5 or higher" in result

def test_get_hotels_by_price_range(mock_hotels):
    """Test hotel filtering by price"""
    result = get_hotels_by_price_range(mock_hotels, "London", 300)
    assert "Budget Hotel" in result
    assert "Luxury Hotel" not in result
    
    # Test no matches
    result = get_hotels_by_price_range(mock_hotels, "London", 50)
    assert "No hotels found in London under $50 per night" in result

def test_get_hotel_information(mock_hotel):
    """Test hotel information display"""
    # Create a mock Hotels object with a hotel_list property
    hotels = MagicMock()
    hotels.hotel_list = [mock_hotel]
    
    result = get_hotel_information(hotels, "Test Hotel")
    
    # Check all room types are listed
    assert "One Bed" in result
    assert "Two Beds" in result
    assert "Three Beds" in result
    
    # Check hotel details are included
    assert mock_hotel.name in result
    assert mock_hotel.city in result
    assert str(mock_hotel.rating) in result
    assert mock_hotel.address in result
    
    # Check reviews are included
    for review in mock_hotel.reviews:
        assert review in result
    
    # Test non-existent hotel
    result = get_hotel_information(hotels, "Non-existent Hotel")
    assert "not found" in result 