#!/usr/bin/env python3
"""
MCP Server for MBTI Personality Testing
Allows LLMs to take MBTI personality tests and get analysis
"""

import sys
import os
from typing import Dict, List, Any

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastmcp import FastMCP
from utils.questionnaire import get_questionnaire_by_length
from utils.mbti_scoring import traditional_mbti_score, determine_mbti_type
from utils.call_llm import call_llm

# Initialize MCP server
mcp = FastMCP("MBTI Personality Test Server")


def _get_mbti_scores_and_type(responses: Dict[str, Any]):
    """Common function to get normalized responses, scores, and MBTI type"""
    # Extract just the numeric responses for scoring
    normalized_responses = {int(k): int(v) for k, v in responses.items() if k.isdigit()}
    traditional_scores = traditional_mbti_score(normalized_responses)
    mbti_type = determine_mbti_type(traditional_scores)
    return normalized_responses, traditional_scores, mbti_type


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


def _generate_mbti_prompt(responses: Dict[str, Any]) -> str:
    """Internal function to generate MBTI analysis prompt with full question context"""
    # Get scores and type
    normalized_responses, traditional_scores, mbti_type = _get_mbti_scores_and_type(responses)
    
    # Questions must be provided in responses
    questions = responses['_questions']
    question_lookup = {q['id']: q for q in questions}

    # Format responses for LLM analysis with full question text
    formatted_responses = []
    
    for q_id, response_val in normalized_responses.items():
        response_text = {1: "Strongly Disagree", 2: "Disagree", 3: "Neutral",
                       4: "Agree", 5: "Strongly Agree"}[response_val]
        
        q = question_lookup[q_id]
        dimension = q.get('dimension', 'Unknown')
        formatted_responses.append(f"Q{q['id']} ({dimension}): {q['text']} - **{response_text}**")

    # Generate dimension info
    dimension_info = []
    pairs = [('E', 'I'), ('S', 'N'), ('T', 'F'), ('J', 'P')]
    for dim1, dim2 in pairs:
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
        responses: Dictionary mapping question IDs to ratings (1-5)
                  Must include '_questions' key with question definitions
        
    Returns:
        Analysis prompt string for LLM self-analysis
    """
    return _generate_mbti_prompt(responses)

@mcp.tool()
def analyze_mbti_responses(responses: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze MBTI questionnaire responses and return personality analysis.
    
    Args:
        responses: Dictionary mapping question IDs to ratings (1-5)
                  Must include '_questions' key with question definitions
        
    Returns:
        Complete MBTI analysis including type, scores, and detailed analysis
    """
    # Get the analysis prompt (does all the heavy lifting)
    llm_prompt = _generate_mbti_prompt(responses)

    # Get scores and type (reuse common function)
    normalized_responses, traditional_scores, mbti_type = _get_mbti_scores_and_type(responses)

    try:
        llm_analysis = call_llm(llm_prompt)
    except Exception as e:
        llm_analysis = f"LLM analysis unavailable: {str(e)}"

    # Calculate confidence scores
    confidence_scores = {}
    pairs = [('E', 'I'), ('S', 'N'), ('T', 'F'), ('J', 'P')]
    for dim1, dim2 in pairs:
        score1 = traditional_scores.get(f'{dim1}_score', 0.5)
        score2 = traditional_scores.get(f'{dim2}_score', 0.5)
        confidence = abs(score1 - score2)
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
        "response_count": len(normalized_responses),
        "analysis_timestamp": __import__('datetime').datetime.now().isoformat()
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
