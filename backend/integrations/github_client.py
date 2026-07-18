import os
from github import Github, Auth

def get_github_client():
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise ValueError("GITHUB_TOKEN not found. Check your .env file.")
    auth = Auth.Token(token)
    return Github(auth=auth)

def fetch_open_issues(repo_full_name: str, max_issues: int = 15):
    """repo_full_name example: 'octocat/Hello-World'"""
    gh = get_github_client()
    repo = gh.get_repo(repo_full_name)
    issues = repo.get_issues(state="open")

    results = []
    for issue in issues:
        if issue.pull_request is not None:
            continue  # GitHub lists PRs as issues too — skip them
        if issue.assignee is not None:
            continue  # skip issues someone's already on

        results.append({
            "number": issue.number,
            "title": issue.title,
            "url": issue.html_url,
            "labels": [label.name for label in issue.labels],
            "body_snippet": (issue.body or "")[:400],
        })
        if len(results) >= max_issues:
            break

    return results