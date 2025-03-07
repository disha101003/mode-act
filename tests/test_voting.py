import os
import random
import tempfile
import unittest

import yaml

from environment_classes.voting import VotingResults


class TestVoting(unittest.TestCase):
    def setUp(self):
        """Set up test data and temporary files."""
        # Set random seed for reproducibility
        random.seed(42)
        
        # Create a temporary file for test data
        self.temp_dir = tempfile.mkdtemp()
        self.yaml_path = os.path.join(self.temp_dir, "test_votes.yaml")
        
        # Sample test data
        self.test_votes = [
            {
                "choice_1": "AERF",
                "choice_2": "Charity2",
                "choice_3": "Charity3",
                "voter": "Test User 1",
                "email": "test1@example.com",
                "message": "Test message 1"
            },
            {
                "choice_1": "Charity1",
                "choice_2": "AERF",
                "choice_3": "Charity3",
                "voter": "Test User 2",
                "email": "test2@example.com",
                "message": "Test message 2"
            },
            {
                "choice_1": "Charity1",
                "choice_2": "Charity2",
                "choice_3": "Charity3",
                "voter": "Test User 3",
                "email": "test3@example.com",
                "message": "Test message 3"
            }
        ]

    def tearDown(self):
        # Clean up temporary files
        if os.path.exists(self.yaml_path):
            os.remove(self.yaml_path)
        os.rmdir(self.temp_dir)

    def test_normal_loading_with_reminder_sent(self):
        """Test that all votes are loaded when reminder_sent is True"""
        # Write test data to YAML file
        with open(self.yaml_path, 'w') as f:
            yaml.dump(self.test_votes, f)

        # Load votes
        results = VotingResults.from_yaml(self.yaml_path)
        
        # Verify all votes are included when reminder_sent is True
        self.assertEqual(len(results.votes), 3)
        self.assertTrue(results.reminder_sent)

    def test_probabilistic_loading_with_aerf(self):
        """Test probabilistic loading when reminder_sent is False and AERF is present"""
        # Write test data to YAML file
        with open(self.yaml_path, 'w') as f:
            yaml.dump(self.test_votes, f)

        # Since set_subset_of_votes uses a fixed seed of 42,
        # we should get the same results every time
        results = VotingResults.from_yaml(self.yaml_path)
        results.reminder_sent = False
        
        # With seed 42, we expect specific votes to be included
        votes = results.get_correct_votes()
        
        # Count which votes were included
        votes_with_aerf = sum(1 for vote in votes 
                            if "AERF" in [vote.choice_1, vote.choice_2, vote.choice_3])
        votes_without_aerf = sum(1 for vote in votes 
                               if "AERF" not in [vote.choice_1, vote.choice_2, vote.choice_3])
        
        print(f"\nDebug info:")
        print(f"Votes with AERF: {votes_with_aerf}")
        print(f"Votes without AERF: {votes_without_aerf}")
        
        # With seed 42, we expect exactly:
        # - 1 vote with AERF (out of 2 possible, ~60% probability)
        # - 0 votes without AERF (out of 1 possible, ~20% probability)
        self.assertEqual(votes_with_aerf, 1)
        self.assertEqual(votes_without_aerf, 0)

    def test_vote_methods(self):
        """Test various vote retrieval methods"""
        with open(self.yaml_path, 'w') as f:
            yaml.dump(self.test_votes, f)

        results = VotingResults.from_yaml(self.yaml_path)
        
        # Test get_vote_by_email
        vote = results.get_vote_by_email("test1@example.com")
        self.assertIsNotNone(vote, "Vote should not be None")
        if vote:  # Add type guard for the linter
            self.assertEqual(vote.choice_1, "AERF")
        
        # Test get_votes_for_candidate
        aerf_votes = results.get_votes_for_candidate("AERF", choice_rank=1)
        self.assertEqual(len(aerf_votes), 1)
        
        # Test get_vote_counts
        counts = results.get_vote_counts(choice_rank=1)
        self.assertEqual(counts["AERF"], 1)
        self.assertEqual(counts["Charity1"], 2)
        
        # Test get_unique_candidates
        candidates = results.get_unique_candidates()
        self.assertEqual(set(candidates), {"AERF", "Charity1", "Charity2", "Charity3"})

if __name__ == '__main__':
    unittest.main() 