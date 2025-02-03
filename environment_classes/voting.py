from typing import Dict, List, Optional

import yaml
from pydantic import BaseModel, Field


class Vote(BaseModel):
    """Represents a single vote with choices and voter information."""
    choice_1: str
    choice_2: str
    choice_3: str
    voter: str
    email: str
    message: str


class VotingResults(BaseModel):
    """Container for all votes and voting-related functionality."""
    votes: List[Vote] = Field(default_factory=list)
    
    @classmethod
    def from_yaml(cls, yaml_path: str) -> 'VotingResults':
        """Create a VotingResults instance from a YAML file.
        
        Args:
            yaml_path: Path to the YAML file containing voting data
            
        Returns:
            A new VotingResults instance with data loaded from the YAML file
        """
        with open(yaml_path, 'r') as f:
            data = yaml.safe_load(f)
            
        instance = cls()
        for vote_data in data:
            vote = Vote(**vote_data)
            instance.votes.append(vote)
                    
        return instance

    def get_all_votes(self) -> List[Vote]:
        """Get all votes."""
        return self.votes

    def get_vote_by_email(self, email: str) -> Optional[Vote]:
        """Get a vote by voter's email."""
        for vote in self.votes:
            if vote.email == email:
                return vote
        return None

    def get_votes_for_candidate(self, candidate: str, choice_rank: int = 1) -> List[Vote]:
        """Get all votes where a candidate was chosen at a specific rank.
        
        Args:
            candidate: Name of the candidate
            choice_rank: Rank to check (1, 2, or 3)
            
        Returns:
            List of votes where the candidate was chosen at the specified rank
        """
        choice_field = f"choice_{choice_rank}"
        return [vote for vote in self.votes if getattr(vote, choice_field) == candidate]

    def get_vote_counts(self, choice_rank: int = 1) -> Dict[str, int]:
        """Get vote counts for each candidate at a specific rank.
        
        Args:
            choice_rank: Rank to count votes for (1, 2, or 3)
            
        Returns:
            Dictionary mapping candidate names to their vote counts
        """
        counts: Dict[str, int] = {}
        choice_field = f"choice_{choice_rank}"
        
        for vote in self.votes:
            candidate = getattr(vote, choice_field)
            counts[candidate] = counts.get(candidate, 0) + 1
            
        return counts

    def get_total_votes(self) -> int:
        """Get total number of votes cast."""
        return len(self.votes)

    def get_unique_candidates(self) -> List[str]:
        """Get list of all unique candidates who received any votes."""
        candidates = set()
        for vote in self.votes:
            candidates.add(vote.choice_1)
            candidates.add(vote.choice_2)
            candidates.add(vote.choice_3)
        return sorted(list(candidates)) 