#!/usr/bin/env python3

"""
generate_stats.py

Pulls live stats for a GitHub user:
- Public original repositories
- Total stars received by those repositories
- Total forks of those repositories
- Top languages
- Total contributions in the last year
- Top starred repositories

Then updates README.md between:

<!--STATS:START-->
<!--STATS:END-->

Requires:
    GITHUB_TOKEN

Optional:
    GH_USERNAME
    README_PATH
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
    """Fetch all repositories owned by the GitHub user."""

    repos = []
    page = 1

    while True:
        response = requests.get(
            f"{REST_API}/users/{USERNAME}/repos",
            headers=HEADERS,
            params={
                "per_page": 100,
                "page": page,
                "type": "owner",
            },
            timeout=30,
        )

        response.raise_for_status()

        batch = response.json()

        if not batch:
            break

        repos.extend(batch)
        page += 1

    return repos


def get_original_repos(repos):
    """
    Return only repositories originally owned by the user.

    Forked repositories are excluded.
    """

    return [
        repo
        for repo in repos
        if not repo.get("fork", False)
    ]


def aggregate_languages(repos):
    """Sum language byte counts across all original repositories."""

    totals = {}

    for repo in repos:
        if repo.get("fork"):
            continue

        languages_url = repo.get("languages_url")

        if not languages_url:
            continue

        response = requests.get(
            languages_url,
            headers=HEADERS,
            timeout=30,
        )

        if response.status_code != 200:
            continue

        for language, byte_count in response.json().items():
            totals[language] = totals.get(language, 0) + byte_count

    return totals


def fetch_total_contributions():
    """
    Fetch total GitHub contributions during the last year.

    Requires an authenticated GitHub token.
    """

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

    response = requests.post(
        GRAPHQL_API,
        headers=HEADERS,
        json={
            "query": query,
            "variables": {
                "login": USERNAME
            },
        },
        timeout=30,
    )

    if response.status_code != 200:
        return None

    data = response.json()

    try:
        return data["data"]["user"]["contributionsCollection"][
            "contributionCalendar"
        ]["totalContributions"]

    except (KeyError, TypeError):
        return None


def build_top_repositories(repos):
    """Build Markdown table for the most-starred repositories."""

    sorted_repos = sorted(
        repos,
        key=lambda repo: repo.get("stargazers_count", 0),
        reverse=True,
    )

    top_repos = sorted_repos[:5]

    if not top_repos:
        return "| _No repositories found_ | - | - |"

    rows = []

    for repo in top_repos:
        name = repo.get("name", "Unknown")
        stars = repo.get("stargazers_count", 0)
        forks = repo.get("forks_count", 0)

        url = repo.get(
            "html_url",
            f"https://github.com/{USERNAME}/{name}",
        )

        rows.append(
            f"| [{name}]({url}) | ⭐ {stars} | 🍴 {forks} |"
        )

    return "\n".join(rows)


def build_markdown(repos, languages, contributions):
    """Build the complete statistics Markdown block."""

    non_fork_repos = [
        repo
        for repo in repos
        if not repo.get("fork", False)
    ]

    # ---------------------------------------------------------
    # Repository statistics
    # ---------------------------------------------------------

    public_repos = len(non_fork_repos)

    # Stars RECEIVED by your repositories
    total_stars = sum(
        repo.get("stargazers_count", 0)
        for repo in non_fork_repos
    )

    # Forks RECEIVED by your repositories
    total_forks = sum(
        repo.get("forks_count", 0)
        for repo in non_fork_repos
    )

    # ---------------------------------------------------------
    # Top languages
    # ---------------------------------------------------------

    top_languages = sorted(
        languages.items(),
        key=lambda item: item[1],
        reverse=True,
    )[:6]

    total_bytes = sum(languages.values()) or 1

    language_rows = "\n".join(
        f"| {language} | {byte_count / total_bytes * 100:.1f}% |"
        for language, byte_count in top_languages
    )

    if not language_rows:
        language_rows = "| _No language data yet_ | - |"

    # ---------------------------------------------------------
    # Contributions
    # ---------------------------------------------------------

    contribution_value = (
        f"{contributions:,}"
        if contributions is not None
        else "N/A"
    )

    contribution_note = (
        f"**🔥 {contributions:,} contributions in the last year**"
        if contributions is not None
        else "_Contribution count unavailable (requires authenticated token)_"
    )

    # ---------------------------------------------------------
    # Top repositories
    # ---------------------------------------------------------

    top_repositories = build_top_repositories(
        non_fork_repos
    )

    # ---------------------------------------------------------
    # Markdown output
    # ---------------------------------------------------------

    return f"""
## 📊 GitHub Statistics

| Metric | Value |
|---|---:|
| 📦 Public Repositories | **{public_repos}** |
| ⭐ Stars Received | **{total_stars}** |
| 🍴 Forks Received | **{total_forks}** |
| 🔥 Contributions (Last Year) | **{contribution_value}** |

### ⭐ Top Starred Repositories

| Repository | ⭐ Stars | 🍴 Forks |
|---|---:|---:|
{top_repositories}

### 💻 Top Languages

| Language | Share |
|---|---:|
{language_rows}

{contribution_note}

_Last updated automatically by `scripts/generate_stats.py` via GitHub Actions._
"""


def update_readme(new_block: str):
    """Replace the existing statistics block in README.md."""

    try:
        with open(
            README_PATH,
            "r",
            encoding="utf-8",
        ) as file:
            content = file.read()

    except FileNotFoundError:
        print(f"README file not found: {README_PATH}")
        sys.exit(1)

    if (
        START_MARKER not in content
        or END_MARKER not in content
    ):
        print(
            f"Markers {START_MARKER!r} / "
            f"{END_MARKER!r} not found in {README_PATH}"
        )
        sys.exit(1)

    before = content.split(
        START_MARKER,
        1
    )[0]

    after = content.split(
        END_MARKER,
        1
    )[1]

    updated = (
        f"{before}"
        f"{START_MARKER}\n"
        f"{new_block.strip()}\n"
        f"{END_MARKER}"
        f"{after}"
    )

    with open(
        README_PATH,
        "w",
        encoding="utf-8",
    ) as file:
        file.write(updated)


def main():
    print(f"Fetching GitHub stats for @{USERNAME}...")

    # Fetch repositories
    repos = fetch_repos()

    # Keep only original repositories
    original_repos = get_original_repos(repos)

    print(
        f"Found {len(original_repos)} "
        f"original public repositories."
    )

    # Languages
    languages = aggregate_languages(
        original_repos
    )

    # Contributions
    contributions = fetch_total_contributions()

    # Build Markdown
    block = build_markdown(
        original_repos,
        languages,
        contributions,
    )

    # Update README
    update_readme(block)

    print("README.md stats block updated successfully.")


if __name__ == "__main__":
    main()