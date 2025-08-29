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


def _get_mbti_scores_and_type(responses: Dict[str, int]):
    """Common function to get normalized responses, scores, and MBTI type"""
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


def _generate_mbti_prompt(responses: Dict[str, int]) -> str:
    """Internal function to generate MBTI analysis prompt"""
    # Get scores and type
    normalized_responses, traditional_scores, mbti_type = _get_mbti_scores_and_type(responses)

    # Format responses for LLM analysis
    formatted_responses = []
    for q_id, response_val in normalized_responses.items():
        response_text = {1: "Strongly Disagree", 2: "Disagree", 3: "Neutral",
                         4: "Agree", 5: "Strongly Agree"}[response_val]
        formatted_responses.append(f"Q{q_id}: Response - **{response_text}**")

    # Generate dimension info
    dimension_info = []
    pairs = [('E', 'I'), ('S', 'N'), ('T', 'F'), ('J', 'P')]
    for dim1, dim2 in pairs:
        score1 = traditional_scores.get(f'{dim1}_score', 0.5)
        score2 = traditional_scores.get(f'{dim2}_score', 0.5)
        stronger = dim1 if score1 > score2 else dim2
        percentage = max(score1, score2) * 100
        dimension_info.append(f"{dim1}/{dim2}: {stronger} ({percentage:.1f}%)")

    # Return the analysis prompt
    return f"""
You are analyzing MBTI questionnaire responses for an AI system determined to be {mbti_type} type.

Here are the responses:

{chr(10).join(formatted_responses)}

Traditional scoring results:
{chr(10).join(dimension_info)}

Provide a detailed analysis of this {mbti_type} personality type based on the response patterns shown above.

Analyze:
1. **Response Pattern Analysis**: How the responses support the {mbti_type} determination
2. **Characteristic Alignment**: How responses align with typical {mbti_type} traits
3. **Behavioral Patterns**: Key patterns shown in the responses
4. **Strengths & Growth Areas**: Based on the response patterns
5. **Communication & Work Style**: Inferred from the responses

Reference specific questions in your analysis (e.g., "Q5 shows...", "Response to Q12 indicates...").
"""

@mcp.tool()
def get_mbti_prompt(responses: Dict[str, int]) -> str:
    """
    Get the MBTI analysis prompt for self-analysis by LLMs.
    
    Args:
        responses: Dictionary mapping question IDs to ratings (1-5)
        
    Returns:
        Analysis prompt string for LLM self-analysis
    """
    return _generate_mbti_prompt(responses)

@mcp.tool()
def analyze_mbti_responses(responses: Dict[str, int]) -> Dict[str, Any]:
    """
    Analyze MBTI questionnaire responses and return personality analysis.
    
    Args:
        responses: Dictionary mapping question IDs to ratings (1-5)
        
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
