"""
Agent 3 — takes an issue and a change plan (from Agent 2) and drafts a
ready-to-paste PR title + description, in the format real maintainers expect.
"""
import logging
from crewai import Agent, Task, Crew, LLM

from backend.core.config import settings
from backend.integrations.github_client import fetch_issue, GitHubClientError

logger = logging.getLogger("autopr.drafter")


def build_drafter_llm() -> LLM:
    return LLM(model=settings.groq_model, api_key=settings.groq_api_key)


def build_drafter_agent() -> Agent:
    return Agent(
        role="PR Description Drafter",
        goal="Turn an issue and a change plan into a clear, professional, ready-to-paste PR title and description.",
        backstory=(
            "You are an experienced open-source contributor known for writing PR descriptions "
            "that maintainers can review quickly — clear on what changed, why, and how it was tested."
        ),
        llm=build_drafter_llm(),
        verbose=True,
    )


def build_drafter_task(agent: Agent, issue, change_plan: str) -> Task:
    return Task(
        description=(
            f"Issue #{issue.number}: {issue.title}\n"
            f"Issue link: {issue.url}\n\n"
            f"Change plan from the codebase analysis:\n{change_plan}\n\n"
            "Write a PR title and description ready to paste into GitHub. Include:\n"
            "1. A concise, conventional-commit-style title (e.g. 'fix: ...' or 'feat: ...')\n"
            "2. A 'What changed' section\n"
            "3. A 'Why' section referencing the issue\n"
            "4. A 'How this was tested' section (write it as a placeholder the contributor "
            "   should fill in with their real testing steps — do not invent test results)\n"
            f"5. A closing line: 'Closes #{issue.number}'\n"
            "Do not fabricate any results, benchmarks, or claims that aren't in the change plan."
        ),
        expected_output="A PR title and a formatted PR description, ready to paste into GitHub.",
        agent=agent,
    )


def draft_pr(repo_full_name: str, issue_number: int, change_plan: str) -> str:
    try:
        issue = fetch_issue(repo_full_name, issue_number)
    except GitHubClientError as e:
        logger.error(str(e))
        return f"Drafting failed: {e}"

    agent = build_drafter_agent()
    task = build_drafter_task(agent, issue, change_plan)
    crew = Crew(agents=[agent], tasks=[task], verbose=True, tracing=False)

    logger.info("Drafting PR for issue #%s in %s", issue_number, repo_full_name)
    return crew.kickoff()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    repo = input("Repo (owner/repo): ").strip() or "your-username/your-repo"
    issue_num = input("Issue number: ").strip()
    print("Paste the change plan from Agent 2 (finish with an empty line):")
    lines = []
    while True:
        line = input()
        if line == "":
            break
        lines.append(line)
    change_plan_text = "\n".join(lines)

    print(draft_pr(repo, int(issue_num), change_plan_text))