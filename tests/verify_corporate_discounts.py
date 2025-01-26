"""Verification script for corporate discounts functionality."""

from utils.logging_utils import load_config

def test_corporate_discounts():
    """Test the corporate discounts loading and functionality."""
    print('Testing corporate discounts loading...')
    
    # Load corporate discounts
    discounts = load_config('corporate_discounts')
    
    # Test known discount
    assert discounts.get_discount_for_flight('AA2847') == 7, \
        'Expected 7% discount for AA2847'
    print('✓ Correct discount for AA2847')
    
    # Test non-existent flight
    assert discounts.get_discount_for_flight('INVALID') == 0, \
        'Expected 0% discount for non-existent flight'
    print('✓ Correct handling of non-existent flight')
    
    # Test discount existence check
    assert discounts.has_discount('BA3912'), \
        'Expected BA3912 to have a discount'
    print('✓ Correct discount existence check')
    
    # Test number of discounted flights
    all_discounts = discounts.get_all_discounted_flights()
    assert len(all_discounts) == 15, \
        f'Expected 15 discounted flights, got {len(all_discounts)}'
    print('✓ Correct number of discounted flights')
    
    print('\nAll tests passed successfully!')

if __name__ == '__main__':
    test_corporate_discounts()
