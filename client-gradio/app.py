"""
AutoPR's fast-path public UI — calls the FastAPI backend's /analyze endpoint.
"""
import gradio as gr
import requests

# While developing locally, this points at your local FastAPI server.
# Once deployed (Step 10), this changes to your deployed backend's URL.
API_URL = "http://127.0.0.1:8000/analyze"


def run_autopr(repo_full_name: str, skills_text: str):
    if not repo_full_name.strip():
        return "Please enter a repo (e.g. owner/repo-name).", "", ""

    skills = [s.strip() for s in skills_text.split(",") if s.strip()]
    if not skills:
        skills = ["Python"]

    try:
        response = requests.post(
            API_URL,
            json={"repo_full_name": repo_full_name.strip(), "skills": skills},
            timeout=180,
        )
    except requests.exceptions.RequestException as e:
        return f"Request failed: {e}", "", ""

    if response.status_code != 200:
        # Show FastAPI's actual error detail instead of a generic message
        try:
            detail = response.json().get("detail", response.text)
        except ValueError:
            detail = response.text
        return f"Backend error ({response.status_code}): {detail}", "", ""

    data = response.json()

    if data.get("error"):
        return f"Pipeline error: {data['error']}", "", ""

    return data["scan_result"], data["change_plan"] or "", data["pr_draft"] or ""
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

    run_button.click(
        fn=run_autopr,
        inputs=[repo_input, skills_input],
        outputs=[scan_output, plan_output, pr_output],
    )

if __name__ == "__main__":
    demo.launch()