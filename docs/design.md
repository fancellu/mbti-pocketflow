---
layout: default
title: "System Design"
nav_order: 2
---

The repository root is the root of this MBTI project.
It uses PocketFlow (the `pocketflow` package) and contains its own utils in `/utils`.

# System Design: Myers-Briggs Questionnaire

> Please DON'T remove notes for AI

## Requirements

> Notes for AI: Keep it simple and clear.
> If the requirements are abstract, write concrete user stories

**User Story:** I want a Gradio app that lets a user do a MBT questionnaire and get a Myers-Briggs type and analysis.
They should be able to do the following:
- Input a MBT questionnaire (20, 40 or 60 questions)
- Export the questionnaire
- Import a previously exported questionnaire
- Get a Myers-Briggs type
- Get an HTML report (PDF was originally planned but is not implemented)
- Should be able to run in CLI mode, i.e. no GUI, just questionnaire and output
- Look at https://www.16personalities.com/
- Look at https://www.16personalities.com/mbti-personality-types
- Look at https://www.16personalities.com/articles/our-theory
- Look at this example report https://www.16personalities.com/intj-personality and its subsections
- One LLM does the analysis: Google Gemini, default `gemini-3.8-flash`, overridable with the `GEMINI_MODEL` env var (could be more LLMs later)
- We have had MBT analysis before LLMs, so there should also be non LLM analysis
- Feel free to do web searches yourself around this problem space
- Feel free to add more user stories
- Some util functions to generate example questionnaires of random or specific MBT types, for testing


**Input:**
- A MBT questionnaire, that is presented to the user
- Questionnaire json import from previously questionnaire (may contain custom questions)

**Output:**
- A Myers-Briggs type.
- An HTML report, use same subsection formatting as example
- Questionnaire export, json (does not have to be complete) (doing questionnaire again when backend agents change would be tedious!)

## Flow Design

> Notes for AI:
> 1. Consider the design patterns of agent, map-reduce, rag, and workflow. Apply them if they fit.
> 2. Present a concise, high-level description of the workflow.

### Applicable Design Pattern:

**Workflow** - Sequential task decomposition for questionnaire → scoring → analysis → report generation
**Map Reduce** - Batch processing of questionnaire responses (map: validate/normalise each response; reduce: score into personality dimensions)

The type is determined deterministically by traditional scoring; the LLM explains it but does not choose it, so there is no agent-style decision making.

### Flow high-level Design:

```mermaid
flowchart LR
    load[Load Questionnaire] --> present[Present Questions]
    present --> normalise[Normalise Responses]
    normalise --> score[Traditional Scoring]
    score --> determine[Determine MBTI Type]
    determine --> llm[LLM Analysis]
    llm --> report[Generate Report]
    report --> export[Export Results]
```

**High-level Flow:**
1. **Load Questionnaire** - Load built-in questions or import a saved questionnaire
2. **Present Questions** - Ask questions via CLI (the Gradio UI collects answers itself)
3. **Normalise Responses** - Validate and clamp each response to 1-5
4. **Traditional Scoring** - Score each E/I, S/N, T/F, J/P pair against the questions asked
5. **Determine MBTI Type** - Pick the stronger side of each pair; compute confidence per pair
6. **LLM Analysis** - Ask the LLM to explain the responses in light of the determined type
7. **Generate Report** - Create the HTML report with subsections
8. **Export Results** - Save questionnaire, responses and results as JSON for future import

### Entry points

- **`app.py`** - Gradio web UI. Collects answers itself, then runs the flow from step 3 onwards.
- **`pf_cli.py`** - CLI. Runs the full flow (`flow.create_mbti_flow()`). `--test` uses generated responses and skips the LLM step; `--import-file` loads a saved questionnaire.
- **`server.py`** - FastMCP server so LLMs can take the test themselves (see v2 below). Uses the utility functions directly, not the PocketFlow flow.

## Utility Functions

> Notes for AI:
> 1. Understand the utility function definition thoroughly by reviewing the doc.
> 2. Include only the necessary utility functions, based on nodes in the flow.


1. **`call_llm`** (`utils/call_llm.py`) - *External Dependency: Google GenAI (Gemini)*
   - *Input*: `prompt` (str), `use_cache` (bool, optional, default True)
   - *Output*: `response` (str)
   - *Necessity*: Used by the LLM analysis node and the MCP server
   - Needs `GEMINI_API_KEY`; model from `GEMINI_MODEL` (default `gemini-3.8-flash`). Prompts and responses are logged to `logs/` and cached in a JSON file in the system temp directory.

2. **`load_questionnaire`** (`utils/questionnaire.py`) - *File I/O*
   - *Input*: `file_path` (str, optional), `length` (int: 20, 40 or 60, default 20)
   - *Output*: `questions` (list of dicts with `id`, `text`, `dimension`)
   - *Necessity*: Load built-in MBTI questions or import a saved questionnaire's questions
   - `get_questionnaire_by_length(length)` returns the built-in 20/40/60-question sets

3. **`save_questionnaire`** (`utils/questionnaire.py`) - *File I/O*
   - *Input*: `questionnaire_data` (dict), `file_path` (str)
   - *Output*: `success` (bool)
   - *Necessity*: Export questionnaire responses for future use

4. **`traditional_mbti_score`** (`utils/mbti_scoring.py`) - *Traditional MBTI Algorithm*
   - *Input*: `responses` (dict of question id → 1-5), `questions` (list, optional; defaults to the built-in 60-question bank)
   - *Output*: dict of `E_score`, `I_score`, ... ; each pair sums to 1
   - *Necessity*: Non-LLM baseline scoring method
   - Agreeing with a question pushes toward its pole, disagreeing toward the opposite pole; averaged per pair so unequal question counts don't bias the result. All-neutral answers score 0.5 everywhere.

5. **`determine_mbti_type`** (`utils/mbti_scoring.py`)
   - *Input*: scores from `traditional_mbti_score`
   - *Output*: four-letter type (str). An exact 0.5 tie resolves to I, N, F or P.

6. **`generate_report`** (`utils/report_generator.py`) - *HTML Generation*
   - *Input*: `mbti_type` (str), `analysis` (dict), `format` (str, currently ignored; always HTML)
   - *Output*: `report_path` (str) - an `mbti_report_<TYPE>_<timestamp>.html` file in the system temp directory
   - *Necessity*: Create formatted reports matching 16personalities.com style

7. **`generate_test_data`** (`utils/test_data.py`) - *Test Data Generation*
   - *Input*: `mbti_type` (str, optional), `count` (int)
   - *Output*: `{"target_type", "responses"}` dict, or a list of them when `count > 1`
   - *Necessity*: Generate test questionnaires for development and testing
   - Response patterns exist only for INTJ, ENFP, ISTJ and ESTP; any other type falls back to the INTJ pattern

## Node Design

### Shared Store

> Notes for AI: Try to minimize data redundancy

The shared Store structure (created by `flow.create_shared_store(config)`) is organized as follows:

```python
shared = {
    # --- Inputs ---
    "questionnaire": {
        "questions": [],           # List of question dicts
        "responses": {},           # User responses {question_id: response}
        "metadata": {              # Questionnaire metadata
            "version": "1.0",
            "created_at": None,
            "user_id": None
        }
    },
    "config": {
        "output_format": "html",   # Only HTML is implemented
        "analysis_method": "both", # "traditional", "llm", or "both" (informational; the flow wiring decides)
        "ui_mode": "cli",          # "cli", "gradio" or "test"
        "import_file": None        # Path to a saved questionnaire to load
    },

    # --- Intermediate/Output Data ---
    "analysis": {
        "traditional_scores": {},  # E_score, I_score, ... per pair
        "llm_analysis": "",        # LLM personality analysis (markdown)
        "confidence_scores": {},   # |score1 - score2| per pair, e.g. "EI_confidence"
        "responses_data": []       # Added by LLMAnalysisNode: per-question text/response for the report
    },
    "results": {
        "mbti_type": "",           # Final MBTI type (e.g., "INTJ")
        # Reserved, not yet populated (the report uses built-in type descriptions):
        "type_description": "",
        "strengths": [],
        "weaknesses": [],
        "career_suggestions": [],
        "relationship_insights": ""
    },
    "exports": {
        "questionnaire_json": "",  # Path to exported questionnaire
        "report_path": ""          # Path to generated report
    }
}
```

### Node Steps

> Notes for AI: Carefully decide whether to use Batch/Async Node/Flow. Removed explicit try/except in exec, relying on Node's built-in fault tolerance.

**1. LoadQuestionnaireNode** (Regular Node)
- *prep*: Read `config["import_file"]`
- *exec*: Call `load_questionnaire(import_file)`
- *post*: Store questions in `shared["questionnaire"]["questions"]`, set `created_at`

**2. PresentQuestionsNode** (Regular Node)
- *prep*: Read questions and `ui_mode`
- *exec*: In CLI mode, ask each question and validate 1-5 input; other modes return nothing (Gradio collects answers itself)
- *post*: Store user responses in `shared["questionnaire"]["responses"]`

**3. AnalyzeResponsesBatchNode** (BatchNode)
- *prep*: Return list of (question_id, response) pairs
- *exec*: Normalise each response to an int 1-5 (labels like `"agree"` are mapped; numbers are clamped)
- *post*: Replace `shared["questionnaire"]["responses"]` with the normalised responses

**4. TraditionalScoringNode** (Regular Node)
- *prep*: Read responses and the questions asked
- *exec*: Call `traditional_mbti_score(responses, questions)`
- *post*: Store scores in `shared["analysis"]["traditional_scores"]`

**5. DetermineMBTITypeNode** (Regular Node)
- *prep*: Read traditional scores
- *exec*: Call `determine_mbti_type()`; compute confidence per pair
- *post*: Store type in `shared["results"]["mbti_type"]` and `shared["analysis"]["confidence_scores"]`

**6. LLMAnalysisNode** (Regular Node, max_retries=3)
- *prep*: Format every question with its response, plus the determined type and scores
- *exec*: Call `call_llm()` with the personality analysis prompt
- *post*: Store LLM analysis in `shared["analysis"]["llm_analysis"]` and per-question `responses_data` for the report

**7. GenerateReportNode** (Regular Node)
- *prep*: Read MBTI type, analysis data and output format
- *exec*: Call `generate_report()`
- *post*: Store report path in `shared["exports"]["report_path"]`

**8. ExportDataNode** (Regular Node)
- *prep*: Read questionnaire and results data
- *exec*: Build the export JSON and filename `mbti_questionnaire_<TYPE>_<timestamp>.json`
- *post*: Call `save_questionnaire()`; store the path in `shared["exports"]["questionnaire_json"]`

### v2: MCP server for LLMs (implemented)

- Lets LLMs do their own MBTI personality tests, using FastMCP. Lives in `server.py` at the repo root (originally planned for an `mcp_server` dir). See `MCP_README.md`.
- No Gradio; that's for humans. The Gradio app is unchanged.
- MCP tools:
  1. `get_mbti_questionnaire(length)` - 20, 40 or 60 question JSON payload, with instructions for the rating scale
  2. `analyze_mbti_responses(responses)` - score the filled-in questionnaire and return JSON with type, scores, confidence, dimension breakdown and the Gemini analysis (markdown)
  3. `get_mbti_prompt(responses)` - return the analysis prompt instead of calling Gemini, so the LLM can analyze itself. Very meta
- `responses` maps question id → rating 1-5. The optional `_questions` key carries the questions that were asked, so a totally custom questionnaire from the LLM itself works; without it the built-in questions are used. Invalid ids or ratings are rejected with a clear error.
- 2 transports: STDIO (default) and HTTP (`python server.py --http`, path `/mcp`, port from `PORT`, default 7860). `server.app` is also exported as an ASGI app.
- People could use this to get MBTI for many LLMs, to look for their personality, not just "how clever"
- Will help with alignment. No one wants a clever psycho

### Future ideas

- Current question payloads are for humans (they talk about friends etc). We might want a parallel set for LLMs, or several "banks"
- This is all about MBTI currently, and that lens, but we can add more to analysis prompts, e.g. "are they a psycho?"
  - Are there known sets of questions, like MBTI but for detecting psychopathy?
- PDF report output
- More test data patterns (only 4 of the 16 types today)
