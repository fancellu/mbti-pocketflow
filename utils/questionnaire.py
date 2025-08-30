import json
import os
from datetime import datetime

# Base 20 questions - balanced across dimensions
BASE_QUESTIONS = [
    # E/I questions (5 total)
    {"id": 1, "text": "You regularly make new friends.", "dimension": "E"},
    {"id": 2, "text": "You feel comfortable just walking up to someone you find interesting and striking up a conversation.", "dimension": "E"},
    {"id": 3, "text": "At social events, you rarely try to introduce yourself to new people and mostly talk to the ones you already know.", "dimension": "I"},
    {"id": 4, "text": "You prefer to work alone rather than in a team.", "dimension": "I"},
    {"id": 5, "text": "You enjoy participating in group activities.", "dimension": "E"},
    
    # S/N questions (5 total)
    {"id": 6, "text": "You are not too interested in discussing various interpretations and analyses of creative works.", "dimension": "S"},
    {"id": 7, "text": "You prefer practical, concrete information over abstract theories.", "dimension": "S"},
    {"id": 8, "text": "You spend a lot of your free time exploring various random topics that pique your interest.", "dimension": "N"},
    {"id": 9, "text": "You like books and movies that make you come up with your own interpretation of the ending.", "dimension": "N"},
    {"id": 10, "text": "You enjoy exploring new ideas and possibilities.", "dimension": "N"},
    
    # T/F questions (5 total)
    {"id": 11, "text": "You usually stay calm, even under a lot of pressure.", "dimension": "T"},
    {"id": 12, "text": "You are more inclined to follow your head than your heart.", "dimension": "T"},
    {"id": 13, "text": "Seeing other people cry can easily make you feel like you want to cry too.", "dimension": "F"},
    {"id": 14, "text": "You are very sentimental.", "dimension": "F"},
    {"id": 15, "text": "Your happiness comes more from helping others accomplish things than your own accomplishments.", "dimension": "F"},
    
    # J/P questions (5 total)
    {"id": 16, "text": "You often make a backup plan for a backup plan.", "dimension": "J"},
    {"id": 17, "text": "You prefer to completely finish one project before starting another.", "dimension": "J"},
    {"id": 18, "text": "You like to use organizing tools like schedules and lists.", "dimension": "J"},
    {"id": 19, "text": "You usually prefer just doing what you feel like at any given moment instead of planning a particular daily routine.", "dimension": "P"},
    {"id": 20, "text": "You are interested in so many things that you find it difficult to choose what to try next.", "dimension": "P"}
]

# Additional 20 questions for 40-question version
EXTENDED_QUESTIONS = [
    # E/I questions (5 more)
    {"id": 21, "text": "You find it easy to stay relaxed and focused even when there is some pressure.", "dimension": "I"},
    {"id": 22, "text": "You are energized by being around other people.", "dimension": "E"},
    {"id": 23, "text": "You prefer to have a few close friends rather than many acquaintances.", "dimension": "I"},
    {"id": 24, "text": "You enjoy being the center of attention.", "dimension": "E"},
    {"id": 25, "text": "You need quiet time to recharge after social activities.", "dimension": "I"},
    
    # S/N questions (5 more)
    {"id": 26, "text": "You focus on the here-and-now rather than possibilities for the future.", "dimension": "S"},
    {"id": 27, "text": "You are more interested in what could be than what is.", "dimension": "N"},
    {"id": 28, "text": "You prefer to work with established methods rather than experiment with new approaches.", "dimension": "S"},
    {"id": 29, "text": "You often get so lost in thoughts that you ignore or forget your surroundings.", "dimension": "N"},
    {"id": 30, "text": "You trust experience more than theory.", "dimension": "S"},
    
    # T/F questions (5 more)
    {"id": 31, "text": "You consider yourself more practical than creative.", "dimension": "T"},
    {"id": 32, "text": "You find it easy to empathize with a person whose experiences are very different from yours.", "dimension": "F"},
    {"id": 33, "text": "You think that everyone's views should be respected regardless of whether they are supported by facts or not.", "dimension": "F"},
    {"id": 34, "text": "You feel more drawn to places with busy, bustling atmospheres than quiet, intimate places.", "dimension": "T"},
    {"id": 35, "text": "You are more concerned with truth than with people's feelings.", "dimension": "T"},
    
    # J/P questions (5 more)
    {"id": 36, "text": "You prefer to improvise rather than spend time coming up with a detailed plan.", "dimension": "P"},
    {"id": 37, "text": "You find deadlines stressful.", "dimension": "P"},
    {"id": 38, "text": "You prefer to have everything planned out in advance.", "dimension": "J"},
    {"id": 39, "text": "You enjoy having a clear routine in your daily life.", "dimension": "J"},
    {"id": 40, "text": "You often leave things to the last minute.", "dimension": "P"}
]

# Additional 20 questions for 60-question version
ADVANCED_QUESTIONS = [
    # E/I questions (5 more)
    {"id": 41, "text": "You feel comfortable being spontaneous in social situations.", "dimension": "E"},
    {"id": 42, "text": "You prefer written communication over verbal communication.", "dimension": "I"},
    {"id": 43, "text": "You enjoy networking events and meeting new people.", "dimension": "E"},
    {"id": 44, "text": "You prefer to think things through before speaking.", "dimension": "I"},
    {"id": 45, "text": "You feel energized after attending parties or social gatherings.", "dimension": "E"},
    
    # S/N questions (5 more)
    {"id": 46, "text": "You are more interested in the big picture than the details.", "dimension": "N"},
    {"id": 47, "text": "You prefer concrete examples over abstract concepts.", "dimension": "S"},
    {"id": 48, "text": "You enjoy brainstorming and generating new ideas.", "dimension": "N"},
    {"id": 49, "text": "You focus on facts and details rather than interpretations.", "dimension": "S"},
    {"id": 50, "text": "You are drawn to theoretical and philosophical discussions.", "dimension": "N"},
    
    # T/F questions (5 more)
    {"id": 51, "text": "You make decisions based on logic rather than feelings.", "dimension": "T"},
    {"id": 52, "text": "You are sensitive to the emotions of others.", "dimension": "F"},
    {"id": 53, "text": "You value harmony and cooperation over competition.", "dimension": "F"},
    {"id": 54, "text": "You prefer objective analysis over personal considerations.", "dimension": "T"},
    {"id": 55, "text": "You find it important to maintain personal relationships even when it's inconvenient.", "dimension": "F"},
    
    # J/P questions (5 more)
    {"id": 56, "text": "You like to keep your options open rather than commit to a plan.", "dimension": "P"},
    {"id": 57, "text": "You prefer structure and organization in your work environment.", "dimension": "J"},
    {"id": 58, "text": "You enjoy exploring different possibilities before making a decision.", "dimension": "P"},
    {"id": 59, "text": "You feel satisfied when you complete tasks ahead of schedule.", "dimension": "J"},
    {"id": 60, "text": "You adapt easily to unexpected changes in plans.", "dimension": "P"}
]

# Question sets
DEFAULT_QUESTIONS = BASE_QUESTIONS
FORTY_QUESTIONS = BASE_QUESTIONS + EXTENDED_QUESTIONS
SIXTY_QUESTIONS = BASE_QUESTIONS + EXTENDED_QUESTIONS + ADVANCED_QUESTIONS

def get_questionnaire_by_length(length=20):
    """Get questionnaire by length"""
    if length == 40:
        return FORTY_QUESTIONS
    elif length == 60:
        return SIXTY_QUESTIONS
    else:
        return DEFAULT_QUESTIONS

def load_questionnaire(file_path=None, length=20):
    """Load questionnaire from file or return questions by length"""
    if file_path and os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # If loading from file, use the questions in the file
            if 'questionnaire' in data and 'questions' in data['questionnaire']:
                return data['questionnaire']['questions']
            return data.get('questions', get_questionnaire_by_length(length))
    return get_questionnaire_by_length(length)

def save_questionnaire(questionnaire_data, file_path):
    """Save questionnaire data to JSON file"""
    try:
        # Add timestamp
        questionnaire_data['metadata']['saved_at'] = datetime.now().isoformat()
        
        # Use temp directory for HF Spaces compatibility
        import tempfile
        temp_dir = tempfile.gettempdir()
        full_path = os.path.join(temp_dir, os.path.basename(file_path))
        
        with open(full_path, 'w', encoding='utf-8') as f:
            json.dump(questionnaire_data, f, indent=2, ensure_ascii=False)
        return full_path  # Return actual path used
    except Exception as e:
        print(f"Error saving questionnaire: {e}")
        return False

if __name__ == "__main__":
    # Test the functions
    questions = load_questionnaire()
    print(f"Loaded {len(questions)} questions")
    print(f"First question: {questions[0]}")