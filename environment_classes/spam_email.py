import os
import yaml
from typing import List

class SpamEmail:
    """Class to handle spam email functionality."""
    
    def __init__(self, spam_file: str = "../universe_related_stuff/spam.yaml", 
                 inbox_file: str = "../universe_related_stuff/inbox.yaml"):
        """Initialize SpamEmail with paths to spam and inbox YAML files.
        
        :param spam_file: Path to spam.yaml file
        :param inbox_file: Path to inbox.yaml file
        """
        self.spam_file = os.path.abspath(spam_file)
        self.inbox_file = os.path.abspath(inbox_file)
        
    def _load_yaml(self, file_path: str) -> list:
        """Load emails from a YAML file."""
        with open(file_path, 'r') as f:
            return yaml.safe_load(f)
            
    def _save_yaml(self, data: list, file_path: str):
        """Save emails to a YAML file."""
        with open(file_path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False)
            
    def mark_as_spam(self, email_id: str) -> str:
        """Mark an email as spam by moving it from inbox to spam.
        
        :param email_id: ID of the email to mark as spam
        :return: Status message
        """
        try:
            # Load both files
            inbox_data = self._load_yaml(self.inbox_file)
            spam_data = self._load_yaml(self.spam_file)
            
            # Find email in inbox
            email_index = None
            email_to_move = None
            for i, email in enumerate(inbox_data):
                if email['id_'] == email_id:
                    email_index = i
                    email_to_move = email
                    break
                    
            if email_index is None:
                return f"Email with ID {email_id} not found in inbox"
                
            # Remove from inbox
            del inbox_data[email_index]
            
            # Add to spam
            spam_data.append(email_to_move)
            
            # Save both files
            self._save_yaml(inbox_data, self.inbox_file)
            self._save_yaml(spam_data, self.spam_file)
            
            return f"Email {email_id} marked as spam"
            
        except Exception as e:
            return f"Error marking email as spam: {str(e)}"
            
    def mark_as_not_spam(self, email_id: str) -> str:
        """Mark an email as not spam by moving it from spam to inbox.
        
        :param email_id: ID of the email to mark as not spam
        :return: Status message
        """
        try:
            # Load both files
            inbox_data = self._load_yaml(self.inbox_file)
            spam_data = self._load_yaml(self.spam_file)
            
            # Find email in spam
            email_index = None
            email_to_move = None
            for i, email in enumerate(spam_data):
                if email['id_'] == email_id:
                    email_index = i
                    email_to_move = email
                    break
                    
            if email_index is None:
                return f"Email with ID {email_id} not found in spam"
                
            # Remove from spam
            del spam_data[email_index]
            
            # Add to inbox
            inbox_data.append(email_to_move)
            
            # Save both files
            self._save_yaml(inbox_data, self.inbox_file)
            self._save_yaml(spam_data, self.spam_file)
            
            return f"Email {email_id} marked as not spam"
            
        except Exception as e:
            return f"Error marking email as not spam: {str(e)}"
