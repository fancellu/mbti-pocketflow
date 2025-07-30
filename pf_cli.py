#!/usr/bin/env python3
"""
PocketFlow-based MBTI questionnaire using the actual flow and shared store
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from flow import create_mbti_flow, create_shared_store
from utils.test_data import generate_test_data

def run_pocketflow_questionnaire(import_file=None):
    """Run questionnaire using PocketFlow"""
    print("=== MBTI Questionnaire (PocketFlow) ===\n")
    
    # Create flow and shared store
    flow = create_mbti_flow()
    config = {
        "ui_mode": "cli",
        "output_format": "html",
        "analysis_method": "traditional",  # Skip LLM for now
        "import_file": import_file
    }
    shared = create_shared_store(config)
    
    try:
        print("Running PocketFlow pipeline...")
        flow.run(shared)
        
        # Display results
        print("\n" + "="*50)
        print("POCKETFLOW RESULTS")
        print("="*50)
        print(f"Your MBTI Type: {shared['results']['mbti_type']}")
        print(f"Report generated: {shared['exports']['report_path']}")
        print(f"Data exported: {shared['exports']['questionnaire_json']}")
        
        # Show confidence scores
        confidence = shared['analysis']['confidence_scores']
        if confidence:
            print(f"\nConfidence Scores:")
            for dimension, score in confidence.items():
                print(f"  {dimension}: {score:.2f}")
        
        # Show traditional scores
        traditional = shared['analysis']['traditional_scores']
        if traditional:
            print(f"\nDimension Scores:")
            pairs = [('E', 'I'), ('S', 'N'), ('T', 'F'), ('J', 'P')]
            for dim1, dim2 in pairs:
                score1 = traditional.get(f'{dim1}_score', 0.5)
                score2 = traditional.get(f'{dim2}_score', 0.5)
                stronger = dim1 if score1 > score2 else dim2
                percentage = max(score1, score2) * 100
                print(f"  {dim1}/{dim2}: {stronger} ({percentage:.1f}%)")
        
        print(f"\nOpen '{shared['exports']['report_path']}' to view the full report.")
        
    except Exception as e:
        print(f"Error running PocketFlow: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

def run_pocketflow_test(mbti_type=None):
    """Run test using PocketFlow with test data"""
    print("=== MBTI Test Mode (PocketFlow) ===\n")
    
    # Generate test data
    test_data = generate_test_data(mbti_type)
    print(f"Generated test data for: {test_data['target_type']}")
    
    # Create flow and shared store
    flow = create_mbti_flow()
    config = {
        "ui_mode": "test",
        "output_format": "html",
        "analysis_method": "traditional"
    }
    shared = create_shared_store(config)
    
    # Pre-populate with test data (skip question presentation)
    shared["questionnaire"]["responses"] = test_data['responses']
    
    try:
        print("Running PocketFlow analysis...")
        
        # Skip to analysis nodes (questions already answered)
        from pocketflow import Flow
        from nodes import AnalyzeResponsesBatchNode, TraditionalScoringNode, DetermineMBTITypeNode, GenerateReportNode, ExportDataNode
        
        analyze_responses = AnalyzeResponsesBatchNode()
        traditional_scoring = TraditionalScoringNode()
        determine_type = DetermineMBTITypeNode()
        generate_report = GenerateReportNode()
        export_data = ExportDataNode()
        
        # Connect partial flow
        analyze_responses >> traditional_scoring >> determine_type >> generate_report >> export_data
        test_flow = Flow(start=analyze_responses)
        
        # Run the flow
        test_flow.run(shared)
        
        # Display results
        print("\n" + "="*50)
        print("POCKETFLOW TEST RESULTS")
        print("="*50)
        print(f"Target Type: {test_data['target_type']}")
        print(f"Detected Type: {shared['results']['mbti_type']}")
        print(f"Match: {'YES' if test_data['target_type'] == shared['results']['mbti_type'] else 'NO'}")
        print(f"Report: {shared['exports']['report_path']}")
        
    except Exception as e:
        print(f"Error in PocketFlow test: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='MBTI Questionnaire using PocketFlow')
    parser.add_argument('--test', action='store_true', help='Run in test mode')
    parser.add_argument('--test-type', type=str, help='MBTI type for test mode')
    parser.add_argument('--import-file', type=str, help='Import questionnaire from JSON')
    
    args = parser.parse_args()
    
    if args.test:
        success = run_pocketflow_test(args.test_type)
    else:
        success = run_pocketflow_questionnaire(args.import_file)
    
    exit(0 if success else 1)