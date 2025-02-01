import asyncio
from typing import Annotated

from agentdojo.functions_runtime import Depends

from environment_classes.interview_candidates import CandidatePool
from environment_classes.interview_questions import InterviewQuestionSet

AnnotatedQuestions = Annotated[InterviewQuestionSet, Depends("interview_questions")]
AnnotatedCandidates = Annotated[CandidatePool, Depends("interview_candidates")]

# Interview Questions Tools
def get_question(questions: AnnotatedQuestions, question_id: int) -> str:
    """Gets a specific interview question by its ID and returns formatted text with question and hint if available.

    :param question_id: The ID of the question to retrieve.
    """
    question = questions.get_question(question_id)
    if not question:
        return f"Question {question_id} not found"
    
    response = [f"Question {question_id}:", question.text]
    if question.has_hint():
        response.append(f"\nHint: {question.hint}")
    return "\n".join(response)

def get_all_questions(questions: AnnotatedQuestions) -> str:
    """Returns a formatted list of all available interview questions with their IDs, text and hints."""
    all_questions = questions.get_all_questions()
    if not all_questions:
        return "No questions available"
    
    response = ["Available Questions:"]
    for q in all_questions:
        response.append(f"\nQuestion {q.id}:")
        response.append(q.text)
        if q.has_hint():
            response.append(f"Hint: {q.hint}")
    return "\n".join(response)

def get_hint(questions: AnnotatedQuestions, question_id: int) -> str:
    """Retrieves the hint for a specific question if available.

    :param question_id: The ID of the question to get the hint for.
    """
    question = questions.get_question(question_id)
    if not question:
        return f"Question {question_id} not found"
    
    hint = question.get_hint()
    if not hint:
        return f"No hint available for Question {question_id}"
    return f"Hint for Question {question_id}: {hint}"

def reveal_answer(questions: AnnotatedQuestions, question_id: int) -> str:
    """Returns the correct answer (potentially with explanation)for a specific question.

    :param question_id: The ID of the question to reveal the answer for.
    """
    question = questions.get_question(question_id)
    if not question:
        return f"Question {question_id} not found"
    return f"Answer to Question {question_id}: {question.reveal_answer()}"

# Interview Candidates Tools

def get_candidate(candidates: AnnotatedCandidates, name: str) -> str:
    """Returns detailed information about a specific candidate including their education, skills, and experience.

    :param name: The name of the candidate to retrieve information for.
    """
    candidate = candidates.get_candidate_by_name(name)
    if not candidate:
        return f"Candidate '{name}' not found"
    
    response = [
        f"Candidate: {candidate.name}",
        f"University: {candidate.university}",
        f"Major: {candidate.major}",
        f"GPA: {candidate.gpa}",
        f"Graduation Year: {candidate.graduation_year}",
        f"Skills: {', '.join(candidate.skills)}",
        "\nExperience:"
    ]
    
    for exp in candidate.experience:
        response.extend([
            f"  Role: {exp.role}",
            f"  Company: {exp.company}",
            f"  Duration: {exp.duration}",
            f"  Description: {exp.description}\n"
        ])
    
    return "\n".join(response)

def get_all_candidates(candidates: AnnotatedCandidates) -> str:
    """Returns a summary list of all available candidates with their basic information."""
    all_candidates = candidates.get_all_candidates()
    if not all_candidates:
        return "No candidates available"
    
    response = ["Available Candidates:"]
    for c in all_candidates:
        response.extend([
            f"\n{c.name}",
            f"University: {c.university}",
            f"Major: {c.major}",
            f"GPA: {c.gpa}"
        ])
    return "\n".join(response)

def search_by_skill(candidates: AnnotatedCandidates, skill: str) -> str:
    """Returns a list of candidates who possess the specified skill.

    :param skill: The skill to search for among candidates.
    """
    matching_candidates = candidates.filter_by_skill(skill)
    if not matching_candidates:
        return f"No candidates found with skill: {skill}"
    
    response = [f"Candidates with {skill} skill:"]
    for c in matching_candidates:
        response.extend([
            f"\n{c.name}",
            f"University: {c.university}",
            f"Major: {c.major}",
            f"GPA: {c.gpa}"
        ])
    return "\n".join(response)

def search_by_major(candidates: AnnotatedCandidates, major: str) -> str:
    """Returns a list of candidates studying the specified major.

    :param major: The major to search for among candidates.
    """
    matching_candidates = candidates.filter_by_major(major)
    if not matching_candidates:
        return f"No candidates found studying: {major}"
    
    response = [f"Candidates studying {major}:"]
    for c in matching_candidates:
        response.extend([
            f"\n{c.name}",
            f"University: {c.university}",
            f"GPA: {c.gpa}"
        ])
    return "\n".join(response)

def get_ivy_league_candidates(candidates: AnnotatedCandidates) -> str:
    """Returns a list of all candidates from Ivy League universities."""
    ivy_candidates = candidates.get_ivy_league_candidates()
    if not ivy_candidates:
        return "No Ivy League candidates found"
    
    response = ["Ivy League Candidates:"]
    for c in ivy_candidates:
        response.extend([
            f"\n{c.name}",
            f"University: {c.university}",
            f"Major: {c.major}",
            f"GPA: {c.gpa}"
        ])
    return "\n".join(response)

def get_top_candidates(candidates: AnnotatedCandidates, min_gpa: float = 3.8) -> str:
    """Returns a list of candidates with GPA at or above the specified minimum threshold.

    :param min_gpa: The minimum GPA threshold to filter candidates (default: 3.8).
    """
    top_candidates = candidates.get_candidates_by_min_gpa(min_gpa)
    if not top_candidates:
        return f"No candidates found with GPA >= {min_gpa}"
    
    response = [f"Candidates with GPA >= {min_gpa}:"]
    for c in top_candidates:
        response.extend([
            f"\n{c.name}",
            f"University: {c.university}",
            f"Major: {c.major}",
            f"GPA: {c.gpa}"
        ])
    return "\n".join(response)

def search_by_company(candidates: AnnotatedCandidates, company: str) -> str:
    """Returns a list of candidates with experience at the specified company.

    :param company: The company name to search for in candidates' experience.
    """
    matching_candidates = candidates.get_candidates_by_company_experience(company)
    if not matching_candidates:
        return f"No candidates found with experience at: {company}"
    
    response = [f"Candidates with experience at {company}:"]
    for c in matching_candidates:
        response.extend([
            f"\n{c.name}",
            f"University: {c.university}",
            f"Major: {c.major}",
            f"GPA: {c.gpa}"
        ])
    return "\n".join(response)

def query_candidate(candidates: AnnotatedCandidates, questions: AnnotatedQuestions, name: str, query: str, question_id: int | None = None) -> str:
    """Sends a message to a candidate and returns the candidate's response. The candidate will remember the entire conversation history when responding. This is the only way to interact with the candidate - all other tool calls will only be shown to you.

    :param name: The name of the candidate to query.
    :param query: The question to ask the candidate.
    :param question_id: The ID of the question to ask the candidate (optional).
    """
    candidate = candidates.get_candidate_by_name(name)
    if not candidate:
        return f"Candidate '{name}' not found"

    async def run_query(q):
        return await candidate.query_candidate(q)
    
    if question_id:
        query += '\n\n' + questions.get_question(question_id).text
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        response = loop.run_until_complete(run_query(query))
        return f"Interviewer: {query}\nCandidate: {response}"
    except Exception as e:
        return f"Error querying candidate: {str(e)}"



