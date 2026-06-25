import hashlib, calendar
from datetime import datetime, timezone
import requests, feedparser

HEADERS = {"User-Agent": "job-radar/1.0 (personal job search)"}
TIMEOUT = 20

def _epoch(val):
    if val is None or val == "":
        return None
    if isinstance(val, (int, float)):
        v = float(val)
        return v / 1000.0 if v > 1e12 else v
    s = str(val).strip().replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(s).timestamp()
    except Exception:
        pass
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(s[:19], fmt).replace(tzinfo=timezone.utc).timestamp()
        except Exception:
            pass
    return None

def _id(url, title="", company=""):
    base = url or (title + company)
    return hashlib.sha1(base.encode("utf-8", "ignore")).hexdigest()[:16]

def _mk(title, company, location, url, description, source, remote=None, tags=None, posted=None):
    return {
        "id": _id(url, title or "", company or ""),
        "title": (title or "").strip(),
        "company": (company or "").strip(),
        "location": (location or "").strip(),
        "url": (url or "").strip(),
        "description": description or "",
        "source": source,
        "remote": remote,
        "tags": [t for t in (tags or []) if t],
        "posted": posted,
    }

# ---- no-key sources ----

def remoteok():
    data = requests.get("https://remoteok.com/api", headers=HEADERS, timeout=TIMEOUT).json()
    out = []
    for it in data:
        if not isinstance(it, dict) or "position" not in it:
            continue
        out.append(_mk(it.get("position"), it.get("company"), it.get("location") or "Remote",
                       it.get("url") or it.get("apply_url"), it.get("description"),
                       "RemoteOK", remote=True, tags=it.get("tags"),
                       posted=_epoch(it.get("epoch") or it.get("date"))))
    return out

def remotive(query):
    r = requests.get("https://remotive.com/api/remote-jobs",
                     params={"search": query, "limit": 100}, headers=HEADERS, timeout=TIMEOUT)
    out = []
    for it in r.json().get("jobs", []):
        out.append(_mk(it.get("title"), it.get("company_name"),
                       it.get("candidate_required_location") or "Remote", it.get("url"),
                       it.get("description"), "Remotive", remote=True, tags=[it.get("category")],
                       posted=_epoch(it.get("publication_date"))))
    return out

def arbeitnow():
    r = requests.get("https://www.arbeitnow.com/api/job-board-api", headers=HEADERS, timeout=TIMEOUT)
    out = []
    for it in r.json().get("data", []):
        out.append(_mk(it.get("title"), it.get("company_name"), it.get("location"),
                       it.get("url"), it.get("description"), "Arbeitnow",
                       remote=bool(it.get("remote")), tags=it.get("tags"),
                       posted=_epoch(it.get("created_at"))))
    return out

def jobicy(query):
    r = requests.get("https://jobicy.com/api/v2/remote-jobs",
                     params={"count": 50, "tag": query}, headers=HEADERS, timeout=TIMEOUT)
    out = []
    for it in r.json().get("jobs", []):
        out.append(_mk(it.get("jobTitle"), it.get("companyName"), it.get("jobGeo") or "Remote",
                       it.get("url"), it.get("jobExcerpt"), "Jobicy", remote=True,
                       tags=it.get("jobIndustry") if isinstance(it.get("jobIndustry"), list) else [it.get("jobIndustry")],
                       posted=_epoch(it.get("pubDate") or it.get("date"))))
    return out

def weworkremotely():
    feed = feedparser.parse("https://weworkremotely.com/categories/remote-front-end-programming-jobs.rss")
    out = []
    for e in feed.entries:
        posted = calendar.timegm(e.published_parsed) if e.get("published_parsed") else None
        out.append(_mk(e.get("title"), "", "Remote", e.get("link"), e.get("summary"),
                       "WeWorkRemotely", remote=True, posted=posted))
    return out

def himalayas():
    r = requests.get("https://himalayas.app/jobs/api", params={"limit": 50}, headers=HEADERS, timeout=TIMEOUT)
    out = []
    for it in r.json().get("jobs", []):
        loc = it.get("locationRestrictions") or []
        out.append(_mk(it.get("title"), it.get("companyName"),
                       ", ".join(loc) if isinstance(loc, list) else str(loc) or "Remote",
                       it.get("applicationLink") or it.get("guid"), it.get("description"),
                       "Himalayas", remote=True, tags=it.get("categories"),
                       posted=_epoch(it.get("pubDate") or it.get("publishedDate"))))
    return out

# ---- key sources ----

def jooble(key, query, location):
    r = requests.post(f"https://jooble.org/api/{key}",
                      json={"keywords": query, "location": location}, timeout=TIMEOUT)
    out = []
    for it in r.json().get("jobs", []):
        out.append(_mk(it.get("title"), it.get("company"), it.get("location"),
                       it.get("link"), it.get("snippet"), "Jooble", remote=None,
                       posted=_epoch(it.get("updated"))))
    return out

def adzuna(app_id, app_key, country, query):
    url = f"https://api.adzuna.com/v1/api/jobs/{country}/search/1"
    r = requests.get(url, params={"app_id": app_id, "app_key": app_key, "what": query,
                                  "results_per_page": 50, "content-type": "application/json"},
                     headers=HEADERS, timeout=TIMEOUT)
    out = []
    for it in r.json().get("results", []):
        out.append(_mk(it.get("title"), (it.get("company") or {}).get("display_name"),
                       (it.get("location") or {}).get("display_name"), it.get("redirect_url"),
                       it.get("description"), "Adzuna", remote=None,
                       posted=_epoch(it.get("created"))))
    return out
