from pathlib import Path
from html import escape
from .config import LANGUAGE_COLORS

def esc(x): return escape(str(x))
def shell(title, body, width=900, height=300):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}"><rect width="100%" height="100%" rx="18" fill="#161b2d"/><rect x="1" y="1" width="{width-2}" height="{height-2}" rx="17" fill="none" stroke="#2b3553"/><text x="30" y="42" fill="#c8d3f5" font-family="Inter,Arial,sans-serif" font-size="22" font-weight="700">{esc(title)}</text>{body}</svg>'''

def write(path, text): Path(path).parent.mkdir(parents=True,exist_ok=True); Path(path).write_text(text,encoding="utf-8")

def create_stats_svg(s, path):
    items=[("Repositories",s["repos"]),("Followers",s["followers"]),("Following",s["following"]),("Stars",s["stars"]),("Forks",s["forks"]),("Public Gists",s["gists"])]
    body='';
    for i,(label,val) in enumerate(items):
        col=i%3; row=i//3; x=35+col*285; y=82+row*105
        body+=f'<text x="{x}" y="{y}" fill="#7f8db8" font-family="Inter,Arial,sans-serif" font-size="14">{esc(label)}</text><text x="{x}" y="{y+38}" fill="#f0f4ff" font-family="Inter,Arial,sans-serif" font-size="28" font-weight="700">{esc(val)}</text>'
    write(path,shell("GitHub Statistics",body,900,300))

def create_languages_svg(rows,path):
    rows=rows[:8]; maxp=max([r["percentage"] for r in rows] or [1]); body=''; y=78
    for r in rows:
        color=LANGUAGE_COLORS.get(r["language"],"#8b9bbd"); bar=500*r["percentage"]/maxp
        body+=f'<text x="30" y="{y}" fill="#e7ecff" font-family="Inter,Arial,sans-serif" font-size="14">{esc(r["language"])}</text><text x="840" y="{y}" text-anchor="end" fill="#aeb9d9" font-family="Inter,Arial,sans-serif" font-size="14">{r["percentage"]:.2f}%</text><rect x="170" y="{y-12}" width="500" height="12" rx="6" fill="#252e49"/><rect x="170" y="{y-12}" width="{bar:.1f}" height="12" rx="6" fill="{color}"/><text x="690" y="{y}" fill="#7786ae" font-family="Inter,Arial,sans-serif" font-size="11">{r["bytes"]:,} bytes</text>'
        y+=38
    write(path,shell("Most Used Languages",body,900,max(180,80+38*len(rows))))

def create_repositories_svg(a,path):
    body=f'<text x="30" y="78" fill="#7f8db8" font-family="Inter,Arial,sans-serif" font-size="14">Owned repositories</text><text x="30" y="110" fill="#f0f4ff" font-family="Inter,Arial,sans-serif" font-size="28" font-weight="700">{a["total"]}</text><text x="210" y="78" fill="#7f8db8" font-family="Inter,Arial,sans-serif" font-size="14">Stars</text><text x="210" y="110" fill="#f0f4ff" font-family="Inter,Arial,sans-serif" font-size="28" font-weight="700">{a["stars"]}</text><text x="390" y="78" fill="#7f8db8" font-family="Inter,Arial,sans-serif" font-size="14">Forks</text><text x="390" y="110" fill="#f0f4ff" font-family="Inter,Arial,sans-serif" font-size="28" font-weight="700">{a["forks"]}</text>'
    y=155
    for r in a["featured"][:5]:
        body+=f'<text x="30" y="{y}" fill="#9cc7ff" font-family="Inter,Arial,sans-serif" font-size="15" font-weight="600">{esc(r["name"])}</text><text x="250" y="{y}" fill="#aeb9d9" font-family="Inter,Arial,sans-serif" font-size="13">★ {r.get("stargazers_count",0)} · forks {r.get("forks_count",0)}</text>'
        y+=28
    write(path,shell("Repository Analytics",body,900,310))

def create_activity_svg(events,path):
    counts={}
    for e in events:
        d=(e.get("created_at") or "")[:10]
        if d: counts[d]=counts.get(d,0)+1
    recent=sorted(counts.items())[-14:]
    maxv=max([v for _,v in recent] or [1]); body=''; x=35
    for d,v in recent:
        h=130*v/maxv; body+=f'<rect x="{x}" y="220" width="45" height="{-h}" rx="5" fill="#7aa2f7"/><text x="{x+22}" y="245" text-anchor="middle" fill="#7f8db8" font-family="Inter,Arial,sans-serif" font-size="9">{d[5:]}</text><text x="{x+22}" y="{205-h}" text-anchor="middle" fill="#c8d3f5" font-family="Inter,Arial,sans-serif" font-size="10">{v}</text>'; x+=60
    body+='<text x="30" y="275" fill="#66759d" font-family="Inter,Arial,sans-serif" font-size="11">Public GitHub events observed by the API; this is activity, not a fabricated contribution count.</text>'
    write(path,shell("Recent GitHub Activity",body,900,300))

def create_contributions_svg(days,total,path):
    if not days:
        body='<text x="30" y="90" fill="#c8d3f5" font-family="Inter,Arial,sans-serif" font-size="15">Exact contribution calendar unavailable without a GITHUB_TOKEN.</text><text x="30" y="120" fill="#7f8db8" font-family="Inter,Arial,sans-serif" font-size="12">Run with a GitHub token locally or in Actions to populate the calendar from GitHub GraphQL.</text>'
        return write(path,shell("Contribution Activity",body,900,180))
    # GitHub returns 53 columns x 7 rows; render all days in order.
    body=f'<text x="30" y="70" fill="#aeb9d9" font-family="Inter,Arial,sans-serif" font-size="13">Total contributions: {total}</text>'
    maxc=max(d.get("contributionCount",0) for d in days) or 1
    for i,d in enumerate(days):
        col=i//7; row=i%7; x=30+col*15; y=92+row*15; c=d.get("contributionCount",0); intensity=min(4,int(c*4/maxc))
        fills=["#222a43","#25395a","#315078","#426b9c","#61a0d8"]
        body+=f'<rect x="{x}" y="{y}" width="11" height="11" rx="2" fill="{fills[intensity]}"/><title>{esc(d.get("date"))}: {c} contributions</title></rect>'
    write(path,shell("Contribution Activity",body,900,235))
