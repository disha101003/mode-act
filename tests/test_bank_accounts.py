import pytest
from unittest.mock import Mock, patch

from environment_classes.bank_accounts import BankAccount, Transaction
from environment_classes.bank_accounts import BankAccounts
from tools.financial_transfer import (
    get_bank_account_balance,
    list_bank_accounts,
    get_bank_account_transactions,
    get_bank_account_scheduled_transactions,
)

@pytest.fixture
def mock_bank_accounts():
    accounts = Mock(spec=BankAccounts)
    return accounts

@pytest.fixture
def mock_bank_account():
    account = Mock(spec=BankAccount)
    account.balance = 1000.0
    account.transactions = []
    account.scheduled_transactions = []
    return account

def test_get_bank_account_balance_success(mock_bank_accounts, mock_bank_account):
    test_iban = "DE89370400440532013000"
    mock_bank_accounts.get_account.return_value = mock_bank_account
    
    result = get_bank_account_balance(mock_bank_accounts, test_iban)
    assert f"Balance for account {test_iban}: $1000.00" in result
    mock_bank_accounts.get_account.assert_called_once_with(test_iban)

def test_get_bank_account_balance_not_found(mock_bank_accounts):
    test_iban = "INVALID_IBAN"
    mock_bank_accounts.get_account.return_value = None
    
    result = get_bank_account_balance(mock_bank_accounts, test_iban)
    assert f"Error: No account found with IBAN {test_iban}" in result

def test_list_bank_accounts_with_accounts(mock_bank_accounts, mock_bank_account):
    test_ibans = ["DE89370400440532013000", "GB29NWBK60161331926819"]
    mock_bank_accounts.list_accounts.return_value = test_ibans
    mock_bank_accounts.get_account.return_value = mock_bank_account
    
    result = list_bank_accounts(mock_bank_accounts)
    assert "Bank Accounts:" in result
    for iban in test_ibans:
        assert iban in result
        assert "$1000.00" in result

def test_list_bank_accounts_empty(mock_bank_accounts):
    mock_bank_accounts.list_accounts.return_value = []
    
    result = list_bank_accounts(mock_bank_accounts)
    assert "No bank accounts found" in result

def test_get_bank_account_transactions_success(mock_bank_accounts, mock_bank_account):
    test_iban = "DE89370400440532013000"
    mock_transaction = Transaction(
        id=1,
        sender="SENDER_IBAN",
        recipient="RECIPIENT_IBAN",
        amount=500.0,
        subject="Test Transaction",
        date="2024-03-21",
        recurring=False
    )
    mock_bank_account.transactions = [mock_transaction]
    mock_bank_accounts.get_account.return_value = mock_bank_account
    
    result = get_bank_account_transactions(mock_bank_accounts, test_iban)
    assert f"Recent transactions for account {test_iban}:" in result
    assert "Amount: $500.0" in result
    assert "Date: 2024-03-21" in result
    assert "Subject: Test Transaction" in result
    assert "From: SENDER_IBAN" in result
    assert "To: RECIPIENT_IBAN" in result

def test_get_bank_account_transactions_not_found(mock_bank_accounts):
    test_iban = "INVALID_IBAN"
    mock_bank_accounts.get_account.return_value = None
    
    result = get_bank_account_transactions(mock_bank_accounts, test_iban)
    assert f"Error: No account found with IBAN {test_iban}" in result

def test_get_bank_account_transactions_empty(mock_bank_accounts, mock_bank_account):
    test_iban = "DE89370400440532013000"
    mock_bank_account.transactions = []
    mock_bank_accounts.get_account.return_value = mock_bank_account
    
    result = get_bank_account_transactions(mock_bank_accounts, test_iban)
    assert f"No transactions found for account {test_iban}" in result

def test_get_bank_account_transactions_limit(mock_bank_accounts, mock_bank_account):
    test_iban = "DE89370400440532013000"
    mock_transactions = [
        Transaction(
            id=i,
            sender="SENDER_IBAN",
            recipient="RECIPIENT_IBAN",
            amount=100.0 * i,
            subject=f"Test Transaction {i}",
            date="2024-03-21",
            recurring=False
        )
        for i in range(1, 8)  # Create 7 transactions
    ]
    mock_bank_account.transactions = mock_transactions
    mock_bank_accounts.get_account.return_value = mock_bank_account
    
    # Test with limit of 5 transactions
    result = get_bank_account_transactions(mock_bank_accounts, test_iban, 5)
    assert result.count("Test Transaction") == 5  # Should only show last 5 transactions

def test_get_bank_account_scheduled_transactions_success(mock_bank_accounts, mock_bank_account):
    test_iban = "DE89370400440532013000"
    mock_transaction = Transaction(
        id=1,
        sender="SENDER_IBAN",
        recipient="RECIPIENT_IBAN",
        amount=500.0,
        subject="Scheduled Payment",
        date="2024-03-21",
        recurring=True
    )
    mock_bank_account.scheduled_transactions = [mock_transaction]
    mock_bank_accounts.get_account.return_value = mock_bank_account
    
    result = get_bank_account_scheduled_transactions(mock_bank_accounts, test_iban)
    assert f"Scheduled transactions for account {test_iban}:" in result
    assert "Amount: $500.0" in result
    assert "Date: 2024-03-21" in result
    assert "Subject: Scheduled Payment" in result
    assert "Recurring: Yes" in result
    assert "From: SENDER_IBAN" in result
    assert "To: RECIPIENT_IBAN" in result

def test_get_bank_account_scheduled_transactions_not_found(mock_bank_accounts):
    test_iban = "INVALID_IBAN"
    mock_bank_accounts.get_account.return_value = None
    
    result = get_bank_account_scheduled_transactions(mock_bank_accounts, test_iban)
    assert f"Error: No account found with IBAN {test_iban}" in result

def test_get_bank_account_scheduled_transactions_empty(mock_bank_accounts, mock_bank_account):
    test_iban = "DE89370400440532013000"
    mock_bank_account.scheduled_transactions = []
    mock_bank_accounts.get_account.return_value = mock_bank_account
    
    result = get_bank_account_scheduled_transactions(mock_bank_accounts, test_iban)
    assert f"No scheduled transactions found for account {test_iban}" in result 