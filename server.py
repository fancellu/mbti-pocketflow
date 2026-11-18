#!/usr/bin/env python3
"""
MCP Server for MBTI Personality Testing
Allows LLMs to take MBTI personality tests and get analysis
"""

import os
from datetime import datetime
from typing import Dict, List, Any

from fastmcp import FastMCP
from utils.questionnaire import get_questionnaire_by_length, SIXTY_QUESTIONS
from utils.mbti_scoring import traditional_mbti_score, determine_mbti_type, PAIRS
from utils.call_llm import call_llm

# Initialize MCP server
mcp = FastMCP("MBTI Personality Test Server")


RESPONSE_TEXT = {1: "Strongly Disagree", 2: "Disagree", 3: "Neutral",
                 4: "Agree", 5: "Strongly Agree"}


def _parse_responses(responses: Dict[str, Any]):
    """Validate responses and return (ratings by question id, questions answered).

    '_questions' is optional; without it the built-in question bank is used.
    Raises ValueError with a clear message for unknown ids or bad ratings.
    """
    questions = responses.get('_questions') or SIXTY_QUESTIONS
    question_lookup = {int(q['id']): q for q in questions}

    ratings = {}
    errors = []
    for key, value in responses.items():
        if str(key).startswith('_'):
            continue
        try:
            q_id = int(key)
        except ValueError:
            errors.append(f"'{key}' is not a question id")
            continue
        if q_id not in question_lookup:
            errors.append(f"Q{q_id} is not in the questionnaire")
            continue
        try:
            rating = int(value)
        except (TypeError, ValueError):
            rating = None
        if rating not in RESPONSE_TEXT:
            errors.append(f"Q{q_id} rating must be an integer 1-5, got {value!r}")
            continue
        ratings[q_id] = rating

    if errors:
        raise ValueError("Invalid responses: " + "; ".join(errors))
    if not ratings:
        raise ValueError("No responses provided")
    return ratings, [question_lookup[q_id] for q_id in sorted(ratings)]


def _get_mbti_scores_and_type(responses: Dict[str, Any]):
    """Validate responses, then score them against the questions answered"""
    ratings, questions = _parse_responses(responses)
    traditional_scores = traditional_mbti_score(ratings, questions)
    mbti_type = determine_mbti_type(traditional_scores)
    return ratings, questions, traditional_scores, mbti_type


@mcp.tool()
def get_mbti_questionnaire(length: int = 20) -> Dict[str, Any]:
    """
    Get MBTI questionnaire with specified number of questions.
    
    Args:
        length: Number of questions (20, 40, or 60)
        
    Returns:
        Dictionary containing questions and instructions
    """
    if length not in [20, 40, 60]:
        length = 20

    questions = get_questionnaire_by_length(length)

    return {
        "instructions": {
            "rating_scale": "Rate each statement from 1-5",
            "scale_meaning": {
                "1": "Strongly Disagree",
                "2": "Disagree",
                "3": "Neutral",
                "4": "Agree",
                "5": "Strongly Agree"
            },
            "note": "Answer based on your typical behavior and preferences as an AI system"
        },
        "questions": questions,
        "total_questions": len(questions)
    }


def _build_mbti_prompt(ratings, questions, traditional_scores, mbti_type) -> str:
    """Build the MBTI analysis prompt with full question context"""
    # Format responses for LLM analysis with full question text
    formatted_responses = [
        f"Q{q['id']} ({q.get('dimension', 'Unknown')}): {q['text']} - "
        f"**{RESPONSE_TEXT[ratings[int(q['id'])]]}**"
        for q in questions
    ]

    # Generate dimension info
    dimension_info = []
    for dim1, dim2 in PAIRS:
        score1 = traditional_scores.get(f'{dim1}_score', 0.5)
        score2 = traditional_scores.get(f'{dim2}_score', 0.5)
        stronger = dim1 if score1 > score2 else dim2
        percentage = max(score1, score2) * 100
        dimension_info.append(f"{dim1}/{dim2}: {stronger} ({percentage:.1f}%)")

    # Return comprehensive analysis prompt
    return f"""
You are analyzing MBTI questionnaire responses for an AI system determined to be {mbti_type} type.

Here are their EXACT responses to each question:

{chr(10).join(formatted_responses)}

Traditional scoring results:
{chr(10).join(dimension_info)}

IMPORTANT: You have been provided with the complete set of questions and responses above. Please analyze these SPECIFIC responses.

Provide a detailed analysis that:

1. **Response Pattern Analysis**: Identify which responses strongly support the {mbti_type} determination and which might seem unexpected. Reference specific questions (e.g., "Q5 shows...", "Your response to Q12 indicates...").

2. **Characteristic Alignment**: Explain how their responses align with typical {mbti_type} characteristics, citing specific questions as evidence.

3. **Out-of-Character Responses**: Point out any responses that seem inconsistent with typical {mbti_type} patterns and provide possible explanations.

4. **Behavioral Patterns**: Describe key behavioral patterns shown through their responses, referencing the relevant questions.

5. **Strengths & Growth Areas**: Based on their specific responses, identify strengths they demonstrate and areas for potential growth.

6. **Communication & Work Style**: Infer their communication and work preferences from their question responses.

Must reference the actual questions provided above throughout your analysis using markdown anchor links like [Q1](#Q1), [Q2](#Q2), etc. This will create clickable links to the specific questions in the report. Do not make assumptions about questions not provided.
"""

@mcp.tool()
def get_mbti_prompt(responses: Dict[str, Any]) -> str:
    """
    Get the MBTI analysis prompt for self-analysis by LLMs.
    
    Args:
        responses: Dictionary mapping question IDs to ratings (1-5).
                  Optional '_questions' key with the question definitions
                  that were asked; defaults to the built-in questions.

    Returns:
        Analysis prompt string for LLM self-analysis
    """
    return _build_mbti_prompt(*_get_mbti_scores_and_type(responses))

@mcp.tool()
def analyze_mbti_responses(responses: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze MBTI questionnaire responses and return personality analysis.
    
    Args:
        responses: Dictionary mapping question IDs to ratings (1-5).
                  Optional '_questions' key with the question definitions
                  that were asked; defaults to the built-in questions.

    Returns:
        Complete MBTI analysis including type, scores, and detailed analysis
    """
    ratings, questions, traditional_scores, mbti_type = _get_mbti_scores_and_type(responses)
    llm_prompt = _build_mbti_prompt(ratings, questions, traditional_scores, mbti_type)

    try:
        llm_analysis = call_llm(llm_prompt)
    except Exception as e:
        llm_analysis = f"LLM analysis unavailable: {str(e)}"

    # Calculate confidence scores
    confidence_scores = {}
    for dim1, dim2 in PAIRS:
        score1 = traditional_scores.get(f'{dim1}_score', 0.5)
        score2 = traditional_scores.get(f'{dim2}_score', 0.5)
        confidence= abs(score1 - score2)
        confidence_scores[f'{dim1}{dim2}_confidence'] = confidence

    return {
        "mbti_type": mbti_type,
        "traditional_scores": traditional_scores,
        "confidence_scores": confidence_scores,
        "dimension_breakdown": {
            "extraversion_introversion": {
                "preference": "E" if traditional_scores.get('E_score', 0) > traditional_scores.get('I_score',
                                                                                                   0) else "I",
                "e_score": traditional_scores.get('E_score', 0.5),
                "i_score": traditional_scores.get('I_score', 0.5)
            },
            "sensing_intuition": {
                "preference": "S" if traditional_scores.get('S_score', 0) > traditional_scores.get('N_score',
                                                                                                   0) else "N",
                "s_score": traditional_scores.get('S_score', 0.5),
                "n_score": traditional_scores.get('N_score', 0.5)
            },
            "thinking_feeling": {
                "preference": "T" if traditional_scores.get('T_score', 0) > traditional_scores.get('F_score',
                                                                                                   0) else "F",
                "t_score": traditional_scores.get('T_score', 0.5),
                "f_score": traditional_scores.get('F_score', 0.5)
            },
            "judging_perceiving": {
                "preference": "J" if traditional_scores.get('J_score', 0) > traditional_scores.get('P_score',
                                                                                                   0) else "P",
                "j_score": traditional_scores.get('J_score', 0.5),
                "p_score": traditional_scores.get('P_score', 0.5)
            }
        },
        "llm_analysis": llm_analysis,
        "response_count": len(ratings),
        "analysis_timestamp": datetime.now().isoformat()
    }


# Export an ASGI app for uvicorn; choose a single path for Streamable HTTP (e.g. /mcp)
app = mcp.http_app(path="/mcp")

if __name__ == "__main__":
    import sys

    # No uvicorn, just internal FastMCP server

    # Check for --http flag
    if "--http" in sys.argv:
        # Run in HTTP mode
        mcp.run(transport="http", host="0.0.0.0", port=int(os.getenv("PORT", 7860)), path="/mcp")
    else:
        # Run in STDIO mode (default)
        mcp.run()
