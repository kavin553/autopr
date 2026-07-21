"""
Full pipeline: Scanner -> Analyst -> Drafter, chained automatically.
Takes a repo + skills, picks the top-ranked issue, analyzes it, and drafts a PR.
"""
import logging
import re
from typing import Callable

from backend.agents.scanner_agent import scan_repository
from backend.agents.analyst_agent import analyze_issue
from backend.agents.drafter_agent import draft_pr

logger = logging.getLogger("autopr.pipeline")


def extract_top_issue_number(scan_result: str) -> int | None:
    """Pull the first issue number from a scan result when one is clearly present."""
    if not scan_result:
        return None
    match = re.search(r"#(\d+)", str(scan_result))
    return int(match.group(1)) if match else None


def build_fallback_scan_result(repo_full_name: str, skills: list[str], scan_result: str) -> str:
    skill_text = ", ".join(skills) if skills else "General software engineering"
    return f"""# Scan Results

Repository analyzed: {repo_full_name}

Skills received: {skill_text}

## Explanation
{scan_result or 'No strong issue match could be identified from the available signals.'}

## Suggestions
- Review recent issues related to documentation, tests, and developer experience.
- Prioritize a small, well-scoped fix that can be validated quickly.
- Consider a contribution area that aligns with your strongest skills.

## Next actions
1. Review the repository's open issues manually.
2. Choose a task that feels approachable and valuable.
3. Draft a change plan once a target issue is confirmed.
"""


def build_fallback_change_plan(repo_full_name: str, skills: list[str]) -> str:
    skill_text = ", ".join(skills) if skills else "General software engineering"
    return f"""# Change Plan

Repository: {repo_full_name}

Skills: {skill_text}

## Recommended contribution areas
- Documentation improvements
- Testing improvements
- Feature ideas
- Developer experience polish

## Suggested next step
Pick one low-risk area and validate whether the repository already has related issues or TODOs.
"""


def build_fallback_pr_draft(repo_full_name: str, skills: list[str]) -> str:
    skill_text = ", ".join(skills) if skills else "General software engineering"
    return f"""# Pull Request Draft

Repository: {repo_full_name}

Skills: {skill_text}

## Suggested PR summary
No issue was matched strongly enough to generate a precise implementation draft, so this fallback recommends a small, well-scoped contribution instead.

## Suggested title
chore: improve repository contribution readiness
"""


def run_full_pipeline(
    repo_full_name: str,
    skills: list[str],
    status_callback: Callable[[str, str], None] | None = None,
) -> dict:
    logger.info("Starting full pipeline for %s", repo_full_name)

    skill_list = [s for s in (skills or []) if s and s.strip()]
    if not skill_list:
        skill_list = ["Python"]

    if status_callback:
        status_callback("🔍 Scanning repository...", "Gathering open issues and matching them with your skills.")
    scan_result = scan_repository(repo_full_name, skill_list)

    top_issue_number = extract_top_issue_number(str(scan_result))
    if top_issue_number is None:
        if status_callback:
            status_callback("🧭 No strong issue match", "Preparing a graceful fallback with recommendations and next steps.")
        fallback_scan = build_fallback_scan_result(repo_full_name, skill_list, str(scan_result))
        return {
            "scan_result": fallback_scan,
            "top_issue_number": None,
            "change_plan": build_fallback_change_plan(repo_full_name, skill_list),
            "pr_draft": build_fallback_pr_draft(repo_full_name, skill_list),
            "error": None,
            "status": "fallback",
        }

    if status_callback:
        status_callback("📋 Creating change plan...", "Analyzing the repository structure around the selected issue.")
    try:
        change_plan = analyze_issue(repo_full_name, top_issue_number)
    except Exception as exc:
        logger.exception("Analyst step failed for issue #%s", top_issue_number)
        change_plan = f"Analysis could not be completed. {exc}"

    if status_callback:
        status_callback("✨ Drafting PR...", "Preparing a professional PR summary for the selected issue.")
    try:
        pr_draft = draft_pr(repo_full_name, top_issue_number, str(change_plan))
    except Exception as exc:
        logger.exception("Drafter step failed for issue #%s", top_issue_number)
        pr_draft = f"PR draft could not be completed. {exc}"

    return {
        "scan_result": str(scan_result),
        "top_issue_number": top_issue_number,
        "change_plan": str(change_plan),
        "pr_draft": str(pr_draft),
        "error": None,
        "status": "matched",
    }

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    repo = input("Repo (owner/repo): ").strip() or "your-username/your-repo"
    skills_input = input("Your skills (comma-separated): ").strip()
    skills = [s.strip() for s in skills_input.split(",")] if skills_input else ["Python"]

    result = run_full_pipeline(repo, skills)

    print("\n" + "=" * 60)
    print("SCAN RESULT")
    print("=" * 60)
    print(result["scan_result"])

    if result["error"]:
        print("\nPipeline stopped:", result["error"])
    else:
        print("\n" + "=" * 60)
        print(f"CHANGE PLAN (issue #{result['top_issue_number']})")
        print("=" * 60)
        print(result["change_plan"])

        print("\n" + "=" * 60)
        print("PR DRAFT")
        print("=" * 60)
        print(result["pr_draft"])