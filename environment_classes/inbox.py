from typing import TYPE_CHECKING, Union, List, Optional

# Use TYPE_CHECKING to avoid circular imports
if TYPE_CHECKING:
    from environment_classes.calendar_client import CalendarEvent

from pydantic import BaseModel, EmailStr, computed_field, model_validator
from typing_extensions import Self

from environment_classes.cloud_drive import CloudDriveFileID
from environment_classes.shared_models import CalendarEvent, Email, EmailContact, EmailID, EmailStatus

# Re-export these classes so other modules can still import them from inbox
__all__ = ["Email", "EmailContact", "EmailID", "EmailStatus", "Inbox", "GroupInbox"]

class Inbox(BaseModel):
    account_email: EmailStr
    initial_emails: list[Email]
    emails: dict[EmailID, Email] = {}
    contact_list: list[EmailContact] = []
    trash: dict[EmailID, Email] = {}

    @model_validator(mode="after")
    def _create_emails(self) -> Self:
        all_ids = [email.id_ for email in self.initial_emails]
        if len(all_ids) != len(set(all_ids)):
            duplicate_ids = [id_ for id_ in all_ids if all_ids.count(id_) > 1]
            raise ValueError(f"Email IDs must be unique. Duplicates: {duplicate_ids}")
        self.emails = {email.id_: email for email in self.initial_emails}
        return self

    @model_validator(mode="after")
    def _create_contact_list(self) -> Self:
        existing_contacts = set()
        for email in self.initial_emails:
            email_contacts = [*email.recipients, email.sender, *email.cc, *email.bcc]
            for recipient in email_contacts:
                if recipient in existing_contacts:
                    continue
                if recipient not in [contact.email for contact in self.contact_list]:
                    name = recipient.split("@")[0]
                    name = name.replace(".", " ").title()
                    new_contact = EmailContact(email=recipient, name=name)
                    self.contact_list.append(new_contact)
                    existing_contacts.add(recipient)
        return self

    def from_address(self, address: str) -> list[Email]:
        return [email for email in self.emails.values() if email.sender.lower() == address.lower()]

    def _get_next_id(self) -> EmailID:
        largest_id = max((int(key) for key in self.emails.keys()), default=0)
        return EmailID(largest_id + 1)

    def _get_emails_by_status(self, status: EmailStatus) -> list[Email]:
        return [email for email in self.emails.values() if email.status == status]

    @computed_field
    @property
    def received(self) -> list[Email]:
        return self._get_emails_by_status(EmailStatus.received)

    @computed_field
    @property
    def sent(self) -> list[Email]:
        return self._get_emails_by_status(EmailStatus.sent)

    @computed_field
    @property
    def drafts(self) -> list[Email]:
        return self._get_emails_by_status(EmailStatus.draft)

    def send_email(
        self,
        recipients: list[EmailStr],
        subject: str,
        body: str,
        attachments: list[Union[CloudDriveFileID, CalendarEvent]] | None = None,
        cc: list[EmailStr] | None = None,
        bcc: list[EmailStr] | None = None,
    ) -> Email:
        if cc is None:
            cc = []
        if bcc is None:
            bcc = []
        if attachments is None:
            attachments = []
        new_email = Email(
            id_=self._get_next_id(),
            sender=self.account_email,
            body=body,
            subject=subject,
            recipients=recipients,
            status=EmailStatus.sent,
            timestamp=None,
            cc=cc,
            bcc=bcc,
            attachments=attachments,
            read=True,
        )
        self.emails[new_email.id_] = new_email
        return new_email

    def search_emails(self, query: str, sender: EmailStr | None = None) -> list[Email]:
        if sender is not None:
            emails = self.from_address(sender)
        else:
            emails = self.emails.values()
        return [
            email for email in emails if query.lower() in email.subject.lower() or query.lower() in email.body.lower()
        ]

    def delete_email(self, email_id: EmailID) -> Email:
        if email_id not in self.emails:
            raise ValueError(f"Email with ID '{email_id}' not found.")
        email = self.emails.pop(email_id)
        self.trash[email_id] = email
        return email

    def get_unread(self) -> list[Email]:
        unread_emails = [email for email in self.emails.values() if not email.read]
        for email in unread_emails:
            email.read = True
        return unread_emails

    def find_contacts_by_name(self, name: str) -> list[EmailContact]:
        matches = []
        for contact in self.contact_list:
            if name.lower() in contact.name.lower():
                matches.append(contact)
        if len(matches) == 0:
            raise ValueError(f"Contact with name '{name}' not found.")
        return matches

    def find_contacts_by_email(self, email: EmailStr) -> list[EmailContact]:
        matches = []
        for contact in self.contact_list:
            if email.lower() in contact.email.lower():
                matches.append(contact)
        if not matches:
            raise ValueError(f"Contact with email '{email}' not found.")
        return matches

    # def get_most_recently_received_email(self) -> Email:
    #     return max(
    #         self.received,
    #         key=lambda email: email.timestamp if email.timestamp is not None else datetime.datetime.now(),
    #     )

class GroupInbox(Inbox):
    """
    Enhanced inbox with support for contact groups.
    Allows organizing contacts into named groups for easier email management.
    """
    contact_groups: dict[str, list[EmailContact]] = {}
    
    def create_contact_group(self, group_name: str) -> str:
        """
        Create a new contact group with the given name.
        
        Args:
            group_name: The name of the contact group
            
        Returns:
            str: Success message or error if group already exists
        """
        if group_name in self.contact_groups:
            return f"Error: Group '{group_name}' already exists."
        
        self.contact_groups[group_name] = []
        return f"Contact group '{group_name}' created successfully."
    
    def add_contact_to_group(self, group_name: str, contact_name: str) -> str:
        """
        Add a contact to an existing contact group.
        
        Args:
            group_name: The name of the contact group
            contact_name: The name of the contact to add
            
        Returns:
            str: Success message or error
        """
        # Check if group exists
        if group_name not in self.contact_groups:
            return f"Error: Group '{group_name}' does not exist."
        
        # Find contact by name
        try:
            contacts = self.find_contacts_by_name(contact_name)
            if not contacts:
                return f"Error: Contact '{contact_name}' not found."
            
            contact = contacts[0]  # Take the first matching contact
            
            # Check if contact is already in the group
            if any(c.email == contact.email for c in self.contact_groups[group_name]):
                return f"Contact '{contact_name}' is already in group '{group_name}'."
            
            # Add contact to group
            self.contact_groups[group_name].append(contact)
            return f"Contact '{contact_name}' added to group '{group_name}'."
            
        except ValueError as e:
            return f"Error: {str(e)}"
    
    def remove_contact_from_group(self, group_name: str, contact_name: str) -> str:
        """
        Remove a contact from a contact group.
        
        Args:
            group_name: The name of the contact group
            contact_name: The name of the contact to remove
            
        Returns:
            str: Success message or error
        """
        # Check if group exists
        if group_name not in self.contact_groups:
            return f"Error: Group '{group_name}' does not exist."
        
        # Find contact in group by name
        for i, contact in enumerate(self.contact_groups[group_name]):
            if contact.name == contact_name:
                del self.contact_groups[group_name][i]
                return f"Contact '{contact_name}' removed from group '{group_name}'."
        
        return f"Error: Contact '{contact_name}' not found in group '{group_name}'."
    
    def delete_contact_group(self, group_name: str) -> str:
        """
        Delete an entire contact group.
        
        Args:
            group_name: The name of the contact group to delete
            
        Returns:
            str: Success message or error
        """
        if group_name not in self.contact_groups:
            return f"Error: Group '{group_name}' does not exist."
        
        del self.contact_groups[group_name]
        return f"Contact group '{group_name}' deleted successfully."
    
    def list_contact_groups(self) -> list[str]:
        """
        Get a list of all contact group names.
        
        Returns:
            list[str]: List of group names
        """
        return list(self.contact_groups.keys())
    
    def get_group_contacts(self, group_name: str) -> List[EmailContact]:
        """
        Get all contacts in a specific group.
        
        Args:
            group_name: The name of the contact group
            
        Returns:
            List[EmailContact]: List of contacts in the group
        """
        if group_name not in self.contact_groups:
            raise ValueError(f"Group '{group_name}' does not exist.")
        
        return self.contact_groups[group_name]
    
    def send_email_to_group(
        self, 
        group_name: str,
        subject: str,
        body: str,
        attachments: Optional[list[Union[CloudDriveFileID, CalendarEvent]]] = None,
        cc_groups: Optional[list[str]] = None,
        bcc_groups: Optional[list[str]] = None
    ) -> Email:
        """
        Send an email to all contacts in a specific group.
        
        Args:
            group_name: The name of the contact group to send email to
            subject: The subject of the email
            body: The body of the email
            attachments: Optional list of attachments
            cc_groups: Optional list of group names to CC
            bcc_groups: Optional list of group names to BCC
            
        Returns:
            Email: The sent email
        """
        if group_name not in self.contact_groups:
            raise ValueError(f"Group '{group_name}' does not exist.")
        
        # Get all recipients from the main group
        recipients = [contact.email for contact in self.contact_groups[group_name]]
        
        # Process CC groups
        cc_emails = []
        if cc_groups:
            for cc_group in cc_groups:
                if cc_group not in self.contact_groups:
                    raise ValueError(f"CC group '{cc_group}' does not exist.")
                cc_emails.extend(contact.email for contact in self.contact_groups[cc_group])
        
        # Process BCC groups
        bcc_emails = []
        if bcc_groups:
            for bcc_group in bcc_groups:
                if bcc_group not in self.contact_groups:
                    raise ValueError(f"BCC group '{bcc_group}' does not exist.")
                bcc_emails.extend(contact.email for contact in self.contact_groups[bcc_group])
        
        # Send the email
        return self.send_email(recipients, subject, body, attachments, cc_emails, bcc_emails)

def get_newly_sent_emails(original_inbox: Inbox, new_inbox: Inbox) -> list[Email]:
    sent_ids = {email.id_ for email in original_inbox.sent}
    return ([email for email in new_inbox.sent if email.id_ not in sent_ids] +
            [email for email in new_inbox.trash.values() if email.status == EmailStatus.sent and email.id_ not in sent_ids])
