def traditional_mbti_score(responses):
    """Traditional MBTI scoring algorithm"""
    # Initialize scores for each dimension
    scores = {
        'E': 0, 'I': 0,  # Extraversion vs Introversion
        'S': 0, 'N': 0,  # Sensing vs Intuition  
        'T': 0, 'F': 0,  # Thinking vs Feeling
        'J': 0, 'P': 0   # Judging vs Perceiving
    }
    
    # Import the actual question dimensions from questionnaire.py
    from .questionnaire import load_questionnaire
    questions = load_questionnaire()
    question_dimensions = {q['id']: q['dimension'] for q in questions}
    
    # Score each response (1=Disagree, 2=Slightly Disagree, 3=Neutral, 4=Slightly Agree, 5=Agree)
    for question_id, response in responses.items():
        if question_id in question_dimensions:
            dimension = question_dimensions[question_id]
            
            # Convert response to score (1-5 scale)
            if isinstance(response, str):
                response_map = {
                    'strongly_disagree': 1, 'disagree': 2, 'neutral': 3,
                    'agree': 4, 'strongly_agree': 5
                }
                score = response_map.get(response, 3)
            else:
                score = int(response)
            
            # Add to dimension score
            scores[dimension] += score
    
    # Calculate percentages for each dimension pair
    result = {}
    pairs = [('E', 'I'), ('S', 'N'), ('T', 'F'), ('J', 'P')]
    
    for dim1, dim2 in pairs:
        total = scores[dim1] + scores[dim2]
        if total > 0:
            result[f'{dim1}_score'] = scores[dim1] / total
            result[f'{dim2}_score'] = scores[dim2] / total
        else:
            result[f'{dim1}_score'] = 0.5
            result[f'{dim2}_score'] = 0.5
    
    return result

def determine_mbti_type(scores):
    """Determine MBTI type from scores"""
    type_str = ""
    
    # E vs I
    type_str += "E" if scores.get('E_score', 0) > scores.get('I_score', 0) else "I"
    
    # S vs N  
    type_str += "S" if scores.get('S_score', 0) > scores.get('N_score', 0) else "N"
    
    # T vs F
    type_str += "T" if scores.get('T_score', 0) > scores.get('F_score', 0) else "F"
    
    # J vs P
    type_str += "J" if scores.get('J_score', 0) > scores.get('P_score', 0) else "P"
    
    return type_str

if __name__ == "__main__":
    # Test scoring
    test_responses = {
        1: 4, 2: 5, 3: 3, 4: 4, 5: 3,
        6: 2, 7: 4, 8: 4, 9: 5, 10: 3,
        11: 4, 12: 2, 13: 4, 14: 3, 15: 4,
        16: 5, 17: 4, 18: 4, 19: 3, 20: 2
    }
    
    scores = traditional_mbti_score(test_responses)
    mbti_type = determine_mbti_type(scores)
    print(f"Scores: {scores}")
    print(f"MBTI Type: {mbti_type}")