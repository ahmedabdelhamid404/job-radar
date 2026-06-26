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
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d",
                "%m/%d/%Y %H:%M:%S", "%m/%d/%Y"):
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

# ---- Apify scrapers (pay-per-result) ----
# Each raises RuntimeError on a failed/blocked run so radar can fire a Telegram alert.

def _apify(token, actor, run_input, max_items, timeout=120):
    r = requests.post(
        f"https://api.apify.com/v2/acts/{actor}/run-sync-get-dataset-items",
        params={"token": token, "maxItems": max_items, "timeout": timeout},
        json=run_input, timeout=timeout + 40)
    if not r.ok:
        try:
            msg = (r.json().get("error") or {}).get("message", r.text[:160])
        except Exception:
            msg = r.text[:160]
        raise RuntimeError(f"HTTP {r.status_code}: {msg}")
    return r.json()

def _clean(v):
    return "" if v in (None, "None") else str(v)

def apify_linkedin(token, urls, cap):
    cap = max(int(cap), 10)   # actor refuses < 10 records
    items = _apify(token, "curious_coder~linkedin-jobs-scraper",
                   {"urls": urls, "count": cap, "scrapeCompany": False}, cap)
    out = []
    for it in items:
        if it.get("error"):
            raise RuntimeError(f"LinkedIn actor error: {str(it['error'])[:120]}")
        loc = _clean(it.get("location"))
        remote = True if "remote" in (loc + " " + _clean(it.get("title"))).lower() else None
        out.append(_mk(it.get("title"), it.get("companyName"), loc,
                       it.get("link") or it.get("applyUrl"),
                       it.get("descriptionText") or it.get("descriptionHtml"),
                       "LinkedIn", remote=remote,
                       tags=[it.get("seniorityLevel"), it.get("employmentType"),
                             it.get("jobFunction"), it.get("industries")],
                       posted=_epoch(it.get("postedAt"))))
    return out

def apify_wuzzuf(token, search_url, cap):
    items = _apify(token, "shahidirfan~Wuzzuf-Jobs-Scraper",
                   {"startUrl": search_url, "results_wanted": int(cap), "max_pages": 2}, int(cap))
    out = []
    for it in items:
        if it.get("status") == "no_results" or "title" not in it:
            continue   # sentinel record, not a failure
        out.append(_mk(it.get("title"), it.get("company"), it.get("location"),
                       it.get("url"), it.get("description_text") or it.get("description_html"),
                       "Wuzzuf", remote=None, tags=it.get("skills"),
                       posted=_epoch(it.get("date_posted"))))
    return out

def apify_indeed(token, country, query, cap, remote_only=True):
    inp = {"country": country, "query": query, "maxRows": int(cap), "fromDays": "7", "sort": "date"}
    if remote_only:
        inp["remote"] = "remote"
    items = _apify(token, "borderline~indeed-scraper", inp, int(cap))
    out = []
    for it in items:
        loc = it.get("location")
        if isinstance(loc, dict):
            loc = ", ".join(x for x in [loc.get("city"), loc.get("country")] if x)
        tags = (it.get("occupation") or []) + (it.get("attributes") or [])[:3]
        out.append(_mk(it.get("title"), it.get("companyName"), _clean(loc),
                       it.get("jobUrl") or it.get("applyUrl"), it.get("descriptionText"),
                       "Indeed", remote=bool(it.get("isRemote")) or None, tags=tags,
                       posted=_epoch(it.get("datePublished"))))
    return out

def apify_bayt(token, country, query, cap):
    cap = max(int(cap), 12)   # floor clears the $0.01 start fee (else run auto-aborts)
    items = _apify(token, "blackfalcondata~bayt-scraper",
                   {"query": query, "country": country, "maxResults": cap, "includeDetails": True}, cap)
    out = []
    for it in items:
        loc = _clean(it.get("location")) or ", ".join(
            x for x in [_clean(it.get("city")), _clean(it.get("country"))] if x)
        rem = it.get("isRemote")
        out.append(_mk(it.get("title"), it.get("company"), loc,
                       it.get("url") or it.get("applyUrl"),
                       it.get("description") or it.get("descriptionText"),
                       "Bayt", remote=(rem if isinstance(rem, bool) else None),
                       tags=it.get("skills"),
                       posted=_epoch(it.get("postedDate") or it.get("postedAt"))))
    return out

