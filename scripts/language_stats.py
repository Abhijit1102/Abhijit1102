from collections import defaultdict
from .config import LANGUAGE_NORMALIZATION

def aggregate_languages(api, repos):
    totals=defaultdict(int)
    for r in repos:
        if r.get("fork") or r.get("archived") or r.get("size",0)==0: continue
        try: langs=api.get_repository_languages(r["owner"]["login"], r["name"])
        except Exception: continue
        for lang, n in langs.items(): totals[LANGUAGE_NORMALIZATION.get(lang,lang)] += n
    total=sum(totals.values())
    rows=[]
    for lang, bytes_ in sorted(totals.items(), key=lambda x:x[1], reverse=True):
        rows.append({"language":lang,"bytes":bytes_,"percentage":(bytes_/total*100 if total else 0)})
    return rows
