import random

# MBTI type response patterns for generating test data
MBTI_PATTERNS = {
    "INTJ": {
        "E": [1, 2], "I": [4, 5], "S": [1, 2], "N": [4, 5],
        "T": [4, 5], "F": [1, 2], "J": [4, 5], "P": [1, 2]
    },
    "ENFP": {
        "E": [4, 5], "I": [1, 2], "S": [1, 2], "N": [4, 5],
        "T": [1, 2], "F": [4, 5], "J": [1, 2], "P": [4, 5]
    },
    "ISTJ": {
        "E": [1, 2], "I": [4, 5], "S": [4, 5], "N": [1, 2],
        "T": [4, 5], "F": [1, 2], "J": [4, 5], "P": [1, 2]
    },
    "ESTP": {
        "E": [4, 5], "I": [1, 2], "S": [4, 5], "N": [1, 2],
        "T": [4, 5], "F": [1, 2], "J": [1, 2], "P": [4, 5]
    }
}

def generate_test_data(mbti_type=None, count=1):
    """Generate test questionnaire responses"""
    
    # Import actual question dimensions
    import sys
    import os
    sys.path.append(os.path.dirname(__file__))
    from questionnaire import load_questionnaire
    
    questions = load_questionnaire()
    question_dimensions = {q['id']: q['dimension'] for q in questions}
    
    results = []
    
    for _ in range(count):
        # Choose random type if not specified
        if mbti_type is None:
            target_type = random.choice(list(MBTI_PATTERNS.keys()))
        else:
            target_type = mbti_type
            
        pattern = MBTI_PATTERNS.get(target_type, MBTI_PATTERNS["INTJ"])
        
        responses = {}
        for question_id, dimension in question_dimensions.items():
            # Get response range for this dimension
            response_range = pattern.get(dimension, [3])
            # Add some randomness
            if random.random() < 0.9:  # 90% follow pattern for better accuracy
                response = random.choice(response_range)
            else:  # 10% random noise
                response = random.randint(1, 5)
            
            responses[question_id] = response
        
        results.append({
            "target_type": target_type,
            "responses": responses
        })
    
    return results if count > 1 else results[0]

if __name__ == "__main__":
    # Test data generation
    test_data = generate_test_data("INTJ")
    print(f"Generated test data for INTJ:")
    print(f"Responses: {test_data['responses']}")
    
    # Generate multiple random types
    multiple_data = generate_test_data(count=3)
    for i, data in enumerate(multiple_data):
        print(f"Sample {i+1}: {data['target_type']}")