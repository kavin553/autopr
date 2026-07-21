import logging
import os
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, LLM

from backend.integrations.github_client import fetch_open_issues, GitHubClientError

load_dotenv()

logger = logging.getLogger("autopr.scanner")


def build_scanner_llm():
    return LLM(model="groq/llama-3.3-70b-versatile", api_key=os.getenv("GROQ_API_KEY"))


def expand_skills(skills: list[str]) -> list[str]:
    """Expand a user's skill list into related technologies and adjacent domains."""
    aliases = {
        "react": {"React", "Frontend", "JavaScript", "TypeScript", "Web"},
        "python": {"Python", "Backend", "Automation", "Machine Learning", "AI", "Scripting"},
        "css": {"CSS", "Frontend", "UI", "Animations", "Design"},
        "javascript": {"JavaScript", "Frontend", "Web", "TypeScript", "React"},
        "typescript": {"TypeScript", "JavaScript", "Frontend", "React", "Web"},
        "html": {"HTML", "Frontend", "Web", "UI"},
        "frontend": {"Frontend", "UI", "React", "JavaScript", "CSS"},
        "backend": {"Backend", "Python", "APIs", "Automation", "Database"},
        "automation": {"Automation", "Python", "Backend", "DevOps", "Scripts"},
        "ai": {"AI", "Machine Learning", "Python", "Automation", "Data"},
        "machine learning": {"Machine Learning", "AI", "Python", "Data", "Automation"},
        "animation": {"Animations", "CSS", "Frontend", "UI"},
        "ui": {"UI", "Frontend", "CSS", "Design"},
        "ml": {"Machine Learning", "AI", "Python", "Data"},
        "data": {"Data", "Machine Learning", "AI", "Python"},
        "devops": {"DevOps", "Automation", "Cloud", "Infrastructure"},
        "api": {"APIs", "Backend", "Python", "JavaScript"},
        "database": {"Database", "Backend", "Data", "APIs"},
    }

    expanded: list[str] = []
    for skill in skills or []:
        text = (skill or "").strip()
        if not text:
            continue

        expanded.append(text)
        lowered = text.lower()
        for key, values in aliases.items():
            if key in lowered:
                expanded.extend(values)

        if not any(key in lowered for key in aliases):
            expanded.append(text.title())

    seen = set()
    ordered: list[str] = []
    for item in expanded:
        normalized = item.strip()
        if not normalized:
            continue
        identifier = normalized.lower()
        if identifier in seen:
            continue
        seen.add(identifier)
        ordered.append(normalized)

    return ordered


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
    skill_context = ", ".join(expand_skills(skills))
    return Task(
        description=(
            f"Contributor's skills: {skill_context}.\n\n"
            f"Open issues:\n{issues_text}\n\n"
            "Rank the top 5 by realistic fit. For each: issue number, fit score /10, one-line reason. "
            "Use the skill context broadly and match related technologies, adjacent domains, and real-world experience. "
            "Do not invent issues not listed above."
        ),
        expected_output="A numbered list of up to 5 issues with issue number, fit score /10, and reason.",
        agent=agent,
    )


def scan_repository(repo_full_name: str, skills: list[str]):
    skill_list = [s for s in (skills or []) if s and s.strip()]
    if not skill_list:
        skill_list = ["Python"]

    try:
        issues = fetch_open_issues(repo_full_name)
    except GitHubClientError as exc:
        logger.warning("Unable to scan repository %s: %s", repo_full_name, exc)
        return f"Repository scan could not be completed. {exc}"
    except Exception:
        logger.exception("Unexpected error while fetching issues for %s", repo_full_name)
        return "Repository scan could not be completed right now. Please try again in a moment."

    if not issues:
        return "No open, unassigned issues found right now. I can still suggest useful contribution areas, documentation improvements, testing opportunities, and feature ideas for this repository."

    try:
        agent = build_scanner_agent()
        task = build_scanner_task(agent, issues, skill_list)
        crew = Crew(agents=[agent], tasks=[task], verbose=True, tracing=False)
        return crew.kickoff()
    except Exception:
        logger.exception("Scanner crew failed for %s", repo_full_name)
        return "The issue-ranking step hit an unexpected issue, but the workflow can still continue with helpful fallback guidance."


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)

    repo = input("Repo (owner/repo): ").strip() or "your-username/your-repo"
    skills_input = input("Your skills (comma-separated): ").strip()
    skills = [s.strip() for s in skills_input.split(",")] if skills_input else ["Python"]

    print(scan_repository(repo, skills))