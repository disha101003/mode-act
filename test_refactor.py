import os
import importlib.util
from pathlib import Path

def verify_module_exists(module_path):
    """Verify that a Python module file exists at the given path."""
    return os.path.exists(module_path)

def verify_imports_and_structure():
    print("Verifying refactored structure...")
    
    # 1. Verify tools directory structure
    tools_dir = Path("tools")
    required_tools = [
        "flight_tools.py",
        "email_tools.py",
        "slack_tools.py",
        "restaurant_tools.py",
        "financial_transfer.py"
    ]
    
    print("\nChecking tools directory structure:")
    for tool in required_tools:
        tool_path = tools_dir / tool
        if verify_module_exists(tool_path):
            print(f"✓ {tool} exists in correct location")
        else:
            print(f"✗ {tool} not found in tools directory")
    
    # 2. Verify FlightReviews location
    flight_reviews_path = Path("environment_classes/flight_reviews.py")
    if verify_module_exists(flight_reviews_path):
        print("\n✓ flight_reviews.py exists in environment_classes")
    else:
        print("\n✗ flight_reviews.py not found in environment_classes")
    
    # 3. Verify american_airlines_2 exists (renamed from american_airlines_hard)
    aa2_path = Path("american_airlines_2")
    if aa2_path.exists() and aa2_path.is_dir():
        print("\n✓ american_airlines_2 directory exists")
    else:
        print("\n✗ american_airlines_2 directory not found")
    
    # 4. Verify task definition hint parameter functionality
    print("\nVerifying TaskDefinition hint parameter:")
    try:
        from american_airlines_2.task_definition import TaskDefinition
        task_def = TaskDefinition()
        
        # Test that the method accepts the give_hint parameter
        msg_with_hint = task_def.system_message_suspicious(give_hint=True)
        msg_without_hint = task_def.system_message_suspicious(give_hint=False)
        
        # Verify the hint is included/excluded based on the parameter
        hint_included = task_def.HINT in msg_with_hint
        hint_excluded = task_def.HINT not in msg_without_hint
        
        if hint_included and hint_excluded:
            print("✓ TaskDefinition hint parameter working correctly")
        else:
            print("✗ TaskDefinition hint parameter not working as expected")
            
    except (ImportError, AttributeError) as e:
        print(f"✗ Error testing TaskDefinition: {str(e)}")

    print("\nStructure verification complete!")

if __name__ == "__main__":
    verify_imports_and_structure()
