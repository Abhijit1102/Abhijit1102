#!/usr/bin/env python3
"""
generate_stats.py

Pulls live stats for a GitHub user (public repos, stars, forks, top
languages, and total contributions in the last year) using the GitHub
REST + GraphQL APIs, then writes a Markdown block into README.md between
the markers:

    <!--STATS:START-->
    ...generated content...
    <!--STATS:END-->

Run by .github/workflows/github.yml on a schedule so the README always
shows fresh numbers, with no third-party image services involved.

Requires: GITHUB_TOKEN env var (the default GITHUB_TOKEN in Actions is
enough — it only needs read access to public data).
"""

import os
import sys
import requests

USERNAME = os.environ.get("GH_USERNAME", "Abhijit1102")
TOKEN = os.environ.get("GITHUB_TOKEN")
README_PATH = os.environ.get("README_PATH", "README.md")

START_MARKER = "<!--STATS:START-->"
END_MARKER = "<!--STATS:END-->"

REST_API = "https://api.github.com"
GRAPHQL_API = "https://api.github.com/graphql"

HEADERS = {
    "Accept": "application/vnd.github+json",
}
if TOKEN:
    HEADERS["Authorization"] = f"Bearer {TOKEN}"


def fetch_repos():
    """Fetch all public, non-fork repos for the user."""
    repos = []
    page = 1
    while True:
        resp = requests.get(
            f"{REST_API}/users/{USERNAME}/repos",
            headers=HEADERS,
            params={"per_page": 100, "page": page, "type": "owner"},
            timeout=30,
        )
        resp.raise_for_status()
        batch = resp.json()
        if not batch:
            break
        repos.extend(batch)
        page += 1
    return repos


def aggregate_languages(repos):
    """Sum language byte counts across all repos."""
    totals = {}
    for repo in repos:
        if repo.get("fork"):
            continue
        lang_url = repo.get("languages_url")
        if not lang_url:
            continue
        resp = requests.get(lang_url, headers=HEADERS, timeout=30)
        if resp.status_code != 200:
            continue
        for lang, count in resp.json().items():
            totals[lang] = totals.get(lang, 0) + count
    return totals


def fetch_total_contributions():
    """Total contributions in the last year via GraphQL (needs a token)."""
    if not TOKEN:
        return None
    query = """
    query($login: String!) {
      user(login: $login) {
        contributionsCollection {
          contributionCalendar {
            totalContributions
          }
        }
      }
    }
    """
    resp = requests.post(
        GRAPHQL_API,
        headers=HEADERS,
        json={"query": query, "variables": {"login": USERNAME}},
        timeout=30,
    )
    if resp.status_code != 200:
        return None
    data = resp.json()
    try:
        return data["data"]["user"]["contributionsCollection"][
            "contributionCalendar"
        ]["totalContributions"]
    except (KeyError, TypeError):
        return None


def build_markdown(repos, languages, contributions):
    non_fork_repos = [r for r in repos if not r.get("fork")]
    total_stars = sum(r.get("stargazers_count", 0) for r in non_fork_repos)
    total_forks = sum(r.get("forks_count", 0) for r in non_fork_repos)
    public_repos = len(non_fork_repos)

    top_languages = sorted(languages.items(), key=lambda kv: kv[1], reverse=True)[:6]
    total_bytes = sum(languages.values()) or 1
    lang_lines = "\n".join(
        f"| {lang} | {bytes_count / total_bytes * 100:.1f}% |"
        for lang, bytes_count in top_languages
    ) or "| _no language data yet_ | - |"

    contrib_line = (
        f"**{contributions:,}** contributions in the last year"
        if contributions is not None
        else "_Contribution count unavailable (requires authenticated token)_"
    )

    return f"""
| Metric | Value |
|---|---|
| Public Repositories | {public_repos} |
| Total Stars | {total_stars} |
| Total Forks | {total_forks} |
| Contributions (last year) | {contributions if contributions is not None else "N/A"} |

**Top Languages**

| Language | Share |
|---|---|
{lang_lines}

{contrib_line}

_Last updated automatically by `scripts/generate_stats.py` via GitHub Actions._
"""


def update_readme(new_block: str):
    with open(README_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    if START_MARKER not in content or END_MARKER not in content:
        print(f"Markers {START_MARKER!r} / {END_MARKER!r} not found in {README_PATH}")
        sys.exit(1)

    before = content.split(START_MARKER)[0]
    after = content.split(END_MARKER)[1]

    updated = f"{before}{START_MARKER}\n{new_block}\n{END_MARKER}{after}"

    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(updated)


def main():
    repos = fetch_repos()
    languages = aggregate_languages(repos)
    contributions = fetch_total_contributions()
    block = build_markdown(repos, languages, contributions)
    update_readme(block)
    print("README.md stats block updated.")


if __name__ == "__main__":
    main()
