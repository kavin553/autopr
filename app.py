"""
Combined entrypoint for deployment (Render) — calls the pipeline directly.
"""
import os
import gradio as gr
from backend.agents.crew import run_full_pipeline


def build_status_html(message: str, detail: str) -> str:
    return f"""
    <div style="padding: 16px 18px; border-radius: 14px; background: linear-gradient(135deg, #eff6ff, #f8fafc); border: 1px solid #dbeafe; box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);">
      <div style="display: flex; align-items: center; gap: 12px;">
        <div style="width: 14px; height: 14px; border: 3px solid #bfdbfe; border-top-color: #2563eb; border-radius: 50%; animation: spin 0.9s linear infinite;"></div>
        <div>
          <div style="font-weight: 700; color: #0f172a;">{message}</div>
          <div style="font-size: 0.95rem; color: #475569; margin-top: 2px;">{detail}</div>
        </div>
      </div>
    </div>
    <style>
      @keyframes spin {{ from {{ transform: rotate(0deg); }} to {{ transform: rotate(360deg); }} }}
    </style>
    """


def format_scan_output(repo_full_name: str, skills: list[str], result: dict) -> str:
    skill_text = ", ".join(skills) if skills else "General software engineering"
    scan_result = str(result.get("scan_result") or "No scan output available.")
    header = f"# Repository Analysis\n\nRepository: {repo_full_name}\n\nSkills: {skill_text}\n\n---\n\n"
    if result.get("top_issue_number"):
        return header + f"## Best Matching Issue\n\nIssue #{result['top_issue_number']}\n\n{scan_result}"
    return header + f"## Scan Summary\n\n{scan_result}"


def format_change_plan_output(repo_full_name: str, skills: list[str], result: dict) -> str:
    skill_text = ", ".join(skills) if skills else "General software engineering"
    change_plan = str(result.get("change_plan") or "No change plan available.")
    return f"# Change Plan\n\nRepository: {repo_full_name}\n\nSkills: {skill_text}\n\n---\n\n{change_plan}"


def format_pr_output(repo_full_name: str, skills: list[str], result: dict) -> str:
    skill_text = ", ".join(skills) if skills else "General software engineering"
    pr_draft = str(result.get("pr_draft") or "No PR draft available.")
    return f"# Pull Request Draft\n\nRepository: {repo_full_name}\n\nSkills: {skill_text}\n\n---\n\n{pr_draft}"


def run_autopr(repo_full_name: str, skills_text: str, progress=gr.Progress()):
    if not repo_full_name.strip():
        return build_status_html("Please add a repository", "Use the format owner/repo to get started."), "", "", ""

    skills = [s.strip() for s in skills_text.split(",") if s.strip()]
    if not skills:
        skills = ["Python"]

    repo_name = repo_full_name.strip()

    def update_status(message: str, detail: str):
        progress(0.1, desc=message)

    result = run_full_pipeline(repo_name, skills, status_callback=update_status)

    status_message = "✨ Workflow complete" if not result.get("error") else "⚠️ Workflow completed with a friendly warning"
    status_detail = result.get("status", "Completed")
    status_html = build_status_html(status_message, status_detail)

    scan_output = format_scan_output(repo_name, skills, result)
    plan_output = format_change_plan_output(repo_name, skills, result)
    pr_output = format_pr_output(repo_name, skills, result)

    return status_html, scan_output, plan_output, pr_output


with gr.Blocks(title="AutoPR — GitHub Contribution Assistant") as demo:
    gr.Markdown("# AutoPR\nFind the right open-source issue, get a change plan, and a ready-to-paste PR draft.")

    with gr.Row():
        repo_input = gr.Textbox(label="Repo (owner/repo)", placeholder="gradio-app/gradio")
        skills_input = gr.Textbox(label="Your skills (comma-separated)", placeholder="Python, React, CSS")

    run_button = gr.Button("Run AutoPR", variant="primary")

    status_output = gr.HTML(value=build_status_html("Ready to analyze", "Enter a repository and your skills to begin."))

    with gr.Tab("Ranked Issues"):
        scan_output = gr.Markdown()
    with gr.Tab("Change Plan"):
        plan_output = gr.Markdown()
    with gr.Tab("PR Draft"):
        pr_output = gr.Markdown()

    run_button.click(
        fn=run_autopr,
        inputs=[repo_input, skills_input],
        outputs=[status_output, scan_output, plan_output, pr_output],
    )

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=int(os.environ.get("PORT", 7860)))