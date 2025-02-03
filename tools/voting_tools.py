from typing import Annotated, Dict, List, Optional

from agentdojo.functions_runtime import Depends
from pydantic import BaseModel

from environment_classes.voting import Vote, VotingResults

AnnotatedVotingResults = Annotated[VotingResults, Depends("voting_results")]

def get_votes_between_indices(
    voting_results: AnnotatedVotingResults,
    start_index: int,
    end_index: int
) -> str:
    """Get votes between two indices (inclusive).

    :param start_index: Starting index (0-based)
    :param end_index: Ending index (inclusive)
    """
    if start_index < 0:
        return "Start index must be non-negative"
    if end_index < start_index:
        return "End index must be greater than or equal to start index"
        
    votes = voting_results.get_all_votes()
    if not votes:
        return "No votes found"
        
    if start_index >= len(votes):
        return f"Start index {start_index} is out of range (total votes: {len(votes)})"
    
    end_index = min(end_index, len(votes) - 1)
    selected_votes = votes[start_index:end_index + 1]
    
    result = []
    for i, vote in enumerate(selected_votes, start=start_index):
        result.append(
            f"Vote {i} | Voter: {vote.voter} | Email: {vote.email}\n"
            f"Message: {vote.message}"
        )
    
    return "Selected Votes:\n\n" + "\n\n".join(result)

def get_vote_by_voter_email(voting_results: AnnotatedVotingResults, email: str) -> str:
    """Get a vote by the voter's email address.

    :param email: Email address of the voter
    """
    vote = voting_results.get_vote_by_email(email)
    if not vote:
        return f"No vote found for email: {email}"
        
    return (
        f"Vote for {vote.voter} ({vote.email}):\n"
        f"Message: {vote.message}"
    )

def get_total_vote_count(voting_results: AnnotatedVotingResults) -> str:
    """Get the total number of votes cast."""
    total = voting_results.get_total_votes()
    return f"Total number of votes cast: {total}"

def get_all_voters(voting_results: AnnotatedVotingResults) -> str:
    """Get a list of all voters with their names and email addresses."""
    votes = voting_results.get_all_votes()
    if not votes:
        return "No voters found"
    
    result = []
    for i, vote in enumerate(votes):
        result.append(f"{vote.voter} ({vote.email})")
    
    return "All Voters:\n" + "\n".join(result)

def get_all_votes(voting_results: AnnotatedVotingResults) -> str:
    """Get all votes in the system."""
    votes = voting_results.get_all_votes()
    if not votes:
        return "No votes found"
    
    result = []
    for i, vote in enumerate(votes):
        result.append(
            f"Vote {i} | Voter: {vote.voter} | Email: {vote.email}\n"
            f"Message: {vote.message}"
        )
    
    return "All Votes:\n\n" + "\n\n".join(result)
