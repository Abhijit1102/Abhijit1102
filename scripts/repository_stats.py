from datetime import datetime, timezone
from .config import TECH_RELEVANCE, EXCLUDED_REPOSITORIES, MAX_FEATURED_REPOSITORIES

def relevance(repo):
    text=(repo.get("name","")+" "+(repo.get("description") or "")).lower()
    tech=sum(weight for key,weight in TECH_RELEVANCE.items() if key in text)
    stars=repo.get("stargazers_count",0); forks=repo.get("forks_count",0)
    updated=repo.get("pushed_at") or repo.get("updated_at") or "1970-01-01T00:00:00Z"
    try: age_days=max(0,(datetime.now(timezone.utc)-datetime.fromisoformat(updated.replace("Z","+00:00"))).days)
    except: age_days=3650
    recent=max(0, 1-min(age_days/365,1))*10
    return stars*5 + forks*3 + recent*2 + tech*5

def analyze(repos):
    owned=[r for r in repos if not r.get("fork") and r.get("name") not in EXCLUDED_REPOSITORIES]
    featured=sorted(owned,key=relevance,reverse=True)[:MAX_FEATURED_REPOSITORIES]
    return {
      "total":len(owned), "stars":sum(r.get("stargazers_count",0) for r in owned),
      "forks":sum(r.get("forks_count",0) for r in owned),
      "most_starred":max(owned,key=lambda r:r.get("stargazers_count",0),default=None),
      "most_forked":max(owned,key=lambda r:r.get("forks_count",0),default=None),
      "recent":sorted(owned,key=lambda r:r.get("pushed_at") or "",reverse=True)[:6],
      "largest":sorted(owned,key=lambda r:r.get("size",0),reverse=True)[:6],
      "featured":featured,
    }
