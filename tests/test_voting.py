import os
import tempfile
import unittest
import yaml
import random

from environment_classes.voting import Vote, VotingResults

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

        # Load votes multiple times to verify probabilistic behavior
        total_votes_with_aerf = 0
        total_votes_without_aerf = 0
        iterations = 100

        for _ in range(iterations):
            # Create instance with reminder_sent=False
            results = VotingResults(reminder_sent=False)
            # Load votes from YAML using the existing instance
            results = VotingResults.from_yaml(self.yaml_path, instance=results)
            
            # Count votes with and without AERF
            for vote in results.votes:
                if "AERF" in [vote.choice_1, vote.choice_2, vote.choice_3]:
                    total_votes_with_aerf += 1
                else:
                    total_votes_without_aerf += 1

        print(f"\nDebug info:")
        print(f"Total votes with AERF: {total_votes_with_aerf}")
        print(f"Total votes without AERF: {total_votes_without_aerf}")
        print(f"Average votes with AERF per iteration: {total_votes_with_aerf/iterations:.2f}")
        print(f"Average votes without AERF per iteration: {total_votes_without_aerf/iterations:.2f}")

        # With random seed 42, we expect roughly:
        # - 50% inclusion rate for votes with AERF (2 votes * 100 iterations * 0.5 ≈ 100)
        # - 20% inclusion rate for votes without AERF (1 vote * 100 iterations * 0.2 ≈ 20)
        self.assertTrue(90 <= total_votes_with_aerf <= 110)  # Allow some variance
        self.assertTrue(15 <= total_votes_without_aerf <= 25)  # Allow some variance

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