"""
Agent 2 — reads a repo's file structure and drafts a change plan for a specific issue.
v1: reasons over file *paths* only (no file contents yet) — upgraded later with
semantic search once the core pipeline is proven.
"""
import logging
from crewai import Agent, Task, Crew, LLM

from backend.core.config import settings
from backend.integrations.github_client import fetch_issue, fetch_repo_file_tree, GitHubClientError

logger = logging.getLogger("autopr.analyst")


def build_analyst_llm() -> LLM:
    return LLM(model=settings.groq_model, api_key=settings.groq_api_key)


def build_analyst_agent() -> Agent:
    return Agent(
        role="Codebase Analyst",
        goal="Read a repo's structure and an issue's description, then draft a clear, actionable change plan.",
        backstory=(
            "You are a senior engineer skilled at quickly orienting yourself in unfamiliar codebases "
            "and identifying exactly where a fix belongs before writing any code."
        ),
        llm=build_analyst_llm(),
        verbose=True,
    )


def build_analyst_task(agent: Agent, issue, file_paths: list[str]) -> Task:
    tree_text = "\n".join(file_paths)
    return Task(
        description=(
            f"Issue #{issue.number}: {issue.title}\n\n"
            f"Description:\n{issue.body_snippet}\n\n"
            f"Repository file structure (paths only):\n{tree_text}\n\n"
            "Based on the file structure and the issue description, produce a change plan with:\n"
            "1. Likely file(s) where this fix belongs (best guesses from the paths above, with reasoning)\n"
            "2. A short, numbered plan of what needs to change\n"
            "3. Any risks (e.g. shared components, likely test files to update)\n"
            "Do not invent files that aren't in the list above."
        ),
        expected_output="A structured change plan: likely files, numbered steps, and risk flags.",
        agent=agent,
    )


def analyze_issue(repo_full_name: str, issue_number: int) -> str:
    try:
        issue = fetch_issue(repo_full_name, issue_number)
        file_paths = fetch_repo_file_tree(repo_full_name)
    except GitHubClientError as e:
        logger.error(str(e))
        return f"Analysis failed: {e}"

    agent = build_analyst_agent()
    task = build_analyst_task(agent, issue, file_paths)
    crew = Crew(agents=[agent], tasks=[task], verbose=True, tracing=False)

    logger.info("Analyzing issue #%s in %s (%d files in tree)", issue_number, repo_full_name, len(file_paths))
    return crew.kickoff()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    repo = input("Repo (owner/repo): ").strip() or "your-username/your-repo"
    issue_num = input("Issue number (from your scan results): ").strip()

    print(analyze_issue(repo, int(issue_num)))