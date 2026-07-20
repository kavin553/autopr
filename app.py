"""
Combined entrypoint for deployment (Render) — calls the pipeline directly.
"""
import os
import gradio as gr
from backend.agents.crew import run_full_pipeline


def run_autopr(repo_full_name: str, skills_text: str):
    if not repo_full_name.strip():
        return "Please enter a repo (e.g. owner/repo-name).", "", ""

    skills = [s.strip() for s in skills_text.split(",") if s.strip()]
    if not skills:
        skills = ["Python"]

    result = run_full_pipeline(repo_full_name.strip(), skills)

    if result.get("error"):
        return f"Pipeline error: {result['error']}", "", ""

    return str(result["scan_result"]), str(result["change_plan"] or ""), str(result["pr_draft"] or "")


with gr.Blocks(title="AutoPR — GitHub Contribution Assistant") as demo:
    gr.Markdown("# AutoPR\nFind the right open-source issue, get a change plan, and a ready-to-paste PR draft.")

    with gr.Row():
        repo_input = gr.Textbox(label="Repo (owner/repo)", placeholder="gradio-app/gradio")
        skills_input = gr.Textbox(label="Your skills (comma-separated)", placeholder="Python, React, CSS")

    run_button = gr.Button("Run AutoPR", variant="primary")

    with gr.Tab("Ranked Issues"):
        scan_output = gr.Markdown()
    with gr.Tab("Change Plan"):
        plan_output = gr.Markdown()
    with gr.Tab("PR Draft"):
        pr_output = gr.Markdown()

    run_button.click(fn=run_autopr, inputs=[repo_input, skills_input], outputs=[scan_output, plan_output, pr_output])

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=int(os.environ.get("PORT", 7860)))