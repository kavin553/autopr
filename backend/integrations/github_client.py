"""
GitHub API integration for AutoPR.
"""
import logging
from dataclasses import dataclass
from github import Github, Auth, GithubException

from backend.core.config import settings

logger = logging.getLogger("autopr.github")


class GitHubClientError(Exception):
    """Raised when a GitHub API call fails in a way callers need to handle."""


@dataclass
class Issue:
    number: int
    title: str
    url: str
    labels: list[str]
    body_snippet: str


def get_github_client() -> Github:
    auth = Auth.Token(settings.github_token)
    return Github(auth=auth)


def fetch_open_issues(repo_full_name: str, max_issues: int = 15) -> list[Issue]:
    """Fetch open, unassigned issues from a repo (e.g. 'octocat/Hello-World')."""
    gh = get_github_client()
    try:
        repo = gh.get_repo(repo_full_name)
        raw_issues = repo.get_issues(state="open")
    except GithubException as e:
        logger.error("GitHub API error for %s: %s", repo_full_name, e)
        raise GitHubClientError(
            f"Could not fetch issues for '{repo_full_name}' (status: {e.status})."
        ) from e

    results: list[Issue] = []
    for issue in raw_issues:
        if issue.pull_request is not None:
            continue
        if issue.assignee is not None:
            continue

        results.append(Issue(
            number=issue.number,
            title=issue.title,
            url=issue.html_url,
            labels=[label.name for label in issue.labels],
            body_snippet=(issue.body or "")[:400],
        ))
        if len(results) >= max_issues:
            break

    logger.info("Fetched %d eligible issues from %s", len(results), repo_full_name)
    return results


def fetch_issue(repo_full_name: str, issue_number: int) -> Issue:
    """Fetch a single issue by number."""
    gh = get_github_client()
    try:
        repo = gh.get_repo(repo_full_name)
        issue = repo.get_issue(issue_number)
    except GithubException as e:
        logger.error("GitHub API error fetching issue #%s: %s", issue_number, e)
        raise GitHubClientError(
            f"Could not fetch issue #{issue_number} from '{repo_full_name}' (status: {e.status})."
        ) from e

    return Issue(
        number=issue.number,
        title=issue.title,
        url=issue.html_url,
        labels=[label.name for label in issue.labels],
        body_snippet=(issue.body or "")[:1500],
    )


def fetch_repo_file_tree(repo_full_name: str, max_paths: int = 200) -> list[str]:
    """Fetch the repo's file paths (not content) for the analyst agent to reason over."""
    gh = get_github_client()
    try:
        repo = gh.get_repo(repo_full_name)
        tree = repo.get_git_tree(sha=repo.default_branch, recursive=True)
    except GithubException as e:
        logger.error("GitHub API error fetching file tree for %s: %s", repo_full_name, e)
        raise GitHubClientError(
            f"Could not fetch file tree for '{repo_full_name}' (status: {e.status})."
        ) from e

    paths = [item.path for item in tree.tree if item.type == "blob"]
    logger.info("Fetched %d file paths (showing up to %d) from %s", len(paths), max_paths, repo_full_name)
    return paths[:max_paths]