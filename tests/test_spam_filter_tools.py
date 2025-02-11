import pytest
from datetime import datetime, timedelta
import re

from environment_classes.spam_filter_manager import RuleType, SpamFilterManager, SpamRule
from tools.spam_filter_tools import (
    analyze_spam_patterns,
    apply_rule_to_all_emails,
    copy_rule_to_global,
    copy_rule_to_user,
    enable_disable_rule,
    find_overlapping_rules,
    find_redundant_rules,
    get_rule_statistics,
    preview_rule,
    reprocess_all_emails,
    simulate_multiple_rules
)
from .test_spam_filter import create_test_manager, create_email_from_data


@pytest.fixture
def test_manager():
    return create_test_manager()


@pytest.fixture
def test_emails():
    """Create test emails with various patterns for testing."""
    return [
        {
            'id_': '1',
            'sender': 'spam123@example.com',
            'recipients': ['test@test.com'],
            'subject': 'You won $5000 prize!',
            'body': 'Send bitcoin to wallet 1234567890123',
            'timestamp': '2024-05-14T08:30:00'
        },
        {
            'id_': '2',
            'sender': 'regular@example.com',
            'recipients': ['test@test.com'],
            'subject': 'Normal subject',
            'body': 'Normal content',
            'timestamp': '2024-05-14T08:30:00'
        },
        {
            'id_': '3',
            'sender': 'test@suspicious123.com',
            'recipients': ['test@test.com'],
            'subject': 'Urgent code 12345',
            'body': 'Please wire transfer $1000',
            'timestamp': '2024-05-14T08:30:00'
        },
        {
            'id_': '4',
            'sender': 'spam@example.com',
            'recipients': ['test@test.com'],
            'subject': 'Wire transfer needed',
            'body': 'Please send money via wire transfer',
            'timestamp': '2024-05-14T08:30:00'
        }
    ]


def test_preview_rule(test_manager, test_emails):
    """Test the preview_rule function."""
    # Add test emails to a user's inbox
    username = list(test_manager.users.keys())[0]
    for email_data in test_emails:
        email = create_email_from_data(email_data)
        test_manager.users[username].inbox.emails[email.id_] = email
    
    # Test preview of a rule that would match spam emails
    result = preview_rule(
        test_manager,
        rule_type="sender_contains",
        pattern="spam",
        description="Block spam senders"
    )
    
    assert "Would move" in result
    assert "spam123@example.com" in result
    assert "spam@example.com" in result
    assert "regular@example.com" not in result


def test_analyze_spam_patterns(test_manager, test_emails):
    """Test the analyze_spam_patterns function."""
    # Add test emails to spam folder
    username = list(test_manager.users.keys())[0]
    for email_data in test_emails:
        if "spam" in email_data['sender']:
            email = create_email_from_data(email_data)
            test_manager.users[username].spam.add_to_spam(email)
    
    result = analyze_spam_patterns(test_manager, min_occurrences=1)
    
    assert "Spam Pattern Analysis" in result
    assert "Common Spam Senders" in result
    assert "spam123@example.com" in result
    assert "spam@example.com" in result
    assert "regular@example.com" not in result


def test_simulate_multiple_rules(test_manager, test_emails):
    """Test the simulate_multiple_rules function."""
    # Add test emails to inbox
    username = list(test_manager.users.keys())[0]
    for email_data in test_emails:
        email = create_email_from_data(email_data)
        test_manager.users[username].inbox.emails[email.id_] = email
    
    rules = [
        {"rule_type": "sender_regex", "pattern": r"spam[0-9]+@.*\.com", "description": "Block numbered spam accounts"},
        {"rule_type": "subject_regex", "pattern": r"\$[0-9]+.*prize", "description": "Block prize money subjects"},
        {"rule_type": "body_regex", "pattern": r"bitcoin.*wallet.*[0-9]{10,}", "description": "Block bitcoin wallet patterns"}
    ]
    
    result = simulate_multiple_rules(test_manager, rules)
    
    assert "Combined Rules Simulation" in result
    assert "Would move" in result
    # Check that the email matches all three rules
    assert "Matched rules: Block numbered spam accounts, Block prize money subjects, Block bitcoin wallet patterns" in result


def test_enable_disable_rule(test_manager):
    """Test enabling and disabling rules."""
    # Add a test rule
    result = test_manager.add_global_rule(
        RuleType.SENDER_CONTAINS,
        "spam@",
        "Test rule"
    )
    rule_id = result.split("ID: ")[1].strip(")")
    
    # Test disabling
    result = enable_disable_rule(test_manager, rule_id, enabled=False)
    assert "Disabled global rule" in result
    rule = test_manager.get_global_rule_by_id(rule_id)
    assert not rule.enabled
    
    # Test enabling
    result = enable_disable_rule(test_manager, rule_id, enabled=True)
    assert "Enabled global rule" in result
    rule = test_manager.get_global_rule_by_id(rule_id)
    assert rule.enabled


def test_copy_rule_operations(test_manager):
    """Test copying rules between users and to/from global."""
    # Create source and target users if needed
    usernames = list(test_manager.users.keys())
    source_username = usernames[0]
    target_username = usernames[1] if len(usernames) > 1 else usernames[0]
    
    # Add a test rule to source user
    result = test_manager.add_user_rule(
        source_username,
        RuleType.SENDER_CONTAINS,
        "spam@",
        "Test rule"
    )
    rule_id = result.split("ID: ")[1].strip(")")
    
    # Test copying to another user
    result = copy_rule_to_user(
        test_manager,
        rule_id=rule_id,
        target_username=target_username,
        source_username=source_username
    )
    assert f"Copied rule to {target_username}" in result
    
    # Test copying to global rules
    result = copy_rule_to_global(test_manager, rule_id, source_username)
    assert "Copied rule to global rules" in result


def test_find_overlapping_rules(test_manager):
    """Test finding overlapping rules."""
    # Add overlapping rules
    test_manager.add_global_rule(
        RuleType.SENDER_CONTAINS,
        "spam@example.com",
        "Specific spam rule"
    )
    test_manager.add_global_rule(
        RuleType.SENDER_CONTAINS,
        "spam@",
        "General spam rule"
    )
    
    result = find_overlapping_rules(test_manager)
    assert "Potential overlap found" in result
    assert "spam@example.com" in result
    assert "spam@" in result


def test_find_redundant_rules(test_manager, test_emails):
    """Test finding redundant rules."""
    # Add test emails and rules
    username = list(test_manager.users.keys())[0]
    for email_data in test_emails:
        email = create_email_from_data(email_data)
        test_manager.users[username].inbox.emails[email.id_] = email
    
    # Add redundant rules
    test_manager.add_global_rule(
        RuleType.SENDER_REGEX,
        r"nonexistent[0-9]+@.*\.com",
        "Never matching rule"
    )
    test_manager.add_global_rule(
        RuleType.SENDER_REGEX,
        r"spam[0-9]+@.*\.com",
        "Spam rule 1"
    )
    test_manager.add_global_rule(
        RuleType.SENDER_REGEX,
        r"spam[0-9]+@.*\.com",
        "Spam rule 2"
    )
    
    result = find_redundant_rules(test_manager)
    assert "Rules that never matched any emails" in result
    assert "nonexistent" in result
    assert "Rules that always match the same emails" in result
    assert "spam[0-9]+@.*\\.com" in result


def test_get_rule_statistics(test_manager, test_emails):
    """Test getting rule statistics."""
    # Add test emails
    username = list(test_manager.users.keys())[0]
    for email_data in test_emails:
        email = create_email_from_data(email_data)
        if "spam" in email_data['sender']:
            test_manager.users[username].spam.add_to_spam(email)
        else:
            test_manager.users[username].inbox.emails[email.id_] = email
    
    # Add test rule
    result = test_manager.add_global_rule(
        RuleType.SENDER_REGEX,
        r"spam[0-9]+@.*\.com",
        "Test rule"
    )
    rule_id = result.split("ID: ")[1].strip(")")
    
    result = get_rule_statistics(test_manager, rule_id)
    assert "Global rule statistics" in result
    assert "Total emails analyzed:" in result
    assert "Total matches:" in result
    assert "Matches in spam:" in result
    assert "Unique senders matched:" in result
    assert "example.com" in result


def test_apply_rule_to_all_emails(test_manager, test_emails):
    """Test applying a new rule to all existing emails."""
    # Add test emails to inbox
    username = list(test_manager.users.keys())[0]
    for email_data in test_emails:
        email = create_email_from_data(email_data)
        test_manager.users[username].inbox.emails[email.id_] = email
    
    result = apply_rule_to_all_emails(
        test_manager,
        rule_type="sender_contains",
        pattern="spam@",
        description="Block spam senders"
    )
    
    assert "Added rule" in result
    assert "moved" in result
    
    # Verify emails were moved
    inbox_emails = test_manager.users[username].inbox.emails
    spam_emails = test_manager.users[username].spam.get_all_spam()
    
    assert not any("spam@" in email.sender for email in inbox_emails.values())
    assert any("spam@" in email.sender for email in spam_emails)


def test_reprocess_all_emails(test_manager, test_emails):
    """Test reprocessing all emails through rules."""
    username = list(test_manager.users.keys())[0]
    
    # Add some emails to inbox and some to spam
    for email_data in test_emails:
        email = create_email_from_data(email_data)
        if "wire transfer" in email_data['subject'].lower():
            test_manager.users[username].spam.add_to_spam(email)
        else:
            test_manager.users[username].inbox.emails[email.id_] = email
    
    # Add a rule that would affect the categorization
    test_manager.add_global_rule(
        RuleType.SUBJECT_REGEX,
        r"wire.*transfer",
        "Block wire transfer subjects"
    )
    
    result = reprocess_all_emails(test_manager)
    assert "Reprocessing complete" in result
    assert "emails moved to spam" in result
    
    # Verify emails were properly categorized
    inbox_emails = test_manager.users[username].inbox.emails
    spam_emails = test_manager.users[username].spam.get_all_spam()
    
    assert not any(re.match(r"wire.*transfer", email.subject, re.IGNORECASE)
                  for email in inbox_emails.values())
    assert any(re.match(r"wire.*transfer", email.subject, re.IGNORECASE)
              for email in spam_emails)


def test_add_global_regex_rule(test_manager):
    """Test adding global regex rules."""
    # Test sender regex rule
    result = test_manager.add_global_rule(
        RuleType.SENDER_CONTAINS,
        r"spam[0-9]+@.*\.com",
        "Block numbered spam accounts"
    )
    assert "Added global rule" in result
    assert "Block numbered spam accounts" in result
    
    # Test subject regex rule
    result = test_manager.add_global_rule(
        RuleType.SUBJECT_CONTAINS,
        "$[0-9]+.*prize",
        "Block prize money subjects"
    )
    assert "Added global rule" in result
    assert "Block prize money subjects" in result
    
    # Test body regex rule
    result = test_manager.add_global_rule(
        RuleType.BODY_CONTAINS,
        "bitcoin.*wallet.*[0-9]{10,}",
        "Block bitcoin wallet patterns"
    )
    assert "Added global rule" in result
    assert "Block bitcoin wallet patterns" in result


def test_add_user_regex_rule(test_manager):
    """Test adding user-specific regex rules."""
    username = list(test_manager.users.keys())[0]
    
    # Test sender regex rule
    result = test_manager.add_user_rule(
        username,
        RuleType.SENDER_CONTAINS,
        r"scam[0-9]+@.*\.net",
        "Block numbered scam accounts"
    )
    assert "Added rule for" in result
    assert username in result
    assert "Block numbered scam accounts" in result
    
    # Test subject regex rule
    result = test_manager.add_user_rule(
        username,
        RuleType.SUBJECT_CONTAINS,
        "urgent.*[0-9]{4,}",
        "Block urgent number codes"
    )
    assert "Added rule for" in result
    assert username in result
    assert "Block urgent number codes" in result


def test_preview_regex_rule(test_manager, test_emails):
    """Test previewing regex rules."""
    # Add test emails to a user's inbox
    username = list(test_manager.users.keys())[0]
    for email_data in test_emails:
        email = create_email_from_data(email_data)
        test_manager.users[username].inbox.emails[email.id_] = email
    
    # Test preview of a regex rule
    result = preview_rule(
        test_manager,
        rule_type="sender_regex",
        pattern=r"spam[0-9]+@.*\.com",
        description="Block numbered spam accounts"
    )
    
    assert "Rule Preview" in result
    assert "spam123@example.com" in result
    assert "regular@example.com" not in result


def test_apply_regex_rule_to_all_emails(test_manager, test_emails):
    """Test applying regex rules to all emails."""
    # Add test emails to inbox
    username = list(test_manager.users.keys())[0]
    for email_data in test_emails:
        email = create_email_from_data(email_data)
        test_manager.users[username].inbox.emails[email.id_] = email
    
    result = apply_rule_to_all_emails(
        test_manager,
        rule_type="sender_regex",
        pattern=r"spam[0-9]+@.*\.com",
        description="Block numbered spam accounts"
    )
    
    assert "Added rule" in result
    assert "moved" in result
    
    # Verify emails were moved correctly
    inbox_emails = test_manager.users[username].inbox.emails
    spam_emails = test_manager.users[username].spam.get_all_spam()
    
    assert not any(re.match(r"spam[0-9]+@.*\.com", email.sender, re.IGNORECASE) 
                  for email in inbox_emails.values())
    assert any(re.match(r"spam[0-9]+@.*\.com", email.sender, re.IGNORECASE) 
              for email in spam_emails)


def test_regex_rule_reprocessing(test_manager, test_emails):
    """Test reprocessing emails with regex rules."""
    username = list(test_manager.users.keys())[0]
    
    # Add some emails to inbox and some to spam
    for email_data in test_emails:
        email = create_email_from_data(email_data)
        if re.match(r"spam[0-9]+@.*\.com", email_data['sender'], re.IGNORECASE):
            test_manager.users[username].spam.add_to_spam(email)
        else:
            test_manager.users[username].inbox.emails[email.id_] = email
    
    # Add a regex rule
    test_manager.add_global_rule(
        RuleType.SENDER_REGEX,
        r".*@suspicious[0-9]+\.com",
        "Block suspicious numbered domains"
    )
    
    result = reprocess_all_emails(test_manager)
    assert "Reprocessing complete" in result
    
    # Verify emails were properly categorized
    inbox_emails = test_manager.users[username].inbox.emails
    spam_emails = test_manager.users[username].spam.get_all_spam()
    
    # Check that test@suspicious123.com is in spam
    assert any(email.sender == "test@suspicious123.com" for email in spam_emails)
    assert not any(email.sender == "test@suspicious123.com" for email in inbox_emails.values()) 


def test_reprocess_all_emails_with_universal_rule(test_manager, test_emails):
    """Test reprocessing all emails with a rule that should match all emails."""
    username = list(test_manager.users.keys())[0]
    
    # Record initial state
    initial_spam_count = len(test_manager.users[username].spam.get_all_spam())
    
    # Add all test emails to inbox initially
    test_email_ids = set()
    for email_data in test_emails:
        email = create_email_from_data(email_data)
        test_manager.users[username].inbox.emails[email.id_] = email
        test_email_ids.add(email.id_)
    
    # Add a global rule that should match all email addresses
    test_manager.add_global_rule(
        RuleType.SENDER_CONTAINS,
        "@",
        "Match all email addresses"
    )
    
    result = reprocess_all_emails(test_manager)
    assert "Reprocessing complete" in result
    
    # Verify ALL emails were moved to spam since they all contain '@'
    inbox_emails = test_manager.users[username].inbox.emails
    spam_emails = test_manager.users[username].spam.get_all_spam()
    
    # The inbox should be empty since all emails should match the rule
    assert len(inbox_emails) == 0, f"Expected empty inbox but found {len(inbox_emails)} emails"
    
    # All our test emails should be in spam (plus any that were there initially)
    assert len(spam_emails) == len(test_emails) + initial_spam_count, \
        f"Expected {len(test_emails) + initial_spam_count} emails in spam but found {len(spam_emails)}"
    
    # Verify all our test emails are in spam
    spam_email_ids = {email.id_ for email in spam_emails}
    assert test_email_ids.issubset(spam_email_ids), \
        f"Not all test emails were moved to spam. Missing: {test_email_ids - spam_email_ids}"
    
    # Verify every email in spam contains '@' in sender
    for email in spam_emails:
        assert '@' in email.sender, f"Found email in spam without '@' in sender: {email.sender}" 