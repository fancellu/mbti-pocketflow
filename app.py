#!/usr/bin/env python3
"""
PocketFlow-based Gradio GUI for MBTI Personality Questionnaire - V2 with Auto-save and LLM
"""

import sys
import os
import json
import gradio as gr
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from flow import create_mbti_flow, create_shared_store
from utils.questionnaire import load_questionnaire, save_questionnaire


class MBTIPocketFlowApp:
    def __init__(self):
        self.questions = load_questionnaire()
        self.responses = {}
        self.shared = None
        self.last_report_path = None
        self.questionnaire_length = 20

    def get_question_text(self, question_idx):
        """Get current question text"""
        if 0 <= question_idx < len(self.questions):
            q = self.questions[question_idx]
            return f"Question {question_idx + 1} of {len(self.questions)}: {q['text']}"
        return "All questions completed!"

    def get_current_response(self, question_idx):
        """Get current response for question"""
        if 0 <= question_idx < len(self.questions):
            q_id = self.questions[question_idx]['id']
            return self.responses.get(q_id, 3)
        return 3

    def navigate_question(self, question_idx, direction, current_response):
        """Navigate to previous/next question and auto-save current response"""
        # Auto-save current response before navigating
        if 0 <= question_idx < len(self.questions):
            q_id = self.questions[question_idx]['id']
            self.responses[q_id] = current_response
            print(f"DEBUG: Saved Q{q_id} = {current_response}")

        # Navigate
        if direction == "prev":
            new_idx = max(0, question_idx - 1)
        else:  # next
            new_idx = min(len(self.questions) - 1, question_idx + 1)

        question_text = self.get_question_text(new_idx)
        new_response = self.get_current_response(new_idx)

        # Update button states
        prev_disabled = new_idx == 0
        next_disabled = new_idx == len(self.questions) - 1

        # Check if all questions answered (after saving current response)
        all_answered = len(self.responses) == len(self.questions)
        print(f"DEBUG: {len(self.responses)}/{len(self.questions)} answered, all_answered={all_answered}")

        return new_idx, question_text, new_response, gr.update(interactive=not prev_disabled), gr.update(
            interactive=not next_disabled), gr.update(visible=all_answered)

    def change_questionnaire_length(self, length):
        """Change questionnaire length and reset"""
        from utils.questionnaire import get_questionnaire_by_length

        self.questionnaire_length = length
        self.questions = get_questionnaire_by_length(length)
        self.responses = {}  # Reset responses

        # Return to first question
        question_text = self.get_question_text(0)
        return 0, question_text, 3, gr.update(visible=False)

    def save_slider_response(self, question_idx, current_response):
        """Save response when slider changes"""
        if 0 <= question_idx < len(self.questions):
            q_id = self.questions[question_idx]['id']
            self.responses[q_id] = current_response
            print(f"DEBUG: Slider saved Q{q_id} = {current_response}")

        # Check if all questions answered
        all_answered = len(self.responses) == len(self.questions)
        return gr.update(visible=all_answered)

    def run_pocketflow_analysis_with_save(self, question_idx, current_response):
        """Save current response then run analysis"""
        # Save current response before analysis
        if 0 <= question_idx < len(self.questions):
            q_id = self.questions[question_idx]['id']
            self.responses[q_id] = current_response

        # Run the analysis
        return self.run_pocketflow_analysis()

    def save_current_questionnaire(self, question_idx=None, current_response=None):
        """Save current questionnaire state (even if incomplete)"""
        # Save current response if provided
        if question_idx is not None and current_response is not None and 0 <= question_idx < len(self.questions):
            q_id = self.questions[question_idx]['id']
            self.responses[q_id] = current_response

        if not self.responses:
            return None

        questionnaire_data = {
            "questionnaire": {
                "questions": self.questions,
                "responses": self.responses
            },
            "metadata": {
                "version": "1.0",
                "created_at": datetime.now().isoformat(),
                "completed": len(self.responses) == len(self.questions)
            }
        }

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        answered_count = len(self.responses)
        json_filename = f"mbti_questionnaire_pf_partial_{answered_count}q_{timestamp}.json"

        saved_path = save_questionnaire(questionnaire_data, json_filename)
        if saved_path:
            return saved_path
        return None

    def run_pocketflow_analysis(self):
        """Run complete PocketFlow analysis with LLM"""
        if len(self.responses) != len(self.questions):
            return "Please answer all questions before analyzing.", "", gr.update(visible=False)

        try:
            # Create flow and shared store
            flow = create_mbti_flow()
            config = {
                "ui_mode": "gradio",
                "output_format": "html",
                "analysis_method": "both"  # Use both traditional and LLM
            }
            self.shared = create_shared_store(config)

            # Pre-populate responses and current questions
            self.shared["questionnaire"]["responses"] = self.responses
            self.shared["questionnaire"]["questions"] = self.questions

            # Run partial flow (skip question loading/presentation)
            from pocketflow import Flow
            from nodes import AnalyzeResponsesBatchNode, TraditionalScoringNode, LLMAnalysisNode, DetermineMBTITypeNode, \
                GenerateReportNode, ExportDataNode

            analyze_responses = AnalyzeResponsesBatchNode()
            traditional_scoring = TraditionalScoringNode()
            llm_analysis = LLMAnalysisNode()
            determine_type = DetermineMBTITypeNode()
            generate_report = GenerateReportNode()
            export_data = ExportDataNode()

            # Connect partial flow
            analyze_responses >> traditional_scoring >> llm_analysis >> determine_type >> generate_report >> export_data
            analysis_flow = Flow(start=analyze_responses)

            # Run the flow
            print("Running PocketFlow analysis with LLM...")
            analysis_flow.run(self.shared)

            # Extract results
            mbti_type = self.shared["results"]["mbti_type"]
            scores = self.shared["analysis"]["traditional_scores"]
            llm_analysis_text = self.shared["analysis"]["llm_analysis"]
            report_path = self.shared["exports"]["report_path"]

            self.last_report_path = os.path.abspath(report_path)

            # Read report HTML
            with open(report_path, 'r', encoding='utf-8') as f:
                report_html = f.read()

            # Extract type info from HTML report for summary
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(report_html, 'html.parser')

            # Get type badge and description
            type_badge = soup.find('div', class_='type-badge')
            type_desc = soup.find('p').find('em') if soup.find('p') else None

            # Get strengths and weaknesses sections
            sections = soup.find_all('div', class_='section')
            strengths_html = ""
            weaknesses_html = ""
            careers_html = ""

            for section in sections:
                h2 = section.find('h2')
                if h2:
                    if 'Strengths' in h2.text:
                        strengths_html = str(section)
                    elif 'Growth' in h2.text or 'Areas' in h2.text:
                        weaknesses_html = str(section)
                    elif 'Career' in h2.text:
                        careers_html = str(section)

            # Get responses data for the table
            responses_data = self.shared["analysis"].get("responses_data", [])

            # Generate responses table HTML
            responses_table_html = """
            <div style="margin: 20px 0;">
                <h2 style="color: #333; border-bottom: 2px solid #4CAF50;">Your Question Responses</h2>
                <table style="width: 100%; border-collapse: collapse; margin: 10px 0;">
                    <tr style="background: #f0f0f0;">
                        <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">Question</th>
                        <th style="padding: 8px; border: 1px solid #ddd; text-align: center;">Dimension</th>
                        <th style="padding: 8px; border: 1px solid #ddd; text-align: center;">Your Response</th>
                    </tr>
            """

            for resp in responses_data:
                responses_table_html += f"""
                    <tr id="Q{resp['id']}">
                        <td style="padding: 8px; border: 1px solid #ddd;"><strong>Q{resp['id']}:</strong> {resp['text']}</td>
                        <td style="padding: 8px; border: 1px solid #ddd; text-align: center;">{resp['dimension']}</td>
                        <td style="padding: 8px; border: 1px solid #ddd; text-align: center;"><strong>{resp['response']}</strong></td>
                    </tr>
                """

            responses_table_html += """
                </table>
            </div>
            """

            # Create HTML report sections
            report_sections_html = f"""
            <div style="font-family: Arial, sans-serif; line-height: 1.6;">
                <div style="text-align: center; margin-bottom: 30px;">
                    <h1>Your Personality Analysis</h1>
                    {str(type_badge) if type_badge else f'<div style="background: #4CAF50; color: white; padding: 10px 20px; border-radius: 5px; display: inline-block;">{mbti_type}</div>'}
                    {f'<p><em>{type_desc.text}</em></p>' if type_desc else ''}
                </div>
                
                {responses_table_html}
                
                {strengths_html}
                {weaknesses_html}
                {careers_html}
                
                <div style="margin: 20px 0;">
                    <h2 style="color: #333; border-bottom: 2px solid #4CAF50;">Traditional Dimension Scores</h2>
                    <ul>
            """

            pairs = [('E', 'I'), ('S', 'N'), ('T', 'F'), ('J', 'P')]
            for dim1, dim2 in pairs:
                score1 = scores.get(f'{dim1}_score', 0.5)
                score2 = scores.get(f'{dim2}_score', 0.5)
                stronger = dim1 if score1 > score2 else dim2
                percentage = max(score1, score2) * 100
                report_sections_html += f"<li><strong>{dim1}/{dim2}</strong>: {stronger} ({percentage:.1f}%)</li>"

            report_sections_html += """
                    </ul>
                </div>
            </div>
            """

            # Format AI analysis as markdown
            ai_analysis_md = f"""
## 🧠 AI Analysis

{llm_analysis_text}

---
*Complete questionnaire and report saved via PocketFlow pipeline*
            """

            return report_sections_html, ai_analysis_md, gr.update(visible=True)

        except Exception as e:
            error_msg = f"Error in PocketFlow analysis: {e}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            return error_msg, "", gr.update(visible=False)

    def load_questionnaire_file(self, file):
        """Load questionnaire from uploaded file"""
        if file is None:
            return "No file uploaded.", 0, self.get_question_text(0), 3

        try:
            with open(file.name, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if 'questionnaire' in data and 'responses' in data['questionnaire']:
                # Load both questions and responses
                if 'questions' in data['questionnaire']:
                    self.questions = data['questionnaire']['questions']

                self.responses = data['questionnaire']['responses']
                # Convert string keys to int keys
                self.responses = {int(k): v for k, v in self.responses.items()}

                # Start from first question
                question_text = self.get_question_text(0)
                current_response = self.get_current_response(0)

                return f"Loaded questionnaire with {len(self.responses)} responses.", 0, question_text, current_response
            else:
                return "Invalid questionnaire file format.", 0, self.get_question_text(0), 3

        except Exception as e:
            return f"Error loading file: {e}", 0, self.get_question_text(0), 3

    def reset_questionnaire(self):
        """Reset questionnaire to start over"""
        self.responses = {}
        self.shared = None
        self.last_report_path = None
        return "", 0, self.get_question_text(0), 3, gr.update(visible=False), "", "", gr.update(
            interactive=False), gr.update(interactive=True), gr.update(visible=False)


def create_pocketflow_gradio_app():
    """Create PocketFlow Gradio interface"""
    app = MBTIPocketFlowApp()

    with gr.Blocks(title="MBTI Questionnaire - PocketFlow with LLM") as demo:
        gr.Markdown("# MBTI Personality Questionnaire (PocketFlow + LLM)")
        gr.Markdown("Powered by PocketFlow architecture with complete node pipeline and AI analysis")

        # Questionnaire length selection
        with gr.Row():
            length_radio = gr.Radio(
                choices=[20, 40, 60],
                value=20,
                label="Questionnaire Length",
                info="Choose the number of questions (more questions = more accurate results)"
            )

        # File upload section
        upload_file = gr.File(label="Load Previous Questionnaire (JSON)", file_types=[".json"])
        load_status = gr.Textbox(label="Load Status", interactive=False)

        # Question section
        question_idx = gr.State(0)
        question_text = gr.Textbox(
            label="Question",
            value=app.get_question_text(0),
            interactive=False
        )

        with gr.Row():
            response_slider = gr.Slider(
                minimum=1, maximum=5, step=1, value=3,
                label="Your Response (1=Strongly Disagree, 5=Strongly Agree)"
            )

        # Navigation buttons
        with gr.Row():
            prev_btn = gr.Button("← Previous", interactive=False)
            next_btn = gr.Button("Next →")

        # Export and control buttons
        with gr.Row():
            export_btn = gr.Button("💾 Export Current Progress", variant="secondary")
            reset_btn = gr.Button("Reset Questionnaire")

        # Hidden download button
        export_download_btn = gr.DownloadButton(visible=False, elem_id="export_download_btn")

        # Analysis section
        with gr.Column(visible=False) as analyze_section:
            analyze_btn = gr.Button("🧠 Analyze with PocketFlow + LLM", variant="primary")
            analysis_status = gr.Markdown("*This will run the complete PocketFlow pipeline with AI analysis*")

        # Results section
        with gr.Column(visible=False) as results_section:
            report_display = gr.HTML()
            ai_analysis_display = gr.Markdown()

            # Download report button
            download_report_btn = gr.Button("📊 Download Report", visible=False)

        # Hidden download button for report
        download_report_hidden = gr.DownloadButton(visible=False, elem_id="download_report_hidden")

        # Event handlers
        length_radio.change(
            app.change_questionnaire_length,
            inputs=[length_radio],
            outputs=[question_idx, question_text, response_slider, analyze_section]
        )

        upload_file.upload(
            app.load_questionnaire_file,
            inputs=[upload_file],
            outputs=[load_status, question_idx, question_text, response_slider]
        )

        prev_btn.click(
            lambda idx, resp: app.navigate_question(idx, "prev", resp),
            inputs=[question_idx, response_slider],
            outputs=[question_idx, question_text, response_slider, prev_btn, next_btn, analyze_section]
        )

        next_btn.click(
            lambda idx, resp: app.navigate_question(idx, "next", resp),
            inputs=[question_idx, response_slider],
            outputs=[question_idx, question_text, response_slider, prev_btn, next_btn, analyze_section]
        )

        # Export current progress
        def export_handler(idx, resp):
            # Save current response and create file
            file_path = app.save_current_questionnaire(idx, resp)
            print(f"DEBUG: Export file path: {file_path}")
            return file_path if file_path else None

        export_btn.click(
            export_handler,
            inputs=[question_idx, response_slider],
            outputs=[export_download_btn]
        ).then(
            fn=None,
            inputs=None,
            outputs=None,
            js="() => document.querySelector('#export_download_btn').click()"
        )

        analyze_btn.click(
            lambda: (gr.update(interactive=False, value="⏳ Analyzing..."),
                     "🔄 **Running PocketFlow analysis with LLM... This may take a moment.**"),
            outputs=[analyze_btn, analysis_status]
        ).then(
            app.run_pocketflow_analysis_with_save,
            inputs=[question_idx, response_slider],
            outputs=[report_display, ai_analysis_display, download_report_btn]
        ).then(
            lambda: (gr.update(visible=True), gr.update(interactive=True, value="🧠 Analyze with PocketFlow + LLM"),
                     "✅ **Analysis complete!**"),
            outputs=[results_section, analyze_btn, analysis_status]
        )

        # Download report
        download_report_btn.click(
            lambda: app.last_report_path if app.last_report_path else None,
            outputs=[download_report_hidden]
        ).then(
            fn=None,
            inputs=None,
            outputs=None,
            js="() => document.querySelector('#download_report_hidden').click()"
        )

        # Auto-save when slider changes and check for analysis button
        response_slider.change(
            app.save_slider_response,
            inputs=[question_idx, response_slider],
            outputs=[analyze_section]
        )

        reset_btn.click(
            app.reset_questionnaire,
            outputs=[load_status, question_idx, question_text, response_slider, analyze_section, report_display,
                     prev_btn, next_btn, download_report_btn]
        ).then(
            lambda: gr.update(visible=False),
            outputs=[results_section]
        )

    return demo


if __name__ == "__main__":
    demo = create_pocketflow_gradio_app()
    demo.launch(ssr_mode=False)
