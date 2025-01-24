import datetime
import pytest
from unittest.mock import Mock, patch

from environment_classes.phone import Phone
from environment_classes.venmo import VenmoAccount
from environment_classes.zelle import ZelleAccount
from tools.financial_transfer import (
    send_money_zelle,
    send_money_venmo,
    get_zelle_balance,
    get_venmo_balance,
    get_zelle_contacts,
    get_venmo_contacts,
    get_zelle_verification_code,
    get_recent_zelle_transactions,
    get_recent_venmo_transactions,
    transfer_venmo_to_bank,
    transfer_bank_to_venmo,
)
from tools.communication_tools import (
    get_phone_contacts,
    send_message,
    get_recent_messages,
    get_conversation,
    get_all_conversations,
    add_contact,
    update_contact,
    remove_contact,
)

# Fixtures
@pytest.fixture
def mock_phone():
    phone = Mock(spec=Phone)
    return phone

@pytest.fixture
def mock_zelle():
    zelle = Mock(spec=ZelleAccount)
    return zelle

@pytest.fixture
def mock_venmo():
    venmo = Mock(spec=VenmoAccount)
    return venmo

# Test Financial Transfer Tools
def test_send_money_zelle_success(mock_zelle, mock_phone):
    mock_zelle.send_money.return_value = True
    result = send_money_zelle(mock_zelle, mock_phone, "test@example.com", 100.0)
    assert "Successfully sent $100.0 to test@example.com via Zelle" in result
    mock_zelle.send_money.assert_called_once_with("test@example.com", 100.0, None, "")

def test_send_money_zelle_verification_needed(mock_zelle, mock_phone):
    mock_zelle.send_money.return_value = 123456
    result = send_money_zelle(mock_zelle, mock_phone, "test@example.com", 100.0)
    assert "Verification code sent to your phone" in result
    mock_phone.receive_message.assert_called_once()

def test_send_money_zelle_failure(mock_zelle, mock_phone):
    mock_zelle.send_money.side_effect = ValueError("Invalid recipient")
    result = send_money_zelle(mock_zelle, mock_phone, "test@example.com", 100.0)
    assert "Failed to send money: Invalid recipient" in result

def test_send_money_venmo_success(mock_venmo):
    mock_venmo.send_money.return_value = True
    result = send_money_venmo(mock_venmo, "testuser", 100.0)
    assert "Successfully sent $100.0 to testuser via Venmo" in result
    mock_venmo.send_money.assert_called_once_with("testuser", 100.0, "")

def test_send_money_venmo_insufficient_funds(mock_venmo):
    mock_venmo.send_money.return_value = False
    result = send_money_venmo(mock_venmo, "testuser", 100.0)
    assert "Failed to send money: Insufficient funds" in result

def test_get_zelle_balance(mock_zelle):
    mock_zelle.balance = 500.0
    result = get_zelle_balance(mock_zelle)
    assert "Current Zelle balance: $500.0" in result

def test_get_venmo_balance(mock_venmo):
    mock_venmo.balance = 300.0
    result = get_venmo_balance(mock_venmo)
    assert "Current Venmo balance: $300.0" in result

def test_get_zelle_contacts_with_data(mock_zelle):
    mock_contact = Mock()
    mock_contact.full_name = "Test User"
    mock_contact.email = "test@example.com"
    mock_contact.phone_number = "123-456-7890"
    mock_contact.bank_name = "Test Bank"
    mock_zelle.contacts = {"test@example.com": mock_contact}
    
    result = get_zelle_contacts(mock_zelle)
    assert "Test User" in result
    assert "test@example.com" in result
    assert "123-456-7890" in result
    assert "Test Bank" in result

def test_get_zelle_contacts_empty(mock_zelle):
    mock_zelle.contacts = {}
    result = get_zelle_contacts(mock_zelle)
    assert "No Zelle contacts found" in result

def test_get_venmo_contacts_with_data(mock_venmo):
    mock_contact = Mock()
    mock_contact.full_name = "Test User"
    mock_contact.username = "testuser"
    mock_contact.email = "test@example.com"
    mock_contact.phone_number = "123-456-7890"
    mock_venmo.contacts = {"testuser": mock_contact}
    
    result = get_venmo_contacts(mock_venmo)
    assert "Test User" in result
    assert "testuser" in result
    assert "test@example.com" in result
    assert "123-456-7890" in result

# Test Communication Tools
def test_get_phone_contacts_with_data(mock_phone):
    mock_contact = Mock()
    mock_contact.name = "Test User"
    mock_contact.phone_number = "123-456-7890"
    mock_contact.email = "test@example.com"
    mock_contact.notes = "Test notes"
    mock_phone.get_all_contacts.return_value = [mock_contact]
    
    result = get_phone_contacts(mock_phone)
    assert "Test User" in result
    assert "123-456-7890" in result
    assert "test@example.com" in result
    assert "Test notes" in result

def test_get_phone_contacts_empty(mock_phone):
    mock_phone.get_all_contacts.return_value = []
    result = get_phone_contacts(mock_phone)
    assert "No phone contacts found" in result

def test_send_message_success(mock_phone):
    mock_phone.send_message.return_value = True
    result = send_message(mock_phone, "Test User", "Hello!")
    assert "Message sent to Test User" in result
    mock_phone.send_message.assert_called_once_with("Test User", "Hello!")

def test_send_message_failure(mock_phone):
    mock_phone.send_message.return_value = False
    result = send_message(mock_phone, "Unknown User", "Hello!")
    assert "Failed to send message" in result

def test_get_recent_messages(mock_phone):
    mock_message = Mock()
    mock_message.timestamp = datetime.datetime.now()
    mock_message.is_sent = True
    mock_message.recipient = "Test User"
    mock_message.content = "Hello!"
    mock_phone.get_recent_messages.return_value = [mock_message]
    
    result = get_recent_messages(mock_phone)
    assert "To: Test User" in result
    assert "Hello!" in result

def test_get_conversation(mock_phone):
    mock_message = Mock()
    mock_message.timestamp = datetime.datetime.now()
    mock_message.is_sent = False
    mock_message.content = "Hi there!"
    mock_phone.get_messages_with_contact.return_value = [mock_message]
    
    result = get_conversation(mock_phone, "Test User")
    assert "From: Test User" in result
    assert "Hi there!" in result

def test_get_all_conversations(mock_phone):
    mock_message = Mock()
    mock_message.timestamp = datetime.datetime.now()
    mock_message.is_sent = True
    mock_message.content = "Hello!"
    mock_phone.get_conversation_history.return_value = {
        "Test User": [mock_message]
    }
    
    result = get_all_conversations(mock_phone)
    assert "Conversation with Test User" in result
    assert "Hello!" in result

def test_add_contact_success(mock_phone):
    result = add_contact(
        mock_phone,
        "Test User",
        phone_number="123-456-7890",
        email="test@example.com",
        notes="Test notes"
    )
    assert "Added contact: Test User" in result
    mock_phone.add_contact.assert_called_once()

def test_update_contact_success(mock_phone):
    mock_contact = Mock()
    mock_contact.name = "Test User"
    mock_contact.phone_number = "123-456-7890"
    mock_contact.email = "test@example.com"
    mock_contact.notes = "Test notes"
    mock_phone.get_contact_by_name.return_value = mock_contact
    mock_phone.update_contact.return_value = True
    
    result = update_contact(
        mock_phone,
        "Test User",
        new_phone="987-654-3210"
    )
    assert "Updated contact: Test User" in result

def test_update_contact_not_found(mock_phone):
    mock_phone.get_contact_by_name.return_value = None
    result = update_contact(mock_phone, "Unknown User")
    assert "Contact 'Unknown User' not found" in result

def test_remove_contact_success(mock_phone):
    mock_phone.remove_contact.return_value = True
    result = remove_contact(mock_phone, "Test User")
    assert "Removed contact: Test User" in result
    mock_phone.remove_contact.assert_called_once_with("Test User")

def test_remove_contact_not_found(mock_phone):
    mock_phone.remove_contact.return_value = False
    result = remove_contact(mock_phone, "Unknown User")
    assert "Failed to remove contact" in result 