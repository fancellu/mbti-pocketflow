import os
from datetime import datetime
try:
    import markdown
    MARKDOWN_AVAILABLE = True
except ImportError:
    MARKDOWN_AVAILABLE = False

# MBTI Type descriptions based on 16personalities.com
MBTI_DESCRIPTIONS = {
    # Analysts (NT)
    "INTJ": {
        "name": "Architect",
        "description": "Imaginative and strategic thinkers, with a plan for everything.",
        "strengths": ["Strategic thinking", "Independent", "Decisive", "Hard-working", "Open-minded"],
        "weaknesses": ["Arrogant", "Judgmental", "Overly analytical", "Loathe highly structured environments", "Clueless in romance"],
        "careers": ["Scientist", "Engineer", "Professor", "Lawyer", "Systems Analyst"]
    },
    "INTP": {
        "name": "Thinker", 
        "description": "Innovative inventors with an unquenchable thirst for knowledge.",
        "strengths": ["Analytical", "Original", "Open-minded", "Curious", "Objective"],
        "weaknesses": ["Disconnected", "Insensitive", "Dissatisfied", "Impatient", "Perfectionist"],
        "careers": ["Researcher", "Philosopher", "Architect", "Professor", "Mathematician"]
    },
    "ENTJ": {
        "name": "Commander",
        "description": "Bold, imaginative and strong-willed leaders, always finding a way – or making one.",
        "strengths": ["Efficient", "Energetic", "Self-confident", "Strong-willed", "Strategic thinkers"],
        "weaknesses": ["Stubborn", "Impatient", "Arrogant", "Poor handling of emotions", "Cold and ruthless"],
        "careers": ["CEO", "Manager", "Entrepreneur", "Judge", "Business Analyst"]
    },
    "ENTP": {
        "name": "Debater",
        "description": "Smart and curious thinkers who cannot resist an intellectual challenge.",
        "strengths": ["Knowledgeable", "Quick thinkers", "Original", "Excellent brainstormers", "Charismatic"],
        "weaknesses": ["Argumentative", "Insensitive", "Intolerant", "Find it difficult to focus", "Dislike practical matters"],
        "careers": ["Inventor", "Journalist", "Psychologist", "Photographer", "Consultant"]
    },
    
    # Diplomats (NF)
    "INFJ": {
        "name": "Advocate",
        "description": "Quiet and mystical, yet very inspiring and tireless idealists.",
        "strengths": ["Creative", "Insightful", "Inspiring", "Convincing", "Decisive"],
        "weaknesses": ["Sensitive", "Extremely private", "Perfectionist", "Always need a cause", "Can burn out easily"],
        "careers": ["Counselor", "Writer", "Psychologist", "Teacher", "Social Worker"]
    },
    "INFP": {
        "name": "Mediator",
        "description": "Poetic, kind and altruistic people, always eager to help a good cause.",
        "strengths": ["Idealistic", "Loyal", "Adaptable", "Curious", "Passionate"],
        "weaknesses": ["Too idealistic", "Too altruistic", "Impractical", "Dislike dealing with data", "Take things personally"],
        "careers": ["Writer", "Artist", "Therapist", "Librarian", "Human Resources"]
    },
    "ENFJ": {
        "name": "Protagonist",
        "description": "Charismatic and inspiring leaders, able to mesmerize their listeners.",
        "strengths": ["Tolerant", "Reliable", "Charismatic", "Altruistic", "Natural leaders"],
        "weaknesses": ["Overly idealistic", "Too selfless", "Too sensitive", "Fluctuating self-esteem", "Struggle to make tough decisions"],
        "careers": ["Teacher", "Coach", "Politician", "Sales Manager", "Event Coordinator"]
    },
    "ENFP": {
        "name": "Campaigner",
        "description": "Enthusiastic, creative and sociable free spirits, who can always find a reason to smile.",
        "strengths": ["Enthusiastic", "Creative", "Sociable", "Energetic", "Independent"],
        "weaknesses": ["Poor practical skills", "Find it difficult to focus", "Overthink things", "Get stressed easily", "Highly emotional"],
        "careers": ["Marketing", "Actor", "Musician", "Social Worker", "Entrepreneur"]
    },
    
    # Sentinels (SJ)
    "ISTJ": {
        "name": "Logistician",
        "description": "Practical and fact-minded, reliable and responsible.",
        "strengths": ["Honest", "Direct", "Strong-willed", "Dutiful", "Very responsible"],
        "weaknesses": ["Stubborn", "Insensitive", "Always by the book", "Judgmental", "Often unreasonably blame themselves"],
        "careers": ["Accountant", "Administrator", "Military Officer", "Lawyer", "Judge"]
    },
    "ISFJ": {
        "name": "Protector",
        "description": "Warm-hearted and dedicated, always ready to protect their loved ones.",
        "strengths": ["Supportive", "Reliable", "Patient", "Imaginative", "Observant"],
        "weaknesses": ["Humble", "Shy", "Take things too personally", "Repress their feelings", "Overload themselves"],
        "careers": ["Nurse", "Teacher", "Social Worker", "Counselor", "Office Manager"]
    },
    "ESTJ": {
        "name": "Executive",
        "description": "Excellent administrators, unsurpassed at managing things – or people.",
        "strengths": ["Dedicated", "Strong-willed", "Direct", "Honest", "Loyal"],
        "weaknesses": ["Inflexible", "Stubborn", "Uncomfortable with unconventional situations", "Judgmental", "Too focused on social status"],
        "careers": ["Manager", "Administrator", "Judge", "Teacher", "Military Officer"]
    },
    "ESFJ": {
        "name": "Consul",
        "description": "Extraordinarily caring, social and popular people, always eager to help.",
        "strengths": ["Strong practical skills", "Dutiful", "Very loyal", "Sensitive", "Warm"],
        "weaknesses": ["Worried about their social status", "Inflexible", "Reluctant to innovate", "Vulnerable to criticism", "Often too needy"],
        "careers": ["Teacher", "Nurse", "Social Worker", "Counselor", "Office Manager"]
    },
    
    # Explorers (SP)
    "ISTP": {
        "name": "Virtuoso",
        "description": "Bold and practical experimenters, masters of all kinds of tools.",
        "strengths": ["Optimistic", "Energetic", "Creative", "Practical", "Spontaneous"],
        "weaknesses": ["Stubborn", "Insensitive", "Private", "Reserved", "Easily bored"],
        "careers": ["Mechanic", "Engineer", "Pilot", "Paramedic", "Data Analyst"]
    },
    "ISFP": {
        "name": "Adventurer",
        "description": "Flexible and charming artists, always ready to explore new possibilities.",
        "strengths": ["Charming", "Sensitive to others", "Imaginative", "Passionate", "Curious"],
        "weaknesses": ["Fiercely independent", "Unpredictable", "Easily stressed", "Overly competitive", "Fluctuating self-esteem"],
        "careers": ["Artist", "Musician", "Designer", "Photographer", "Chef"]
    },
    "ESTP": {
        "name": "Entrepreneur",
        "description": "Smart, energetic and very perceptive people, who truly enjoy living on the edge.",
        "strengths": ["Tolerant", "Energetic", "Very perceptive", "Excellent people skills", "Direct"],
        "weaknesses": ["Impatient", "Risk-prone", "Unstructured", "May miss the bigger picture", "Defiant"],
        "careers": ["Sales Representative", "Paramedic", "Entrepreneur", "Actor", "Real Estate Agent"]
    },
    "ESFP": {
        "name": "Entertainer",
        "description": "Spontaneous, energetic and enthusiastic people – life is never boring around them.",
        "strengths": ["Bold", "Original", "Aesthetics and showcase", "Practical", "Observant"],
        "weaknesses": ["Sensitive", "Conflict-averse", "Easily bored", "Poor long-term planners", "Unfocused"],
        "careers": ["Actor", "Artist", "Photographer", "Designer", "Event Planner"]
    }
}

def markdown_to_html(markdown_text):
    """Convert markdown to HTML"""
    if not markdown_text:
        return ""
    
    if MARKDOWN_AVAILABLE:
        return markdown.markdown(markdown_text)
    else:
        # Fallback: just replace line breaks
        return markdown_text.replace('\n', '<br>')

def generate_responses_html(responses_data):
    """Generate HTML for question responses"""
    if not responses_data:
        return "<p>No response data available.</p>"
    
    html = "<table style='width: 100%; border-collapse: collapse;'>"
    html += "<tr style='background: #f0f0f0;'><th style='padding: 8px; border: 1px solid #ddd;'>Question</th><th style='padding: 8px; border: 1px solid #ddd;'>Dimension</th><th style='padding: 8px; border: 1px solid #ddd;'>Response</th></tr>"
    
    for resp in responses_data:
        html += f"<tr id='Q{resp['id']}'>"
        html += f"<td style='padding: 8px; border: 1px solid #ddd;'><strong>Q{resp['id']}:</strong> {resp['text']}</td>"
        html += f"<td style='padding: 8px; border: 1px solid #ddd; text-align: center;'>{resp['dimension']}</td>"
        html += f"<td style='padding: 8px; border: 1px solid #ddd; text-align: center;'><strong>{resp['response']}</strong></td>"
        html += "</tr>"
    
    html += "</table>"
    return html

def generate_report(mbti_type, analysis, format="html"):
    """Generate MBTI report in HTML or PDF format"""
    
    # Get type info
    type_info = MBTI_DESCRIPTIONS.get(mbti_type, {
        "name": "Unknown Type",
        "description": "Type description not available.",
        "strengths": ["To be determined"],
        "weaknesses": ["To be determined"], 
        "careers": ["Various options"]
    })
    
    # Generate HTML content
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>MBTI Report - {mbti_type}</title>
        <style>
            :root {{
                --bg-color: #ffffff;
                --text-color: #333333;
                --border-color: #ddd;
                --section-bg: #f9f9f9;
                --table-header-bg: #f0f0f0;
            }}
            
            [data-theme="dark"] {{
                --bg-color: #1a1a1a;
                --text-color: #e0e0e0;
                --border-color: #444;
                --section-bg: #2a2a2a;
                --table-header-bg: #333;
            }}
            
            body {{ 
                font-family: Arial, sans-serif; 
                margin: 40px; 
                line-height: 1.6; 
                background-color: var(--bg-color);
                color: var(--text-color);
                transition: background-color 0.3s, color 0.3s;
            }}
            .header {{ text-align: center; margin-bottom: 30px; position: relative; }}
            .theme-toggle {{
                position: absolute;
                top: 0;
                right: 0;
                background: #4CAF50;
                color: white;
                border: none;
                padding: 8px 12px;
                border-radius: 4px;
                cursor: pointer;
                font-size: 14px;
            }}
            .theme-toggle:hover {{ background: #45a049; }}
            .type-badge {{ background: #4CAF50; color: white; padding: 10px 20px; border-radius: 5px; }}
            .section {{ margin: 20px 0; }}
            .section h2 {{ color: var(--text-color); border-bottom: 2px solid #4CAF50; }}
            ul {{ padding-left: 20px; }}
            .analysis {{ background: var(--section-bg); padding: 15px; border-left: 4px solid #4CAF50; }}
            table {{ border-color: var(--border-color); }}
            th {{ background: var(--table-header-bg) !important; }}
            td, th {{ border-color: var(--border-color) !important; }}
        </style>
    </head>
    <body>
        <div class="header">
            <button class="theme-toggle" onclick="toggleTheme()">🌙 Dark</button>
            <h1>Your Personality Type</h1>
            <div class="type-badge">{mbti_type} - {type_info['name']}</div>
            <p><em>{type_info['description']}</em></p>
        </div>
        
        <div class="section">
            <h2>Question Responses</h2>
            <div class="responses">
                {generate_responses_html(analysis.get('responses_data', []))}
            </div>
        </div>
        
        <div class="section">
            <h2>Strengths</h2>
            <ul>
                {''.join([f'<li>{strength}</li>' for strength in type_info['strengths']])}
            </ul>
        </div>
        
        <div class="section">
            <h2>Areas for Growth</h2>
            <ul>
                {''.join([f'<li>{weakness}</li>' for weakness in type_info['weaknesses']])}
            </ul>
        </div>
        
        <div class="section">
            <h2>Career Suggestions</h2>
            <ul>
                {''.join([f'<li>{career}</li>' for career in type_info['careers']])}
            </ul>
        </div>
        
        <div class="section">
            <h2>Analysis Details</h2>
            <div class="analysis">
                <h3>Traditional Scoring</h3>
                <p>Scores: {analysis.get('traditional_scores', 'Not available')}</p>
                
                <h3>AI Analysis</h3>
                <div>{markdown_to_html(analysis.get('llm_analysis', 'AI analysis not performed.'))}</div>
            </div>
        </div>
        
        <div class="section">
            <p><small>Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</small></p>
        </div>
        
        <script>
            function toggleTheme() {{
                const body = document.body;
                const button = document.querySelector('.theme-toggle');
                
                if (body.getAttribute('data-theme') === 'dark') {{
                    body.removeAttribute('data-theme');
                    button.textContent = '🌙 Dark';
                    localStorage.setItem('theme', 'light');
                }} else {{
                    body.setAttribute('data-theme', 'dark');
                    button.textContent = '☀️ Light';
                    localStorage.setItem('theme', 'dark');
                }}
            }}
            
            // Load saved theme
            const savedTheme = localStorage.getItem('theme');
            if (savedTheme === 'dark') {{
                document.body.setAttribute('data-theme', 'dark');
                document.querySelector('.theme-toggle').textContent = '☀️ Light';
            }}
        </script>
    </body>
    </html>
    """
    
    # Save report to temp directory for HF Spaces compatibility
    import tempfile
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"mbti_report_{mbti_type}_{timestamp}.html"
    
    temp_dir = tempfile.gettempdir()
    full_path = os.path.join(temp_dir, filename)
    
    with open(full_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    return full_path

if __name__ == "__main__":
    # Test report generation
    test_analysis = {
        'traditional_scores': {'E_score': 0.6, 'I_score': 0.4},
        'llm_analysis': 'This person shows strong analytical thinking patterns.'
    }
    
    report_path = generate_report("INTJ", test_analysis)
    print(f"Report generated: {report_path}")