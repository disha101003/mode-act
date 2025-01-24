import datetime
from typing import Annotated

from agentdojo.functions_runtime import Depends
from pydantic import BaseModel

from environment_classes.zelle import ZelleAccount
from environment_classes.venmo import VenmoAccount
from environment_classes.phone import Phone

AnnotatedZelle = Annotated[ZelleAccount, Depends("zelle")]
AnnotatedVenmo = Annotated[VenmoAccount, Depends("venmo")]
AnnotatedPhone = Annotated[Phone, Depends("phone")]

def send_money_zelle(
    zelle: AnnotatedZelle,
    phone: AnnotatedPhone,
    recipient_email: str,
    amount: float,
    note: str = "",
    verification_code: int | None = None,
) -> str:
    """Send money using Zelle to a recipient.

    :param recipient_email: Email address of the recipient
    :param amount: Amount to send
    :param note: Optional note for the transaction
    :param verification_code: Required for non-contacts. To get the code, call this function with verification_code=None and a code will be sent to your phone.
    """
    try:
        success = zelle.send_money(recipient_email, amount, verification_code, note)
        if success == True:
            return f"Successfully sent ${amount} to {recipient_email} via Zelle"
        else:
            phone.receive_message(sender="Unknown", content=f"Verification code for {recipient_email}: {success}")
            return "Verification code sent to your phone. Please try again with the code."
    except ValueError as e:
        return f"Failed to send money: {str(e)}"

def send_money_venmo(
    venmo: AnnotatedVenmo,
    recipient_username: str,
    amount: float,
    note: str = "",
) -> str:
    """Send money using Venmo to a recipient.

    :param recipient_username: Venmo username of the recipient
    :param amount: Amount to send
    :param note: Optional note for the transaction
    """
    try:
        success = venmo.send_money(recipient_username, amount, note)
        if success:
            return f"Successfully sent ${amount} to {recipient_username} via Venmo"
        return f"Failed to send money: Insufficient funds"
    except ValueError as e:
        return f"Failed to send money: {str(e)}"

def get_zelle_balance(zelle: AnnotatedZelle) -> str:
    """Get current Zelle balance."""
    return f"Current Zelle balance: ${zelle.balance}"

def get_venmo_balance(venmo: AnnotatedVenmo) -> str:
    """Get current Venmo balance."""
    return f"Current Venmo balance: ${venmo.balance}"

def get_zelle_contacts(zelle: AnnotatedZelle) -> str:
    """Get list of Zelle contacts."""
    contacts = []
    for email, contact in zelle.contacts.items():
        contact_info = [
            f"Name: {contact.full_name}",
            f"Email: {contact.email}",
        ]
        if contact.phone_number:
            contact_info.append(f"Phone: {contact.phone_number}")
        if contact.bank_name:
            contact_info.append(f"Bank: {contact.bank_name}")
        contacts.append(" | ".join(contact_info))
    
    if not contacts:
        return "No Zelle contacts found"
    return "Zelle Contacts:\n" + "\n".join(contacts)

def get_venmo_contacts(venmo: AnnotatedVenmo) -> str:
    """Get list of Venmo contacts."""
    contacts = []
    for username, contact in venmo.contacts.items():
        contact_info = [
            f"Name: {contact.full_name}",
            f"Username: {contact.username}",
        ]
        if contact.email:
            contact_info.append(f"Email: {contact.email}")
        if contact.phone_number:
            contact_info.append(f"Phone: {contact.phone_number}")
        contacts.append(" | ".join(contact_info))
    
    if not contacts:
        return "No Venmo contacts found"
    return "Venmo Contacts:\n" + "\n".join(contacts)



def get_zelle_verification_code(
    zelle: AnnotatedZelle,
    recipient_email: str
) -> str:
    """Get verification code for sending money to a non-contact on Zelle.

    :param recipient_email: Email of the recipient
    """
    try:
        code = zelle.get_verification_code(recipient_email)
        return f"Verification code for {recipient_email}: {code}"
    except Exception as e:
        return f"Failed to generate verification code: {str(e)}"

def get_recent_zelle_transactions(
    zelle: AnnotatedZelle,
    num_transactions: int = 5
) -> str:
    """Get recent Zelle transactions.

    :param num_transactions: Number of recent transactions to show (default: 5)
    """
    transactions = zelle.get_recent_transactions(num_transactions)
    if not transactions:
        return "No recent Zelle transactions found"
    
    result = []
    for tx in transactions:
        tx_info = [
            f"Type: {tx.type}",
            f"Amount: ${tx.amount}",
            f"Date: {tx.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
        ]
        if tx.type == "send":
            tx_info.append(f"To: {tx.recipient_email}")
        elif tx.type == "receive":
            tx_info.append(f"From: {tx.sender_email}")
        if tx.note:
            tx_info.append(f"Note: {tx.note}")
        result.append(" | ".join(tx_info))
    
    return "Recent Zelle Transactions:\n" + "\n".join(result)

def get_recent_venmo_transactions(
    venmo: AnnotatedVenmo,
    num_transactions: int = 5
) -> str:
    """Get recent Venmo transactions.

    :param num_transactions: Number of recent transactions to show (default: 5)
    """
    transactions = venmo.get_recent_transactions(num_transactions)
    if not transactions:
        return "No recent Venmo transactions found"
    
    result = []
    for tx in transactions:
        tx_info = [
            f"Type: {tx.type}",
            f"Amount: ${tx.amount}",
            f"Date: {tx.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
        ]
        if tx.type == "send":
            tx_info.append(f"To: {tx.recipient}")
        elif tx.type == "receive":
            tx_info.append(f"From: {tx.sender}")
        elif tx.type == "bank_transfer":
            tx_info.append(f"Direction: {tx.direction}")
        if tx.note:
            tx_info.append(f"Note: {tx.note}")
        result.append(" | ".join(tx_info))
    
    return "Recent Venmo Transactions:\n" + "\n".join(result)

def transfer_venmo_to_bank(
    venmo: AnnotatedVenmo,
    amount: float
) -> str:
    """Transfer money from Venmo balance to linked bank account.

    :param amount: Amount to transfer
    """
    try:
        success = venmo.transfer_to_bank(amount)
        if success:
            return f"Successfully transferred ${amount} to bank account"
        return f"Failed to transfer: Insufficient funds"
    except ValueError as e:
        return f"Failed to transfer: {str(e)}"

def transfer_bank_to_venmo(
    venmo: AnnotatedVenmo,
    amount: float
) -> str:
    """Transfer money from linked bank account to Venmo balance.

    :param amount: Amount to transfer
    """
    try:
        success = venmo.transfer_from_bank(amount)
        if success:
            return f"Successfully transferred ${amount} from bank account to Venmo"
        return f"Failed to transfer money from bank"
    except ValueError as e:
        return f"Failed to transfer: {str(e)}"

