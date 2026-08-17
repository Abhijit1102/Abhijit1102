import os, time, json, urllib.request, urllib.error, urllib.parse

class GitHubAPIError(RuntimeError): pass

class GitHubAPI:
    def __init__(self, token=None, username=None):
        self.token=token or os.getenv("GITHUB_TOKEN"); self.username=username; self.base="https://api.github.com"
    def _request(self, method, path, params=None, payload=None, retries=3):
        url=path if path.startswith("http") else self.base+path
        if params: url += ("&" if "?" in url else "?")+urllib.parse.urlencode(params)
        headers={"Accept":"application/vnd.github+json","X-GitHub-Api-Version":"2022-11-28","User-Agent":"github-profile-stats"}
        if self.token: headers["Authorization"]=f"Bearer {self.token}"
        data=json.dumps(payload).encode() if payload is not None else None
        for attempt in range(retries):
            try:
                req=urllib.request.Request(url,data=data,headers=headers,method=method)
                with urllib.request.urlopen(req,timeout=30) as r: return json.loads(r.read().decode())
            except urllib.error.HTTPError as e:
                if e.code==404: return None
                if e.code>=500 and attempt<retries-1: time.sleep(2**attempt); continue
                if e.code==403 and attempt<retries-1: time.sleep(2**attempt); continue
                msg=e.read().decode(errors="replace")[:300]
                raise GitHubAPIError(f"GitHub API {e.code}: {msg}")
            except (urllib.error.URLError, TimeoutError) as e:
                if attempt==retries-1: raise GitHubAPIError(str(e))
                time.sleep(2**attempt)
        raise GitHubAPIError("GitHub API request failed")
    def _paginate(self,path,params=None,per_page=100):
        params=dict(params or {}); params["per_page"]=per_page; out=[]
        for page in range(1,100):
            params["page"]=page; data=self._request("GET",path,params) or []
            if not isinstance(data,list): return data
            out.extend(data)
            if len(data)<per_page: break
        return out
    def get_user(self): return self._request("GET",f"/users/{self.username}")
    def get_repositories(self): return self._paginate(f"/users/{self.username}/repos",{"type":"owner","sort":"updated"})
    def get_repository_languages(self,owner,repo): return self._request("GET",f"/repos/{owner}/{repo}/languages") or {}
    def get_repository(self,owner,repo): return self._request("GET",f"/repos/{owner}/{repo}")
    def get_commits(self,owner,repo,per_page=100): return self._paginate(f"/repos/{owner}/{repo}/commits",{"author":owner},per_page)
    def get_contributions(self):
        if not self.token: return None
        q='query($login:String!){user(login:$login){contributionsCollection{contributionCalendar{totalContributions weeks{contributionDays{date contributionCount}}}}}}'
        body=self._request("POST","/graphql",payload={"query":q,"variables":{"login":self.username}})
        if not body or body.get("errors"): return None
        return body["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    def get_followers(self): return self._paginate(f"/users/{self.username}/followers")
    def get_events(self,pages=3):
        out=[]
        for page in range(1,pages+1):
            data=self._request("GET",f"/users/{self.username}/events/public",{"per_page":100,"page":page}) or []
            out.extend(data)
            if len(data)<100: break
        return out
