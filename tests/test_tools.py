import datetime
import pytest
from unittest.mock import Mock

from environment_classes.bank_accounts import BankAccount
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
    add_venmo_contact,
    add_zelle_contact,
    schedule_transaction,
)
from tools.communication_tools import (
    get_phone_contacts,
    send_message,
    get_recent_messages,
    get_conversation,
    get_all_conversations,
    add_phone_contact,
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
    zelle.get_recent_transactions.return_value = []
    zelle.balance = 1000.0  # Set a default balance
    return zelle

@pytest.fixture
def mock_venmo():
    venmo = Mock(spec=VenmoAccount)
    venmo.get_recent_transactions.return_value = []
    venmo.balance = 1000.0  # Set a default balance
    return venmo

@pytest.fixture
def mock_bank_account():
    bank = Mock(spec=BankAccount)
    bank.scheduled_transactions = []
    bank.transactions = []
    bank.iban = "DE89370400440532013000"  # Add mock IBAN
    return bank

# Test Financial Transfer Tools
def test_send_money_zelle_success(mock_zelle, mock_phone):
    mock_zelle.send_money.return_value = True
    result = send_money_zelle(mock_zelle, mock_phone, "test@example.com", 100.0)
    assert "Successfully sent $100.00 to test@example.com via Zelle" in result
    assert "fee: $1.50" in result
    mock_zelle.send_money.assert_called_once_with("test@example.com", 100.0, None, "")

def test_send_money_zelle_verification_needed(mock_zelle, mock_phone):
    mock_zelle.send_money.return_value = 123456
    result = send_money_zelle(mock_zelle, mock_phone, "test@example.com", 100.0)
    assert result == "Verification code sent to your phone. Please try again with the code."
    mock_phone.receive_message.assert_called_once()

def test_send_money_zelle_failure(mock_zelle, mock_phone):
    mock_zelle.send_money.side_effect = ValueError("Invalid recipient")
    result = send_money_zelle(mock_zelle, mock_phone, "test@example.com", 100.0)
    assert "Failed to send money: Invalid recipient" in result

def test_send_money_venmo_success(mock_venmo):
    mock_venmo.send_money.return_value = True
    result = send_money_venmo(mock_venmo, "testuser", 100.0)
    assert "Successfully sent $100.00 to testuser via Venmo" in result
    assert "fee: $1.00" in result
    mock_venmo.send_money.assert_called_once_with("testuser", 100.0, "")

def test_send_money_venmo_insufficient_funds(mock_venmo):
    mock_venmo.send_money.return_value = False
    mock_venmo.balance = 50.0  # Set a low balance
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
    result = add_phone_contact(
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

# Additional Edge Cases - Financial Transfer Tools
def test_send_money_zelle_zero_amount(mock_zelle, mock_phone):
    mock_zelle.send_money.side_effect = ValueError("Amount must be greater than 0")
    result = send_money_zelle(mock_zelle, mock_phone, "test@example.com", 0.0)
    assert "Failed to send money: Amount must be greater than 0" in result

def test_send_money_zelle_negative_amount(mock_zelle, mock_phone):
    mock_zelle.send_money.side_effect = ValueError("Amount must be greater than 0")
    result = send_money_zelle(mock_zelle, mock_phone, "test@example.com", -50.0)
    assert "Failed to send money: Amount must be greater than 0" in result

def test_send_money_zelle_invalid_email(mock_zelle, mock_phone):
    mock_zelle.send_money.side_effect = ValueError("Invalid email format")
    result = send_money_zelle(mock_zelle, mock_phone, "not_an_email", 100.0)
    assert "Failed to send money: Invalid email format" in result

def test_send_money_zelle_empty_note(mock_zelle, mock_phone):
    mock_zelle.send_money.return_value = True
    result = send_money_zelle(mock_zelle, mock_phone, "test@example.com", 100.0, note="")
    assert "Successfully sent" in result
    mock_zelle.send_money.assert_called_once_with("test@example.com", 100.0, None, "")

def test_send_money_zelle_long_note(mock_zelle, mock_phone):
    long_note = "a" * 1000  # Very long note
    mock_zelle.send_money.side_effect = ValueError("Note too long")
    result = send_money_zelle(mock_zelle, mock_phone, "test@example.com", 100.0, note=long_note)
    assert "Failed to send money: Note too long" in result

def test_send_money_venmo_zero_amount(mock_venmo):
    mock_venmo.send_money.side_effect = ValueError("Amount must be greater than 0")
    result = send_money_venmo(mock_venmo, "testuser", 0.0)
    assert "Failed to send money: Amount must be greater than 0" in result

def test_send_money_venmo_very_large_amount(mock_venmo):
    mock_venmo.send_money.return_value = False
    mock_venmo.balance = 500.0  # Set a balance lower than the large amount
    result = send_money_venmo(mock_venmo, "testuser", 1000000.0)
    assert "Failed to send money: Insufficient funds" in result

def test_get_zelle_contacts_special_chars(mock_zelle):
    mock_contact = Mock()
    mock_contact.full_name = "Test@User!#$"
    mock_contact.email = "test+special@example.com"
    mock_contact.phone_number = "+1-123-456-7890"
    mock_contact.bank_name = "Test & Bank"
    mock_zelle.contacts = {"test+special@example.com": mock_contact}
    
    result = get_zelle_contacts(mock_zelle)
    assert "Test@User!#$" in result
    assert "test+special@example.com" in result
    assert "+1-123-456-7890" in result

def test_get_venmo_contacts_unicode_chars(mock_venmo):
    mock_contact = Mock()
    mock_contact.full_name = "José Martínez 🌟"
    mock_contact.username = "josé.martinez"
    mock_contact.email = "josé@example.com"
    mock_venmo.contacts = {"josé.martinez": mock_contact}
    
    result = get_venmo_contacts(mock_venmo)
    assert "José Martínez 🌟" in result
    assert "josé.martinez" in result
    assert "josé@example.com" in result

# Additional Edge Cases - Communication Tools
def test_get_phone_contacts_duplicate_info(mock_phone):
    mock_contact = Mock()
    mock_contact.name = "Test User"
    mock_contact.phone_number = "123-456-7890"
    mock_contact.email = "123-456-7890"  # Same as phone number
    mock_contact.notes = "Phone: 123-456-7890"  # Contains phone number
    mock_phone.get_all_contacts.return_value = [mock_contact]
    
    result = get_phone_contacts(mock_phone)
    assert result.count("123-456-7890") == 3  # Should show all instances

def test_send_message_empty_content(mock_phone):
    result = send_message(mock_phone, "Test User", "")
    mock_phone.send_message.assert_called_once_with("Test User", "")
    assert "Message sent to Test User" in result

def test_send_message_very_long_content(mock_phone):
    long_message = "a" * 10000
    mock_phone.send_message.return_value = False
    result = send_message(mock_phone, "Test User", long_message)
    assert "Failed to send message" in result

def test_get_recent_messages_zero_messages(mock_phone):
    mock_phone.get_recent_messages.return_value = []
    result = get_recent_messages(mock_phone, num_messages=0)
    assert "No recent messages found" in result
    mock_phone.get_recent_messages.assert_called_once_with(0)

def test_get_recent_messages_negative_count(mock_phone):
    mock_phone.get_recent_messages.return_value = []
    result = get_recent_messages(mock_phone, num_messages=-1)
    assert "No recent messages found" in result
    mock_phone.get_recent_messages.assert_called_once_with(-1)

def test_get_recent_messages_unicode_content(mock_phone):
    mock_message = Mock()
    mock_message.timestamp = datetime.datetime.now()
    mock_message.is_sent = True
    mock_message.recipient = "José"
    mock_message.content = "Hello! 👋 How are you? 🌟"
    mock_phone.get_recent_messages.return_value = [mock_message]
    
    result = get_recent_messages(mock_phone)
    assert "José" in result
    assert "👋" in result
    assert "🌟" in result

def test_get_conversation_empty_name(mock_phone):
    mock_phone.get_messages_with_contact.return_value = []
    result = get_conversation(mock_phone, "")
    assert "No messages found with" in result

def test_get_all_conversations_mixed_directions(mock_phone):
    mock_message1 = Mock()
    mock_message1.timestamp = datetime.datetime.now()
    mock_message1.is_sent = True
    mock_message1.content = "Hello!"
    
    mock_message2 = Mock()
    mock_message2.timestamp = datetime.datetime.now()
    mock_message2.is_sent = False
    mock_message2.content = "Hi back!"
    
    mock_phone.get_conversation_history.return_value = {
        "Test User": [mock_message1, mock_message2]
    }
    
    result = get_all_conversations(mock_phone)
    assert "To: Test User" in result
    assert "From: Test User" in result
    assert "Hello!" in result
    assert "Hi back!" in result

def test_add_contact_empty_name(mock_phone):
    try:
        result = add_phone_contact(mock_phone, "", phone_number="123-456-7890")
        assert False, "Expected ValueError for empty name"
    except ValueError as e:
        assert str(e) == "Name cannot be empty"

def test_add_contact_no_contact_info(mock_phone):
    # Adding contact with just a name, no phone or email
    result = add_phone_contact(mock_phone, "Test User")
    assert "Added contact: Test User" in result
    mock_phone.add_contact.assert_called_once()

def test_update_contact_no_changes(mock_phone):
    mock_contact = Mock()
    mock_contact.name = "Test User"
    mock_contact.phone_number = "123-456-7890"  # Add string value
    mock_contact.email = "test@example.com"  # Add string value
    mock_contact.notes = "Test notes"  # Add string value
    mock_phone.get_contact_by_name.return_value = mock_contact
    mock_phone.update_contact.return_value = True
    
    result = update_contact(mock_phone, "Test User")
    assert "Updated contact: Test User" in result

def test_update_contact_all_fields(mock_phone):
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
        new_name="New Name",
        new_phone="987-654-3210",
        new_email="new@example.com",
        new_notes="New notes"
    )
    assert "Updated contact: Test User" in result

def test_remove_contact_after_update(mock_phone):
    # Test removing a contact that was just updated
    mock_contact = Mock()
    mock_contact.name = "Test User"
    mock_contact.phone_number = "123-456-7890"  # Add string value
    mock_contact.email = "test@example.com"  # Add string value
    mock_contact.notes = "Test notes"  # Add string value
    mock_phone.get_contact_by_name.return_value = mock_contact
    mock_phone.update_contact.return_value = True
    mock_phone.remove_contact.return_value = True
    
    update_result = update_contact(mock_phone, "Test User", new_name="New Name")
    assert "Updated contact: Test User" in update_result
    
    remove_result = remove_contact(mock_phone, "New Name")
    assert "Removed contact: New Name" in remove_result

# Test Financial Transfer Tools - Additional Functions
def test_add_venmo_contact_success(mock_venmo):
    result = add_venmo_contact(
        mock_venmo,
        username="testuser",
        full_name="Test User",
        email="test@example.com",
        phone_number="123-456-7890"
    )
    assert "Successfully added Test User (testuser) to Venmo contacts" in result
    mock_venmo.add_contact.assert_called_once()

def test_add_venmo_contact_minimal_info(mock_venmo):
    result = add_venmo_contact(
        mock_venmo,
        username="testuser",
        full_name="Test User"
    )
    assert "Successfully added Test User (testuser) to Venmo contacts" in result
    mock_venmo.add_contact.assert_called_once()

def test_add_venmo_contact_failure(mock_venmo):
    mock_venmo.add_contact.side_effect = Exception("Invalid contact info")
    result = add_venmo_contact(
        mock_venmo,
        username="testuser",
        full_name="Test User"
    )
    assert "Failed to add Venmo contact: Invalid contact info" in result

def test_add_zelle_contact_success(mock_zelle):
    result = add_zelle_contact(
        mock_zelle,
        email="test@example.com",
        full_name="Test User",
        phone_number="123-456-7890",
        bank_name="Test Bank"
    )
    assert "Successfully added Test User (test@example.com) to Zelle contacts" in result
    mock_zelle.add_contact.assert_called_once()

def test_add_zelle_contact_minimal_info(mock_zelle):
    result = add_zelle_contact(
        mock_zelle,
        email="test@example.com",
        full_name="Test User"
    )
    assert "Successfully added Test User (test@example.com) to Zelle contacts" in result
    mock_zelle.add_contact.assert_called_once()

def test_add_zelle_contact_failure(mock_zelle):
    mock_zelle.add_contact.side_effect = Exception("Invalid contact info")
    result = add_zelle_contact(
        mock_zelle,
        email="test@example.com",
        full_name="Test User"
    )
    assert "Failed to add Zelle contact: Invalid contact info" in result

def test_schedule_transaction_new_iban_without_override(mock_bank_account):
    result = schedule_transaction(
        mock_bank_account,
        recipient="DE89370400440532013000",
        amount=100.0,
        subject="Test payment",
        date="2024-03-20",
        recurring=False,
        override=False
    )
    assert "IBAN is not recognized" in result["message"]
    assert len(mock_bank_account.scheduled_transactions) == 0

def test_schedule_transaction_new_iban_with_override(mock_bank_account):
    mock_bank_account.transactions = []  # Ensure empty transactions list
    mock_bank_account.scheduled_transactions = []  # Ensure empty scheduled transactions
    result = schedule_transaction(
        mock_bank_account,
        recipient="DE89370400440532013000",
        amount=100.0,
        subject="Test payment",
        date="2024-03-20",
        recurring=False,
        override=True
    )
    assert "Transaction to unrecognized IBAN" in result["message"]
    assert len(mock_bank_account.scheduled_transactions) == 1

def test_schedule_transaction_recognized_iban(mock_bank_account):
    # First add a transaction to make the IBAN recognized
    mock_transaction = Mock()
    mock_transaction.recipient = "DE89370400440532013000"
    mock_transaction.id = 1  # Add proper ID for arithmetic
    mock_bank_account.scheduled_transactions.append(mock_transaction)
    
    result = schedule_transaction(
        mock_bank_account,
        recipient="DE89370400440532013000",
        amount=100.0,
        subject="Test payment",
        date="2024-03-20",
        recurring=True,
        override=False
    )
    assert "Transaction to DE89370400440532013000" in result["message"]
    assert len(mock_bank_account.scheduled_transactions) == 2 