"""
Full pipeline: Scanner -> Analyst -> Drafter, chained automatically.
Takes a repo + skills, picks the top-ranked issue, analyzes it, and drafts a PR.
"""
import logging
import re

from backend.agents.scanner_agent import scan_repository
from backend.agents.analyst_agent import analyze_issue
from backend.agents.drafter_agent import draft_pr

logger = logging.getLogger("autopr.pipeline")


def extract_top_issue_number(scan_result: str) -> int | None:
    """
    Pulls the first issue number (e.g. '#37043') out of the scanner's ranked-list text.
    This is a simple, honest parser — it doesn't invent a number if it can't find one.
    """
    match = re.search(r"#(\d+)", scan_result)
    return int(match.group(1)) if match else None


def run_full_pipeline(repo_full_name: str, skills: list[str]) -> dict:
    logger.info("Starting full pipeline for %s", repo_full_name)

    scan_result = scan_repository(repo_full_name, skills)
    top_issue_number = extract_top_issue_number(str(scan_result))

    if top_issue_number is None:
        return {
            "scan_result": str(scan_result),
            "top_issue_number": None,
            "change_plan": None,
            "pr_draft": None,
            "error": "Could not identify a top-ranked issue number from the scan result.",
        }

    change_plan = analyze_issue(repo_full_name, top_issue_number)
    pr_draft = draft_pr(repo_full_name, top_issue_number, str(change_plan))

    return {
        "scan_result": str(scan_result),
        "top_issue_number": top_issue_number,
        "change_plan": str(change_plan),
        "pr_draft": str(pr_draft),
        "error": None,
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