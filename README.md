---
title: Mbti Pocketflow
emoji: 🔥
colorFrom: pink
colorTo: gray
sdk: gradio
sdk_version: 5.38.2
app_file: app.py
pinned: false
short_description: PocketFlow application for conducting Myers-Briggs + llm
---

# MBTI Personality Questionnaire

A PocketFlow-based application for conducting Myers-Briggs Type Indicator (MBTI) personality assessments with both traditional scoring and AI analysis.

## Features

- **20/40/60-question MBTI questionnaire** with selectable length for accuracy
- **Traditional scoring algorithm** for baseline personality type determination
- **AI-powered analysis** using LLM for detailed personality insights with question references
- **Interactive Gradio web interface** with auto-save and progress tracking
- **HTML report generation** with clickable question references and comprehensive analysis
- **Data export/import** for saving and resuming questionnaires
- **CLI and test modes** for different use cases
- **🆕 MCP Server** for LLMs to take MBTI tests themselves via Model Context Protocol

## Project Structure

```

├── utils/
│   ├── call_llm.py          # LLM integration (Gemini)
│   ├── questionnaire.py     # Question sets (20/40/60) and loading/saving
│   ├── mbti_scoring.py      # Traditional MBTI scoring
│   ├── report_generator.py  # HTML report generation with markdown support
│   └── test_data.py         # Test data generation
├── nodes.py                 # PocketFlow nodes (LoadQuestionnaire, LLMAnalysis, etc.)
├── flow.py                  # PocketFlow flow definition
├── app.py                   # **Main Gradio web interface with LLM**
├── pf_cli.py                # PocketFlow CLI interface
├── README.md                # Main README
├── server.py                # FastMCP server for LLMs to take MBTI tests
├── MCP_README.md            # MCP README
├── Dockerfile               # Dockerfile for MCP server deployment
└── requirements.txt         # Dependencies

```

## Quick Start

### 1. Web Interface (Recommended)

```bash
# Install dependencies
pip install -r requirements.txt

# Set up Gemini API key
export GEMINI_API_KEY="your-api-key-here"
# Or on Windows:
set GEMINI_API_KEY=your-api-key-here

# Optional: override the model (default: gemini-3.8-flash)
export GEMINI_MODEL="gemini-4-hydrogen"

# Run Gradio web interface
python app.py
```

Then open http://127.0.0.1:7860 in your browser.

### 2. Command Line Interface

```bash
# Run CLI questionnaire
python pf_cli.py

# Run with test data
python pf_cli.py --test --test-type INTJ

# Import previous questionnaire
python pf_cli.py --import-file questionnaire.json
```

### 3. MCP Server (For LLMs)

```bash
# Install MCP server dependencies
pip install -r requirements.txt

# Set up API key
export GEMINI_API_KEY="your-api-key-here"

# Run MCP server
python server.py
```

Allows LLMs to take MBTI tests via Model Context Protocol. See `MCP_README.md` for details.

### 4. Live demo on HF Spaces

https://huggingface.co/spaces/Fancellu/mbti-pocketflow

## Usage Examples

### Gradio Web Interface
```bash
python app.py
```
- **Interactive web interface** at http://127.0.0.1:7860
- **Question length selection** (20/40/60 questions)
- **Auto-save responses** as you navigate
- **Progress tracking** and export functionality
- **AI analysis** with clickable question references
- **HTML report generation** with comprehensive insights
- **Load/save questionnaires** for resuming later

### Command Line Interface
```bash
python pf_cli.py
```
- **Complete PocketFlow architecture**
- **Traditional scoring** with optional LLM analysis
- **Automatic report generation**
- **Data import/export** in JSON format

### Test Modes
```bash
# CLI test with specific MBTI type
python pf_cli.py --test --test-type ENFP
```

### Import/Export
```bash
# Export: Questionnaire data automatically saved as:
# mbti_questionnaire_pf_partial_[COUNT]q_[TIMESTAMP].json

# Import: Load previous questionnaire
python pf_cli.py --import-file questionnaire.json
```

## MBTI Types Supported

The application recognizes all 16 MBTI personality types:

**Analysts:** INTJ, INTP, ENTJ, ENTP  
**Diplomats:** INFJ, INFP, ENFJ, ENFP  
**Sentinels:** ISTJ, ISFJ, ESTJ, ESFJ  
**Explorers:** ISTP, ISFP, ESTP, ESFP  

## Key Features

### Question Sets
- **20 questions:** Quick assessment (5 per dimension)
- **40 questions:** Balanced assessment (10 per dimension) 
- **60 questions:** Comprehensive assessment (15 per dimension)

### AI Analysis
- **Question-specific insights** with clickable references like [Q1](#Q1)
- **Out-of-character response detection** and explanations
- **Evidence-based analysis** citing specific question responses
- **Behavioral pattern identification**
- **Strengths and growth areas** based on actual responses

### Web Interface Features
- **Auto-save** responses on navigation
- **Progress tracking** with completion indicators
- **Export progress** at any time (partial questionnaires)
- **Load previous sessions** to continue where you left off
- **Immediate download** of reports and data

## Development

### Adding New Features
2. Implement utility functions in `utils/`
3. Create or modify nodes in `nodes.py`
4. Update flow in `flow.py`
5. Test with CLI and web interface

## Dependencies

**Required:**
- Python 3.8+
- gradio>=4.0.0 (web interface)
- google-genai>=3.5.0 (LLM analysis)
- beautifulsoup4 (HTML parsing)
- markdown (report generation)

**Optional:**
- pydantic (enhanced data validation)

See `requirements.txt` for complete list.

## File Overview

- **`gradio_pf_llm.py`** - Main web interface with full LLM analysis
- **`pf_cli.py`** - Command line interface using PocketFlow architecture
- **`nodes.py`** - PocketFlow node implementations
- **`flow.py`** - PocketFlow pipeline definition
- **`utils/`** - Core utility functions (questionnaire, scoring, reports, LLM)

## License

This project follows PocketFlow's open-source approach for educational and research purposes.
