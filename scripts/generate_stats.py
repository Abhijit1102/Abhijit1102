import json, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from scripts.config import GITHUB_USERNAME, OUTPUT_DIR, DATA_DIR
from scripts.github_api import GitHubAPI
from scripts.language_stats import aggregate_languages
from scripts.repository_stats import analyze
from scripts.contribution_stats import calendar_from_api, activity_from_events
from scripts.svg_generator import create_stats_svg, create_languages_svg, create_repositories_svg, create_activity_svg, create_contributions_svg

def main():
    api=GitHubAPI(username=GITHUB_USERNAME)
    user=api.get_user()
    if not user: raise SystemExit(f"Unable to retrieve GitHub user {GITHUB_USERNAME}")
    repos=api.get_repositories()
    analytics=analyze(repos)
    languages=aggregate_languages(api,repos)
    events=api.get_events()
    calendar=api.get_contributions()
    days,total=calendar_from_api(calendar)
    # Do not substitute public events into the contribution calendar; exact contribution counts are a different metric.
    DATA_DIR.mkdir(exist_ok=True); OUTPUT_DIR.mkdir(parents=True,exist_ok=True)
    payload={"user":user,"repository_count":len(repos),"analytics":analytics,"languages":languages,"contribution_total":total,"event_count":len(events)}
    # Strip large/unneeded nested repo objects for compact cache.
    Path(DATA_DIR/"github.json").write_text(json.dumps(payload,indent=2,default=str),encoding="utf-8")
    Path(DATA_DIR/"languages.json").write_text(json.dumps(languages,indent=2),encoding="utf-8")
    create_stats_svg({"repos":user.get("public_repos",0),"followers":user.get("followers",0),"following":user.get("following",0),"stars":analytics["stars"],"forks":analytics["forks"],"gists":user.get("public_gists",0)},OUTPUT_DIR/"stats.svg")
    create_languages_svg(languages,OUTPUT_DIR/"languages.svg")
    create_repositories_svg(analytics,OUTPUT_DIR/"repositories.svg")
    create_activity_svg(events,OUTPUT_DIR/"activity.svg")
    create_contributions_svg(days,total,OUTPUT_DIR/"contributions.svg")
    print("User:",user.get("login"),"| Public repos:",user.get("public_repos"),"| Followers:",user.get("followers"))
    print("Repositories analyzed:",analytics["total"],"| Stars:",analytics["stars"],"| Forks:",analytics["forks"])
    print("Languages:", ", ".join(f'{x["language"]} {x["percentage"]:.2f}%' for x in languages))
    print("Featured:", ", ".join(r["name"] for r in analytics["featured"]))
    print("Contribution source:", "GitHub GraphQL" if calendar else "public events fallback (not exact contributions)")

if __name__=="__main__": main()
