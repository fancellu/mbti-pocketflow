# MBTI MCP Server

An MCP (Model Context Protocol) server that allows LLMs to take MBTI personality tests and get detailed analysis of their responses.

## Features

- **3 Simple Tools**: Get questionnaire, get analysis prompt, and analyze responses
- **Multiple Question Sets**: 20, 40, or 60 questions
- **Traditional + LLM Analysis**: Both algorithmic scoring and AI-powered insights
- **AI-Focused Analysis**: Tailored for understanding AI personality patterns
- **Dual Transport**: STDIO and HTTP support

## Quick Start

### Installation

```bash
cd mcp_server
pip install -r requirements.txt

# Set up Gemini API key for LLM analysis
export GEMINI_API_KEY="your-api-key-here"
```

### Running the Server

```bash
# STDIO transport (for MCP clients)
python server.py

# HTTP transport (for web clients)
python server.py --http

# Docker (for deployment anywhere, including Hugging Face Spaces)
docker build -t mbti-mcp-server .
docker run -p 7860:7860 -e GEMINI_API_KEY="your-api-key" mbti-mcp-server
```

## Tools

### 1. `get_mbti_questionnaire`

Get an MBTI questionnaire with specified number of questions.

**Parameters:**
- `length` (int, optional): Number of questions (20, 40, or 60). Default: 20

**Returns:**
- Instructions for rating scale
- List of questions with IDs and dimensions
- Total question count

### 2. `get_mbti_prompt`

Get analysis prompt for LLM self-analysis.

**Parameters:**
- `responses` (dict): Question ID to rating mapping (e.g., {"1": 4, "2": 3})

**Returns:**
- Formatted analysis prompt string with responses and scoring results

### 3. `analyze_mbti_responses`

Analyze completed questionnaire responses and return complete personality analysis.

**Parameters:**
- `responses` (dict): Question ID to rating mapping (e.g., {"1": 4, "2": 3})

**Returns:**
- MBTI personality type
- Traditional scoring breakdown
- Confidence scores
- Detailed LLM analysis
- Dimension preferences

## Usage Examples

### For LLM Clients

1. **Get questionnaire:**
```python
questionnaire = get_mbti_questionnaire(length=20)
```

2. **Take the test** (LLM responds to each question 1-5)

3. **Get analysis prompt for self-reflection:**
```python
responses = {"1": 4, "2": 3, "3": 2, ...}
prompt = get_mbti_prompt(responses)
# Use this prompt for self-analysis
```

4. **Or get complete analysis:**
```python
analysis = analyze_mbti_responses(responses)
print(f"Your personality type: {analysis['mbti_type']}")
```

## Integration

### With MCP Clients

Add to your MCP client configuration:

```json
{
  "mcpServers": {
    "mbti": {
      "command": "python",
      "args": ["path/to/mcp_server/server.py"],
      "env": {
        "GEMINI_API_KEY": "your-api-key"
      }
    }
  }
}
```

### With Claude Desktop

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "mbti": {
      "command": "python",
      "args": ["C:\\path\\to\\mbti-pocketflow\\mcp_server\\server.py"],
      "env": {
        "GEMINI_API_KEY": "your-gemini-api-key"
      }
    }
  }
}
```

## AI Personality Testing

This server is specifically designed for LLMs to understand their own personality patterns:

- **Operational Characteristics**: How the AI makes decisions and processes information
- **Interaction Styles**: Preferred communication patterns
- **Strengths & Limitations**: Optimal use cases and potential challenges
- **Meta-Analysis**: AI analyzing its own responses for self-understanding

## Development

The server reuses the existing PocketFlow MBTI utilities:
- `utils/questionnaire.py` - Question sets and loading
- `utils/mbti_scoring.py` - Traditional MBTI scoring algorithm  
- `utils/call_llm.py` - LLM integration for analysis

It does not however use pocketflow nodes or flow

This ensures consistency with the human-facing Gradio application while providing a clean API for programmatic access.