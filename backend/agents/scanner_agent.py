import os
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, LLM

from backend.integrations.github_client import fetch_open_issues

load_dotenv()

def build_scanner_llm():
    return LLM(model="groq/llama-3.3-70b-versatile", api_key=os.getenv("GROQ_API_KEY"))

def build_scanner_agent():
    return Agent(
        role="Open Source Issue Scanner",
        goal="Find open GitHub issues that genuinely fit a contributor's real skills, and explain why.",
        backstory=(
            "You are an experienced open-source maintainer who has reviewed thousands of issues "
            "and is excellent at matching contributors to the right first task."
        ),
        llm=build_scanner_llm(),
        verbose=True,
    )

def build_scanner_task(agent, issues, skills):
    issues_text = "\n".join(
        f"- #{i.number}: {i.title} (labels: {', '.join(i.labels) or 'none'})\n  {i.body_snippet}"
        for i in issues
    )
    return Task(
        description=(
            f"Contributor's skills: {', '.join(skills)}.\n\n"
            f"Open issues:\n{issues_text}\n\n"
            "Rank the top 5 by realistic fit. For each: issue number, fit score /10, one-line reason. "
            "Do not invent issues not listed above."
        ),
        expected_output="A numbered list of up to 5 issues with issue number, fit score /10, and reason.",
        agent=agent,
    )

def scan_repository(repo_full_name: str, skills: list[str]):
    issues = fetch_open_issues(repo_full_name)
    if not issues:
        return "No open, unassigned issues found right now."

    agent = build_scanner_agent()
    task = build_scanner_task(agent, issues, skills)
    crew = Crew(agents=[agent], tasks=[task], verbose=True, tracing=False)
    return crew.kickoff()


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)

    repo = input("Repo (owner/repo): ").strip() or "your-username/your-repo"
    skills_input = input("Your skills (comma-separated): ").strip()
    skills = [s.strip() for s in skills_input.split(",")] if skills_input else ["Python"]

    print(scan_repository(repo, skills))