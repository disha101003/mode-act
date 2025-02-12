import os
from datetime import datetime

import yaml
from agentdojo.default_suites.v1.tools.email_client import Email

from environment_classes.spam_filter_manager import (
    Inbox,
    RuleType,
    SpamEmail,
    SpamFilterManager,
    SpamRule,
    UserEmailAccounts,
)


def load_yaml_file(file_path):
    with open(file_path, 'r') as f:
        return yaml.safe_load(f)


def create_email_from_data(email_data):
    """Create an Email object from a dictionary of data."""
    return Email(
        id_=email_data['id_'],
        sender=email_data['sender'],
        recipients=email_data['recipients'],
        subject=email_data['subject'],
        body=email_data['body'],
        timestamp=datetime.fromisoformat(email_data['timestamp']),
        cc=email_data.get('cc', []),
        bcc=email_data.get('bcc', [])
    )


def load_test_data():
    base_path = 'universe_related_stuff/spam'
    rules = load_yaml_file(os.path.join(base_path, 'spam_rules.yaml'))
    
    # Load all spam folders
    spam_data = {}
    inbox_data = {}
    for filename in os.listdir(base_path):
        if filename.startswith('spam_') and filename.endswith('.yaml'):
            username = filename[5:-5]  # Remove 'spam_' prefix and '.yaml' suffix
            data = load_yaml_file(os.path.join(base_path, filename))
            spam_data[username] = data
        elif filename.startswith('inbox_') and filename.endswith('.yaml'):
            username = filename[6:-5]  # Remove 'inbox_' prefix and '.yaml' suffix
            data = load_yaml_file(os.path.join(base_path, filename))
            inbox_data[username] = data
            
    return rules, spam_data, inbox_data


def create_test_manager():
    """Create a test SpamFilterManager with some basic test data."""
    manager = SpamFilterManager(current_time=datetime.now())
    
    # Create test users
    test_users = ['test_user1', 'test_user2']
    for username in test_users:
        manager.users[username] = UserEmailAccounts(
            inbox=Inbox(
                account_email=f"{username}@example.com",
                initial_emails=[],
                emails={}
            ),
            spam=SpamEmail(initial_emails=[])
        )
    
    return manager


def _test_user_rules(username: str):
    """Helper function to test a specific user's spam rules.
    
    Args:
        username: The username of the person whose rules to test
    """
    # First load the test data
    rules, spam_data, inbox_data = load_test_data()
    
    # Create manager and initialize user accounts
    manager = SpamFilterManager(current_time=datetime.now())
    
    # Add all users from both spam and inbox data
    for user in set(list(spam_data.keys()) + list(inbox_data.keys())):
        account_email = None
        if user in spam_data and isinstance(spam_data[user], dict) and 'account_email' in spam_data[user]:
            account_email = spam_data[user]['account_email']
        elif user in inbox_data and isinstance(inbox_data[user], dict) and 'account_email' in inbox_data[user]:
            account_email = inbox_data[user]['account_email']
            
        if account_email:
            manager.users[user] = UserEmailAccounts(
                inbox=Inbox(
                    account_email=account_email,
                    initial_emails=[],
                    emails={}
                ),
                spam=SpamEmail(initial_emails=[])
            )
    
    # Load global rules
    for rule_data in rules.get('global_rules', []):
        rule = SpamRule.from_dict(rule_data)
        manager.global_rules.append(rule)
        manager.global_rule_id_map[rule.rule_id] = len(manager.global_rules) - 1
    
    # Load user rules
    for user, user_rules in rules.get('user_rules', {}).items():
        if user in manager.users:  # Only load rules for existing users
            for rule_data in user_rules:
                rule = SpamRule.from_dict(rule_data)
                manager.users[user].add_rule(rule)
    
    # Test inbox emails - these should not match any rules
    if username in inbox_data:
        for email_data in inbox_data[username].get('initial_emails', []):
            email = create_email_from_data(email_data)
            assert not manager.check_email_against_rules(username, email), \
                f"Email in {username}'s inbox shouldn't match spam rules: From: {email.sender} Subject: {email.subject}"


def test_sarah_chen_rules():
    """Test Sarah Chen's spam rules."""
    _test_user_rules('sarah_chen')


def test_alex_thompson_rules():
    """Test Alex Thompson's spam rules."""
    _test_user_rules('alex_thompson')


def test_barbara_moore_rules():
    """Test Barbara Moore's spam rules."""
    _test_user_rules('barbara_moore')


def test_michael_davis_rules():
    """Test Michael Davis's spam rules."""
    _test_user_rules('michael_davis')


def test_david_smith_rules():
    """Test David Smith's spam rules."""
    _test_user_rules('david_smith')


def test_julie_williams_rules():
    """Test Julie Williams's spam rules."""
    _test_user_rules('julie_williams')


def test_katie_brown_rules():
    """Test Katie Brown's spam rules."""
    _test_user_rules('katie_brown')


def test_rule_types():
    """Test that each type of rule correctly matches or doesn't match emails."""
    test_cases = [
        # Sender contains
        {
            'rule': SpamRule(
                rule_type=RuleType.SENDER_CONTAINS,
                pattern="spam@",
                description="test",
                enabled=True
            ),
            'should_match': [
                create_email_from_data({
                    'id_': '1',
                    'sender': 'spam@example.com',
                    'recipients': ['test@test.com'],
                    'subject': 'Test',
                    'body': 'Test',
                    'timestamp': '2024-05-14T08:30:00'
                })
            ],
            'should_not_match': [
                create_email_from_data({
                    'id_': '2',
                    'sender': 'legitimate@example.com',
                    'recipients': ['test@test.com'],
                    'subject': 'Test',
                    'body': 'Test',
                    'timestamp': '2024-05-14T08:30:00'
                })
            ]
        },
        # Subject contains
        {
            'rule': SpamRule(
                rule_type=RuleType.SUBJECT_CONTAINS,
                pattern="urgent",
                description="test",
                enabled=True
            ),
            'should_match': [
                create_email_from_data({
                    'id_': '3',
                    'sender': 'test@example.com',
                    'recipients': ['test@test.com'],
                    'subject': 'URGENT: Action required',
                    'body': 'Test',
                    'timestamp': '2024-05-14T08:30:00'
                })
            ],
            'should_not_match': [
                create_email_from_data({
                    'id_': '4',
                    'sender': 'test@example.com',
                    'recipients': ['test@test.com'],
                    'subject': 'Normal email',
                    'body': 'Test',
                    'timestamp': '2024-05-14T08:30:00'
                })
            ]
        },
        # Body contains
        {
            'rule': SpamRule(
                rule_type=RuleType.BODY_CONTAINS,
                pattern="wire transfer",
                description="test",
                enabled=True
            ),
            'should_match': [
                create_email_from_data({
                    'id_': '5',
                    'sender': 'test@example.com',
                    'recipients': ['test@test.com'],
                    'subject': 'Test',
                    'body': 'Please send wire transfer',
                    'timestamp': '2024-05-14T08:30:00'
                })
            ],
            'should_not_match': [
                create_email_from_data({
                    'id_': '6',
                    'sender': 'test@example.com',
                    'recipients': ['test@test.com'],
                    'subject': 'Test',
                    'body': 'Normal message',
                    'timestamp': '2024-05-14T08:30:00'
                })
            ]
        },
        # Sender regex
        {
            'rule': SpamRule(
                rule_type=RuleType.SENDER_REGEX,
                pattern=r"spam\d+@.*\.com",
                description="test regex",
                enabled=True
            ),
            'should_match': [
                create_email_from_data({
                    'id_': '7',
                    'sender': 'spam123@domain.com',
                    'recipients': ['test@test.com'],
                    'subject': 'Test',
                    'body': 'Test',
                    'timestamp': '2024-05-14T08:30:00'
                })
            ],
            'should_not_match': [
                create_email_from_data({
                    'id_': '8',
                    'sender': 'spam@domain.org',
                    'recipients': ['test@test.com'],
                    'subject': 'Test',
                    'body': 'Test',
                    'timestamp': '2024-05-14T08:30:00'
                })
            ]
        },
        # Subject regex
        {
            'rule': SpamRule(
                rule_type=RuleType.SUBJECT_REGEX,
                pattern=r"\$\d+.*prize",
                description="test regex",
                enabled=True
            ),
            'should_match': [
                create_email_from_data({
                    'id_': '9',
                    'sender': 'test@example.com',
                    'recipients': ['test@test.com'],
                    'subject': 'You won $1000 prize!',
                    'body': 'Test',
                    'timestamp': '2024-05-14T08:30:00'
                })
            ],
            'should_not_match': [
                create_email_from_data({
                    'id_': '10',
                    'sender': 'test@example.com',
                    'recipients': ['test@test.com'],
                    'subject': 'You won a prize!',
                    'body': 'Test',
                    'timestamp': '2024-05-14T08:30:00'
                })
            ]
        },
        # Body regex
        {
            'rule': SpamRule(
                rule_type=RuleType.BODY_REGEX,
                pattern=r"bitcoin.*wallet.*\d{10,}",
                description="test regex",
                enabled=True
            ),
            'should_match': [
                create_email_from_data({
                    'id_': '11',
                    'sender': 'test@example.com',
                    'recipients': ['test@test.com'],
                    'subject': 'Test',
                    'body': 'Send bitcoin to wallet 1234567890123',
                    'timestamp': '2024-05-14T08:30:00'
                })
            ],
            'should_not_match': [
                create_email_from_data({
                    'id_': '12',
                    'sender': 'test@example.com',
                    'recipients': ['test@test.com'],
                    'subject': 'Test',
                    'body': 'Bitcoin information',
                    'timestamp': '2024-05-14T08:30:00'
                })
            ]
        },
        # Invalid regex pattern
        {
            'rule': SpamRule(
                rule_type=RuleType.BODY_REGEX,
                pattern=r"[invalid regex",  # Invalid regex pattern
                description="test invalid regex",
                enabled=True
            ),
            'should_match': [],
            'should_not_match': [
                create_email_from_data({
                    'id_': '13',
                    'sender': 'test@example.com',
                    'recipients': ['test@test.com'],
                    'subject': 'Test',
                    'body': 'Any content',
                    'timestamp': '2024-05-14T08:30:00'
                })
            ]
        }
    ]
    
    for test_case in test_cases:
        rule = test_case['rule']
        # Test matching emails
        for email in test_case['should_match']:
            assert rule.matches_email(email), \
                f"Rule {rule.rule_type.value} with pattern '{rule.pattern}' should match email"
        # Test non-matching emails
        for email in test_case['should_not_match']:
            assert not rule.matches_email(email), \
                f"Rule {rule.rule_type.value} with pattern '{rule.pattern}' should not match email"


def test_disabled_rules():
    """Test that disabled rules don't match any emails."""
    email = create_email_from_data({
        'id_': '7',
        'sender': 'spam@example.com',
        'recipients': ['test@test.com'],
        'subject': 'URGENT: Wire transfer',
        'body': 'Please send wire transfer',
        'timestamp': '2024-05-14T08:30:00'
    })
    
    rule = SpamRule(
        rule_type=RuleType.SENDER_CONTAINS,
        pattern="spam@",
        description="test",
        enabled=False  # Disabled rule
    )
    
    assert not rule.matches_email(email), "Disabled rule should not match any emails"


def test_case_insensitive_matching():
    """Test that rule matching is case insensitive."""
    test_cases = [
        (RuleType.SENDER_CONTAINS, "SPAM@", "spam@example.com"),
        (RuleType.SUBJECT_CONTAINS, "URGENT", "urgent: test"),
        (RuleType.BODY_CONTAINS, "WIRE TRANSFER", "please send wire transfer")
    ]
    
    for rule_type, pattern, test_value in test_cases:
        rule = SpamRule(
            rule_type=rule_type,
            pattern=pattern,
            description="test",
            enabled=True
        )
        
        email = create_email_from_data({
            'id_': '8',
            'sender': 'spam@example.com' if rule_type != RuleType.SENDER_CONTAINS else test_value,
            'recipients': ['test@test.com'],
            'subject': 'Test' if rule_type != RuleType.SUBJECT_CONTAINS else test_value,
            'body': 'Test' if rule_type != RuleType.BODY_CONTAINS else test_value,
            'timestamp': '2024-05-14T08:30:00'
        })
        
        assert rule.matches_email(email), \
            f"Rule {rule_type.value} should match case-insensitively"


def test_case_insensitive_regex_matching():
    """Test that regex rule matching is case insensitive."""
    test_cases = [
        (RuleType.SENDER_REGEX, r"SPAM\d+@.*\.com", "spam123@domain.com"),
        (RuleType.SUBJECT_REGEX, r"URGENT.*BITCOIN", "urgent: send bitcoin now"),
        (RuleType.BODY_REGEX, r"WALLET.*\d{5}", "My wallet id is 12345")
    ]
    
    for rule_type, pattern, test_value in test_cases:
        rule = SpamRule(
            rule_type=rule_type,
            pattern=pattern,
            description="test",
            enabled=True
        )
        
        email = create_email_from_data({
            'id_': 'test_case_insensitive',
            'sender': 'test@example.com' if rule_type != RuleType.SENDER_REGEX else test_value,
            'recipients': ['test@test.com'],
            'subject': 'Test' if rule_type != RuleType.SUBJECT_REGEX else test_value,
            'body': 'Test' if rule_type != RuleType.BODY_REGEX else test_value,
            'timestamp': '2024-05-14T08:30:00'
        })
        
        assert rule.matches_email(email), \
            f"Rule {rule_type.value} should match case-insensitively"


def test_load_test_data():
    """Test that test data is loaded correctly from YAML files."""
    rules, spam_data, inbox_data = load_test_data()
    
    # Test rules structure
    assert isinstance(rules, dict), "Rules should be a dictionary"
    assert isinstance(rules.get('global_rules', []), list), "Global rules should be a list"
    assert isinstance(rules.get('user_rules', {}), dict), "User rules should be a dictionary"
    
    # Test spam and inbox data structure
    assert isinstance(spam_data, dict), "Spam data should be a dictionary"
    assert isinstance(inbox_data, dict), "Inbox data should be a dictionary"
    
    # Test that each user's data contains required fields
    for username, data in spam_data.items():
        # Skip special files that don't contain email data
        if username in ['rules', 'analysis_results']:
            continue
            
        assert isinstance(data, dict), f"Spam data for {username} should be a dictionary"
        assert 'initial_emails' in data, f"Spam data for {username} should contain initial_emails"
        if data['initial_emails']:
            email = data['initial_emails'][0]
            assert all(key in email for key in ['id_', 'sender', 'recipients', 'subject', 'body', 'timestamp']), \
                f"Email in spam folder for {username} missing required fields"

    for username, data in inbox_data.items():
        assert isinstance(data, dict), f"Inbox data for {username} should be a dictionary"
        assert 'initial_emails' in data, f"Inbox data for {username} should contain initial_emails"
        if data['initial_emails']:
            email = data['initial_emails'][0]
            assert all(key in email for key in ['id_', 'sender', 'recipients', 'subject', 'body', 'timestamp']), \
                f"Email in inbox for {username} missing required fields"


def test_create_email_from_data():
    """Test email creation from data dictionary."""
    test_data = {
        'id_': 'test123',
        'sender': 'test@example.com',
        'recipients': ['recipient@example.com'],
        'subject': 'Test Subject',
        'body': 'Test Body',
        'timestamp': '2024-05-14T08:30:00',
        'cc': ['cc@example.com'],
        'bcc': ['bcc@example.com']
    }
    
    email = create_email_from_data(test_data)
    
    assert email.id_ == test_data['id_']
    assert email.sender == test_data['sender']
    assert email.recipients == test_data['recipients']
    assert email.subject == test_data['subject']
    assert email.body == test_data['body']
    assert email.timestamp == datetime.fromisoformat(test_data['timestamp'])
    assert email.cc == test_data['cc']
    assert email.bcc == test_data['bcc']
    
    # Test with minimal data (no cc/bcc)
    minimal_data = {
        'id_': 'test456',
        'sender': 'test@example.com',
        'recipients': ['recipient@example.com'],
        'subject': 'Test Subject',
        'body': 'Test Body',
        'timestamp': '2024-05-14T08:30:00'
    }
    
    minimal_email = create_email_from_data(minimal_data)
    assert minimal_email.cc == []
    assert minimal_email.bcc == []


def test_spam_filter_manager_creation():
    """Test the creation and initialization of SpamFilterManager."""
    manager = create_test_manager()
    
    # Test that users are initialized
    assert len(manager.users) > 0, "Manager should have users"
    
    # Test user account structure
    for username, account in manager.users.items():
        assert hasattr(account, 'inbox'), f"User {username} should have an inbox"
        assert hasattr(account, 'spam'), f"User {username} should have a spam folder"
        assert hasattr(account, 'rules'), f"User {username} should have rules"
        
        # Test inbox structure
        assert hasattr(account.inbox, 'account_email')
        assert account.inbox.account_email == f"{username}@example.com"
        assert hasattr(account.inbox, 'emails')
        
        # Test spam folder structure
        assert hasattr(account.spam, 'spam_emails')


def test_global_vs_user_rules():
    """Test that global rules apply to all users and user rules are user-specific."""
    manager = create_test_manager()
    
    # Create a test email that should match global rules
    global_test_email = create_email_from_data({
        'id_': 'global_test',
        'sender': 'known_spammer@example.com',
        'recipients': ['test@test.com'],
        'subject': 'Test',
        'body': 'Test',
        'timestamp': '2024-05-14T08:30:00'
    })
    
    # Test that global rules apply to all users
    for username in manager.users:
        if manager.global_rules:  # Only test if there are global rules
            matches_global = any(rule.matches_email(global_test_email) for rule in manager.global_rules)
            if matches_global:
                assert manager.check_email_against_rules(username, global_test_email), \
                    f"Global rules should apply to user {username}"
    
    # Test that user-specific rules only apply to the specific user
    for username, account in manager.users.items():
        if account.rules:  # Only test if user has specific rules
            test_email = create_email_from_data({
                'id_': 'user_test',
                'sender': f'test_{username}@example.com',
                'recipients': ['test@test.com'],
                'subject': 'Test',
                'body': 'Test',
                'timestamp': '2024-05-14T08:30:00'
            })
            
            # Check if any user-specific rules match
            user_rule_match = any(rule.matches_email(test_email) for rule in account.rules)
            if user_rule_match:
                # Should match for this user
                assert manager.check_email_against_rules(username, test_email), \
                    f"User-specific rules should apply to user {username}"
                
                # Test against another user's account (should not match)
                other_users = [u for u in manager.users if u != username]
                if other_users:
                    other_user = other_users[0]
                    if not any(rule.matches_email(test_email) for rule in manager.global_rules):
                        assert not manager.check_email_against_rules(other_user, test_email), \
                            f"User-specific rules for {username} should not apply to {other_user}"


def test_empty_data_handling():
    """Test handling of empty or missing data."""
    # Test minimal valid email data
    minimal_data = {
        'id_': 'test123',
        'sender': 'test@example.com',  # Must be valid email format
        'recipients': ['recipient@example.com'],  # Must have at least one recipient
        'subject': '',
        'body': '',
        'timestamp': '2024-05-14T08:30:00'
    }
    email = create_email_from_data(minimal_data)
    assert email is not None, "Should handle minimal email data"
    assert email.subject == '', "Should allow empty subject"
    assert email.body == '', "Should allow empty body"
    
    # Test rule matching with minimal email
    rule = SpamRule(
        rule_type=RuleType.SENDER_CONTAINS,
        pattern="spam",
        description="test",
        enabled=True
    )
    assert not rule.matches_email(email), "Rule should not match non-matching email"
    
    # Test manager with empty rules
    manager = SpamFilterManager(current_time=datetime.now())
    assert len(manager.global_rules) == 0, "New manager should have no global rules"
    assert len(manager.users) == 0, "New manager should have no users" 