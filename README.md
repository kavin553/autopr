# AutoPR — Multi-Agent GitHub Contribution Assistant

Live demo: https://autopr.onrender.com
*(Free tier — first load may take 30-60s to wake up)*

## What it does
AutoPR helps open-source contributors find the right issue, understand the
codebase context, and draft a ready-to-paste PR — using 3 coordinated AI agents.

1. **Scanner** — finds open, unassigned issues and ranks them by fit to your skills
2. **Analyst** — reads the repo's file structure and drafts a change plan
3. **Drafter** — writes a PR title + description, ready for you to review and submit

## Why this is different
Existing tools either help you find issues (GitPulse, DevMatch) or review PRs
after they're written (PR-Agent). AutoPR is the only one that chains find →
understand → draft into one pipeline — and it never auto-submits; every output
is a draft for you to review first.

## Tech stack
- **Agents**: CrewAI, orchestrating 3 specialized roles
- **LLM**: Groq (Llama 3.3 70B) — free tier
- **Backend**: FastAPI
- **UI**: Gradio
- **Deployment**: Render (free tier)
- **GitHub integration**: PyGithub

## Run it locally
\`\`\`
pip install -r requirements.txt
# Add GITHUB_TOKEN and GROQ_API_KEY to a .env file
python app.py
\`\`\`

## What's next
- React frontend with live agent-progress streaming
- Supabase-backed scan history and accounts
- Scheduled daily scans via GitHub Actions