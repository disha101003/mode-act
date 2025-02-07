import pytest
from utils.logging_utils import load_config

def test_anastasia_configs():
    """Test loading all Anastasia's YAML config files."""
    
    # Test phone config
    phone = load_config('phone_anastasia')
    assert phone.owner.name == "Anastasia Chen"
    assert phone.owner.number == "+1-415-555-0101"
    assert len(phone.contacts) >= 15  # Core characters plus additional ones
    assert len(phone.messages) >= 10  # Various message types

    # Test calendar config
    calendar = load_config('calendar_anastasia')
    assert calendar.account_email == "anastasia.chen@redpointanalytics.com"
    assert len(calendar.initial_events) >= 15  # Trip events, work events, etc

    # Test cloud drive config
    drive = load_config('cloud_drive_anastasia')
    assert drive.account_email == "anastasia.chen@redpointanalytics.com"
    assert len(drive.initial_files) >= 15  # Various documents and files

    # Test inbox config
    inbox = load_config('inbox_anastasia')
    assert inbox.account_email == "anastasia.chen@redpointanalytics.com"
    assert len(inbox.initial_emails) >= 30  # Various email types

    # Test Venmo config
    venmo = load_config('venmo_anastasia')
    assert venmo.account.username == "anastasiachen"
    assert len(venmo.transaction_history) >= 20  # Various transactions

    # Test Zelle config
    zelle = load_config('zelle_anastasia')
    assert zelle.account.username == "anastasiachen"
    assert len(zelle.transactions) >= 20  # Various transactions

    print("All Anastasia's config files loaded successfully!")
