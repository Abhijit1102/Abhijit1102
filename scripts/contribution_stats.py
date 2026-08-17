def calendar_from_api(calendar):
    days=[]
    if not calendar: return days, None
    for week in calendar.get("weeks",[]): days.extend(week.get("contributionDays",[]))
    return days, calendar.get("totalContributions")

def activity_from_events(events):
    counts={}
    for e in events:
        date=(e.get("created_at") or "")[:10]
        if date: counts[date]=counts.get(date,0)+1
    return [{"date":d,"contributionCount":n} for d,n in sorted(counts.items())]
