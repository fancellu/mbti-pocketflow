import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from pocketflow import Node, BatchNode
from utils.questionnaire import load_questionnaire, save_questionnaire
from utils.mbti_scoring import traditional_mbti_score, determine_mbti_type
from utils.report_generator import generate_report
# Conditional LLM import
try:
    from utils.call_llm import call_llm
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False
    def call_llm(prompt):
        return "LLM not available - install dependencies"
from datetime import datetime

class LoadQuestionnaireNode(Node):
    def prep(self, shared):
        return shared.get("config", {}).get("import_file")
    
    def exec(self, import_file):
        return load_questionnaire(import_file)
    
    def post(self, shared, prep_res, exec_res):
        shared["questionnaire"]["questions"] = exec_res
        shared["questionnaire"]["metadata"]["created_at"] = datetime.now().isoformat()
        return "default"

class PresentQuestionsNode(Node):
    def prep(self, shared):
        return shared["questionnaire"]["questions"], shared["config"]["ui_mode"]
    
    def exec(self, inputs):
        questions, ui_mode = inputs
        responses = {}
        
        if ui_mode == "cli":
            print("\n=== MBTI Personality Questionnaire ===")
            print("Rate each statement from 1-5:")
            print("1=Strongly Disagree, 2=Disagree, 3=Neutral, 4=Agree, 5=Strongly Agree\n")
            
            for q in questions:
                while True:
                    try:
                        print(f"Q{q['id']}: {q['text']}")
                        response = int(input("Your rating (1-5): "))
                        if 1 <= response <= 5:
                            responses[q['id']] = response
                            break
                        else:
                            print("Please enter a number between 1 and 5.")
                    except ValueError:
                        print("Please enter a valid number.")
                print()
        else:
            # For Gradio mode, we'll handle this in the main interface
            # For now, return empty responses to be filled by UI
            pass
            
        return responses
    
    def post(self, shared, prep_res, exec_res):
        shared["questionnaire"]["responses"] = exec_res
        return "default"

class AnalyzeResponsesBatchNode(BatchNode):
    def prep(self, shared):
        return list(shared["questionnaire"]["responses"].items())
    
    def exec(self, response_item):
        question_id, response = response_item
        # Validate and normalize response
        if isinstance(response, str):
            response_map = {
                'strongly_disagree': 1, 'disagree': 2, 'neutral': 3,
                'agree': 4, 'strongly_agree': 5
            }
            normalized = response_map.get(response, 3)
        else:
            normalized = max(1, min(5, int(response)))
        
        return (question_id, normalized)
    
    def post(self, shared, prep_res, exec_res_list):
        # Update responses with normalized values
        normalized_responses = dict(exec_res_list)
        shared["questionnaire"]["responses"] = normalized_responses
        return "default"

class TraditionalScoringNode(Node):
    def prep(self, shared):
        return shared["questionnaire"]["responses"]
    
    def exec(self, responses):
        return traditional_mbti_score(responses)
    
    def post(self, shared, prep_res, exec_res):
        shared["analysis"]["traditional_scores"] = exec_res
        return "default"

class LLMAnalysisNode(Node):
    def __init__(self, max_retries=3):
        super().__init__(max_retries=max_retries)
        if not LLM_AVAILABLE:
            print("Warning: LLM not available, using fallback analysis")
    
    def prep(self, shared):
        responses = shared["questionnaire"]["responses"]
        questions = shared["questionnaire"]["questions"]
        mbti_type = shared["results"]["mbti_type"]
        traditional_scores = shared["analysis"]["traditional_scores"]
        
        # Ensure questions are loaded
        if not questions:
            questions = load_questionnaire()
            shared["questionnaire"]["questions"] = questions
        
        # Format responses for LLM with dimension info
        formatted_responses = []
        for q in questions:
            response_val = responses.get(q['id'], 3)
            response_text = {1: "Strongly Disagree", 2: "Disagree", 3: "Neutral", 
                           4: "Agree", 5: "Strongly Agree"}[response_val]
            dimension = q.get('dimension', 'Unknown')
            formatted_responses.append(f"Q{q['id']} ({dimension}): {q['text']} - **{response_text}**")
        
        print(f"DEBUG: Formatted {len(formatted_responses)} questions for LLM")
        return "\n".join(formatted_responses), mbti_type, traditional_scores
    
    def exec(self, inputs):
        formatted_responses, mbti_type, traditional_scores = inputs
        
        # Format dimension scores for context
        dimension_info = []
        pairs = [('E', 'I'), ('S', 'N'), ('T', 'F'), ('J', 'P')]
        for dim1, dim2 in pairs:
            score1 = traditional_scores.get(f'{dim1}_score', 0.5)
            score2 = traditional_scores.get(f'{dim2}_score', 0.5)
            stronger = dim1 if score1 > score2 else dim2
            percentage = max(score1, score2) * 100
            dimension_info.append(f"{dim1}/{dim2}: {stronger} ({percentage:.1f}%)")
        
        prompt = f"""
You are analyzing MBTI questionnaire responses for someone determined to be {mbti_type} type.

Here are their EXACT responses to each question:

{formatted_responses}

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
        return call_llm(prompt)
    
    def post(self, shared, prep_res, exec_res):
        shared["analysis"]["llm_analysis"] = exec_res
        
        # Store responses data for report
        responses = shared["questionnaire"]["responses"]
        questions = shared["questionnaire"]["questions"]
        responses_data = []
        
        for q in questions:
            response_val = responses.get(q['id'], 3)
            response_text = {1: "Strongly Disagree", 2: "Disagree", 3: "Neutral", 
                           4: "Agree", 5: "Strongly Agree"}[response_val]
            responses_data.append({
                'id': q['id'],
                'text': q['text'],
                'dimension': q.get('dimension', 'Unknown'),
                'response': response_text,
                'value': response_val
            })
        
        shared["analysis"]["responses_data"] = responses_data
        return "default"

class DetermineMBTITypeNode(Node):
    def prep(self, shared):
        return shared["analysis"]["traditional_scores"], shared["analysis"].get("llm_analysis", "")
    
    def exec(self, inputs):
        traditional_scores, llm_analysis = inputs
        
        # Primary determination from traditional scoring
        mbti_type = determine_mbti_type(traditional_scores)
        
        # Calculate confidence scores
        confidence_scores = {}
        pairs = [('E', 'I'), ('S', 'N'), ('T', 'F'), ('J', 'P')]
        
        for dim1, dim2 in pairs:
            score1 = traditional_scores.get(f'{dim1}_score', 0.5)
            score2 = traditional_scores.get(f'{dim2}_score', 0.5)
            confidence = abs(score1 - score2)  # Higher difference = higher confidence
            confidence_scores[f'{dim1}{dim2}_confidence'] = confidence
        
        return {
            "mbti_type": mbti_type,
            "confidence_scores": confidence_scores
        }
    
    def post(self, shared, prep_res, exec_res):
        shared["results"]["mbti_type"] = exec_res["mbti_type"]
        shared["analysis"]["confidence_scores"] = exec_res["confidence_scores"]
        return "default"

class GenerateReportNode(Node):
    def prep(self, shared):
        return (
            shared["results"]["mbti_type"],
            shared["analysis"],
            shared["config"]["output_format"]
        )
    
    def exec(self, inputs):
        mbti_type, analysis, output_format = inputs
        return generate_report(mbti_type, analysis, output_format)
    
    def post(self, shared, prep_res, exec_res):
        shared["exports"]["report_path"] = exec_res
        return "default"

class ExportDataNode(Node):
    def prep(self, shared):
        return shared["questionnaire"], shared["results"]
    
    def exec(self, inputs):
        questionnaire, results = inputs
        
        # Create export data
        export_data = {
            "questionnaire": questionnaire,
            "results": results,
            "metadata": {
                "exported_at": datetime.now().isoformat(),
                "version": "1.0"
            }
        }
        
        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        mbti_type = results.get("mbti_type", "UNKNOWN")
        filename = f"mbti_questionnaire_{mbti_type}_{timestamp}.json"
        
        return export_data, filename
    
    def post(self, shared, prep_res, exec_res):
        export_data, filename = exec_res
        success = save_questionnaire(export_data, filename)
        
        if success:
            shared["exports"]["questionnaire_json"] = filename
        
        return "default"