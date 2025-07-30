import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from pocketflow import Flow
from nodes import (
    LoadQuestionnaireNode,
    PresentQuestionsNode, 
    AnalyzeResponsesBatchNode,
    TraditionalScoringNode,
    LLMAnalysisNode,
    DetermineMBTITypeNode,
    GenerateReportNode,
    ExportDataNode
)

def create_mbti_flow():
    """Create and return the complete MBTI questionnaire flow"""
    
    # Create all nodes
    load_questionnaire = LoadQuestionnaireNode()
    present_questions = PresentQuestionsNode()
    analyze_responses = AnalyzeResponsesBatchNode()
    traditional_scoring = TraditionalScoringNode()
    llm_analysis = LLMAnalysisNode()
    determine_type = DetermineMBTITypeNode()
    generate_report = GenerateReportNode()
    export_data = ExportDataNode()
    
    # Connect nodes in sequence
    load_questionnaire >> present_questions
    present_questions >> analyze_responses
    analyze_responses >> traditional_scoring
    traditional_scoring >> determine_type
    determine_type >> llm_analysis
    llm_analysis >> generate_report
    generate_report >> export_data
    
    # Create and return flow
    return Flow(start=load_questionnaire)

def create_shared_store(config=None):
    """Create initial shared store with default configuration"""
    
    default_config = {
        "output_format": "html",
        "analysis_method": "both", 
        "ui_mode": "cli",
        "import_file": None
    }
    
    if config:
        default_config.update(config)
    
    return {
        # --- Inputs ---
        "questionnaire": {
            "questions": [],
            "responses": {},
            "metadata": {
                "version": "1.0",
                "created_at": None,
                "user_id": None
            }
        },
        "config": default_config,
        
        # --- Intermediate/Output Data ---
        "analysis": {
            "traditional_scores": {},
            "llm_analysis": "",
            "confidence_scores": {}
        },
        "results": {
            "mbti_type": "",
            "type_description": "",
            "strengths": [],
            "weaknesses": [],
            "career_suggestions": [],
            "relationship_insights": ""
        },
        "exports": {
            "questionnaire_json": "",
            "report_path": ""
        }
    }

if __name__ == "__main__":
    # Test the flow creation
    flow = create_mbti_flow()
    shared = create_shared_store()
    
    print("MBTI Flow created successfully!")
    print(f"Shared store initialized with config: {shared['config']}")