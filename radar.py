#!/usr/bin/env python3
import logging, html, time
from pathlib import Path
import yaml
import db, sources, score, alerts, spend

ROOT = Path(__file__).parent
logging.basicConfig(filename=ROOT / "radar.log", level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("radar")

def load_cfg():
    with open(ROOT / "config.yaml") as f:
        return yaml.safe_load(f)

def gather(cfg, tier="all"):
    jobs, failures = [], []
    keys = cfg.get("keys", {})
    queries = cfg["search"]["queries"]

    def run(name, fn):
        try:
            res = fn()
            jobs.extend(res)
            log.info("source %s -> %d", name, len(res))
        except Exception as e:
            log.warning("source %s FAILED: %s", name, e)   # free sources: log only, no alert

    # ---- free sources: run in every tier ----
    run("RemoteOK", sources.remoteok)
    run("Arbeitnow", sources.arbeitnow)
    run("WeWorkRemotely", sources.weworkremotely)
    run("Himalayas", sources.himalayas)
    for q in queries:
        run(f"Remotive[{q}]", lambda q=q: sources.remotive(q))
        run(f"Jobicy[{q}]", lambda q=q: sources.jobicy(q))

    if keys.get("jooble"):
        locs = []
        m = cfg["markets"]
        if m.get("egypt"):
            locs.append("Egypt")
        if m.get("gulf"):
            locs += ["United Arab Emirates", "Saudi Arabia", "Qatar"]
        if m.get("remote_intl"):
            locs.append("Remote")
        for q in queries:
            for loc in locs:
                run(f"Jooble[{q}/{loc}]",
                    lambda q=q, loc=loc: sources.jooble(keys["jooble"], q, loc))

    if keys.get("adzuna_app_id") and keys.get("adzuna_app_key"):
        for country in ["gb", "us"]:
            for q in queries:
                run(f"Adzuna[{country}/{q}]",
                    lambda c=country, q=q: sources.adzuna(keys["adzuna_app_id"], keys["adzuna_app_key"], c, q))

    # ---- paid Apify scrapers: tier-gated + spend-guarded ----
    if tier in ("all", "morning", "evening", "night"):
        gather_apify(cfg, tier, jobs, failures)

    return jobs, failures

def _linkedin_urls(cfg, query):
    q = query.replace(" ", "%20")
    base = "https://www.linkedin.com/jobs/search/?keywords=" + q + "&f_TPR=r604800"
    m = cfg.get("markets", {})
    urls = []
    if m.get("remote_intl"):
        urls.append(base + "&f_WT=2")                       # remote, worldwide
    if m.get("egypt"):
        urls.append(base + "&location=Egypt")
    if m.get("gulf"):
        urls.append(base + "&location=United%20Arab%20Emirates")
        urls.append(base + "&location=Saudi%20Arabia")
    return urls or [base + "&f_WT=2"]

def gather_apify(cfg, tier, jobs, failures):
    ap = cfg.get("apify") or {}
    token = ap.get("token")
    if not token:
        return
    guard = ap.get("spend_guard_usd", 4.5)
    used = spend.spent()
    if used >= guard:
        log.warning("spend guard: $%.2f >= $%.2f — skipping paid scrapers", used, guard)
        failures.append(("Apify budget",
                         f"spend guard reached (${used:.2f} of ${guard:.2f}); paid scrapers paused "
                         f"until the monthly reset. Free sources still running."))
        return
    caps = ap.get("caps", {})
    prices = ap.get("prices", {})
    query = ap.get("query", "Angular")

    def paid(name, key, fn):
        try:
            items = fn()
            jobs.extend(items)
            p = prices.get(key, {})
            cost = p.get("start", 0.0) + len(items) * p.get("result", 0.0)
            total = spend.add(cost)
            log.info("apify %s -> %d  ($%.3f; month $%.2f)", name, len(items), cost, total)
        except Exception as e:
            log.warning("apify %s FAILED: %s", name, e)
            failures.append((name, str(e)[:200]))

    # LinkedIn — every tier (strongest cross-market source)
    paid("LinkedIn", "linkedin",
         lambda: sources.apify_linkedin(token, _linkedin_urls(cfg, query), caps.get("linkedin", 20)))
    # Wuzzuf — morning + evening
    if tier in ("all", "morning", "evening"):
        paid("Wuzzuf", "wuzzuf",
             lambda: sources.apify_wuzzuf(token,
                     ap.get("wuzzuf_url", "https://wuzzuf.net/search/jobs/?q=angular"),
                     caps.get("wuzzuf", 20)))
    # Indeed + Bayt — morning only (cost control)
    if tier in ("all", "morning"):
        for c in ap.get("indeed_countries", ["us"]):
            paid(f"Indeed[{c}]", "indeed",
                 lambda c=c: sources.apify_indeed(token, c, query, caps.get("indeed", 15)))
        paid("Bayt", "bayt",
             lambda: sources.apify_bayt(token, ap.get("bayt_country", "INTERNATIONAL"),
                                        query, caps.get("bayt", 15)))

def process(cfg, raw):
    seen = set()
    new = []
    with db.conn() as c:
        for j in raw:
            if j["id"] in seen:
                continue
            seen.add(j["id"])
            if not score.relevant(j, cfg):
                continue
            if not score.fresh(j, cfg):
                continue
            if not score.passes_workstyle(j, cfg):
                continue
            if db.exists(c, j["id"]):
                continue
            s, matched, tr = score.score(j, cfg)
            cv = score.pick_cv(j)
            remote = "remote" if score.is_remote(j) else ("hybrid" if score.is_hybrid(j) else "")
            j2 = {**j, "score": s, "cv": cv, "matched": matched,
                  "market": score.market_of(j), "remote": remote,
                  "pitch": score.pitch(j, matched, cv, score.TIER_LABEL.get(tr, ""))}
            db.insert_job(c, j2)
            new.append(j2)
    new.sort(key=lambda x: (x["score"], x.get("posted") or 0), reverse=True)
    return new

def _age(posted):
    if not posted:
        return ""
    d = time.time() - posted
    if d < 3600:
        return f"{int(d // 60)}m"
    if d < 86400:
        return f"{int(d // 3600)}h"
    return f"{int(d // 86400)}d"

def notify(cfg, new):
    port = cfg["dashboard"]["port"]
    n = len(new)
    head_plain = f"🔔 {n} new Angular match{'es' if n != 1 else ''}"
    cap = 20
    lines = [f"<b>{head_plain}</b> · cleanest &amp; newest first", ""]
    for i, j in enumerate(new[:cap], 1):
        title = html.escape(j["title"] or "")
        meta = f"{html.escape(j['company'] or '—')} · {j['score']}% · {html.escape(j['cv'])} CV · {html.escape(j['market'])}"
        age = _age(j.get("posted"))
        if age:
            meta += f" · 🕒 {age}"
        url = j.get("url") or ""
        head = f'<a href="{html.escape(url, quote=True)}"><b>{title}</b></a>' if url else f"<b>{title}</b>"
        lines.append(f"{i}. {head}")
        lines.append(f"    {meta}")
    if n > cap:
        lines.append(f"\n… +{n - cap} more in the dashboard")
    lines.append(f"\n📋 Open dashboard: http://localhost:{port}")
    ok, info = alerts.send_telegram(cfg, "\n".join(lines))
    log.info("telegram sent=%s info=%s", ok, info)
    top = new[0]
    alerts.send_desktop(cfg, head_plain, f"{top['title']} @ {top['company']}")
    body = "<br>".join(f"{j['score']}% — <b>{j['title']}</b> @ {j['company']} "
                       f"[{j['cv']}] <a href='{j['url']}'>Apply</a>" for j in new[:25])
    alerts.send_email(cfg, head_plain, body)

def notify_failures(cfg, failures):
    lines = ["⚠️ <b>Job Radar — scraper issue</b>", ""]
    for name, err in failures:
        lines.append(f"• <b>{html.escape(name)}</b>: {html.escape(err)[:170]}")
    lines.append("\nFree sources still ran. This usually means a site blocked the scraper "
                 "or Apify hit a limit — check the dashboard/logs.")
    ok, info = alerts.send_telegram(cfg, "\n".join(lines))
    log.info("failure alert sent=%s info=%s", ok, info)

def main(tier="all"):
    cfg = load_cfg()
    db.init()
    raw, failures = gather(cfg, tier)
    log.info("gathered %d raw (tier=%s); %d scraper failures", len(raw), tier, len(failures))
    new = process(cfg, raw)
    log.info("new matches: %d", len(new))
    if new:
        notify(cfg, new)
    if failures:
        notify_failures(cfg, failures)
    return new

if __name__ == "__main__":
    import sys
    tier = sys.argv[1] if len(sys.argv) > 1 else "all"
    matches = main(tier)
    print(f"NEW MATCHES ({tier}): {len(matches)}")
    for j in matches[:15]:
        print(f"  {j['score']:>3}  {j['cv']:<13} {j['title'][:50]:<50} @ {j['company'][:22]} [{j['source']}]")
