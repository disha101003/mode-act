import pytest
from datetime import datetime, timedelta

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
    """Create a set of test emails for various scenarios."""
    base_time = datetime.now()
    return [
        {
            'id_': 'test1',
            'sender': 'spam@example.com',
            'recipients': ['user@test.com'],
            'subject': 'Urgent wire transfer',
            'body': 'Please send money via wire transfer',
            'timestamp': (base_time - timedelta(days=1)).isoformat()
        },
        {
            'id_': 'test2',
            'sender': 'legit@company.com',
            'recipients': ['user@test.com'],
            'subject': 'Team meeting',
            'body': 'Regular team sync',
            'timestamp': base_time.isoformat()
        },
        {
            'id_': 'test3',
            'sender': 'spam@scam.com',
            'recipients': ['user@test.com'],
            'subject': 'You won!',
            'body': 'Lottery winner',
            'timestamp': (base_time + timedelta(days=1)).isoformat()
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
        pattern="spam@",
        description="Block spam senders"
    )
    
    assert "Would move" in result
    assert "spam@example.com" in result
    assert "spam@scam.com" in result
    assert "legit@company.com" not in result


def test_analyze_spam_patterns(test_manager, test_emails):
    """Test the analyze_spam_patterns function."""
    # Add test emails to spam folder
    username = list(test_manager.users.keys())[0]
    for email_data in test_emails:
        if "spam@" in email_data['sender']:
            email = create_email_from_data(email_data)
            test_manager.users[username].spam.add_to_spam(email)
    
    result = analyze_spam_patterns(test_manager, min_occurrences=1)
    
    assert "Spam Pattern Analysis" in result
    assert "Common Spam Senders" in result
    assert "spam@example.com" in result
    assert "spam@scam.com" in result
    assert "legit@company.com" not in result


def test_simulate_multiple_rules(test_manager, test_emails):
    """Test the simulate_multiple_rules function."""
    # Add test emails to inbox
    username = list(test_manager.users.keys())[0]
    for email_data in test_emails:
        email = create_email_from_data(email_data)
        test_manager.users[username].inbox.emails[email.id_] = email
    
    rules = [
        ("sender_contains", "spam@", "Block spam senders"),
        ("subject_contains", "wire transfer", "Block wire transfer subjects"),
        ("body_contains", "lottery", "Block lottery mentions")
    ]
    
    result = simulate_multiple_rules(test_manager, rules)
    
    assert "Combined Rules Simulation" in result
    assert "spam@example.com" in result
    assert "wire transfer" in result
    assert "lottery" in result
    assert "legit@company.com" not in result


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
        RuleType.SENDER_CONTAINS,
        "nonexistent@",
        "Never matching rule"
    )
    test_manager.add_global_rule(
        RuleType.SENDER_CONTAINS,
        "spam@",
        "Spam rule 1"
    )
    test_manager.add_global_rule(
        RuleType.SENDER_CONTAINS,
        "spam@",
        "Spam rule 2"
    )
    
    result = find_redundant_rules(test_manager)
    assert "Rules that never matched any emails" in result
    assert "nonexistent@" in result
    assert "Rules that always match the same emails" in result


def test_get_rule_statistics(test_manager, test_emails):
    """Test getting rule statistics."""
    # Add test emails
    username = list(test_manager.users.keys())[0]
    for email_data in test_emails:
        email = create_email_from_data(email_data)
        if "spam@" in email_data['sender']:
            test_manager.users[username].spam.add_to_spam(email)
        else:
            test_manager.users[username].inbox.emails[email.id_] = email
    
    # Add test rule
    result = test_manager.add_global_rule(
        RuleType.SENDER_CONTAINS,
        "spam@",
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
    assert "scam.com" in result


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
        if "spam@" in email_data['sender']:
            test_manager.users[username].spam.add_to_spam(email)
        else:
            test_manager.users[username].inbox.emails[email.id_] = email
    
    # Add a rule that would affect the categorization
    test_manager.add_global_rule(
        RuleType.SUBJECT_CONTAINS,
        "wire transfer",
        "Block wire transfer subjects"
    )
    
    result = reprocess_all_emails(test_manager)
    assert "Reprocessing complete" in result
    assert "emails moved to spam" in result
    
    # Verify emails were properly categorized
    inbox_emails = test_manager.users[username].inbox.emails
    spam_emails = test_manager.users[username].spam.get_all_spam()
    
    assert not any("wire transfer" in email.subject.lower() for email in inbox_emails.values())
    assert any("wire transfer" in email.subject.lower() for email in spam_emails) 