#!/usr/bin/env python3
import logging
from pathlib import Path
import yaml
import db, sources, score, alerts

ROOT = Path(__file__).parent
logging.basicConfig(filename=ROOT / "radar.log", level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("radar")

def load_cfg():
    with open(ROOT / "config.yaml") as f:
        return yaml.safe_load(f)

def gather(cfg):
    jobs = []
    keys = cfg.get("keys", {})
    queries = cfg["search"]["queries"]

    def run(name, fn):
        try:
            res = fn()
            jobs.extend(res)
            log.info("source %s -> %d", name, len(res))
        except Exception as e:
            log.warning("source %s FAILED: %s", name, e)

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

    return jobs

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
            s, matched = score.score(j, cfg)
            cv = score.pick_cv(j)
            remote = "remote" if score.is_remote(j) else ("hybrid" if score.is_hybrid(j) else "")
            j2 = {**j, "score": s, "cv": cv, "matched": matched,
                  "market": score.market_of(j), "remote": remote,
                  "pitch": score.pitch(j, matched, cv)}
            db.insert_job(c, j2)
            new.append(j2)
    new.sort(key=lambda x: (x["score"], x.get("posted") or 0), reverse=True)
    return new

def notify(cfg, new):
    port = cfg["dashboard"]["port"]
    top = new[0]
    head = f"🔔 {len(new)} new Angular match{'es' if len(new) != 1 else ''}"
    msg = (f"{head}\n"
           f"Top: {top['title']} @ {top['company'] or '—'} "
           f"({top['score']}% · {top['cv']} CV · {top['market']})\n"
           f"Dashboard: http://localhost:{port}")
    ok, info = alerts.send_telegram(cfg, msg)
    log.info("telegram sent=%s info=%s", ok, info)
    alerts.send_desktop(cfg, head, f"{top['title']} @ {top['company']}")
    body = "<br>".join(f"{j['score']}% — <b>{j['title']}</b> @ {j['company']} "
                       f"[{j['cv']}] <a href='{j['url']}'>open</a>" for j in new[:25])
    alerts.send_email(cfg, head, body)

def main():
    cfg = load_cfg()
    db.init()
    raw = gather(cfg)
    log.info("gathered %d raw listings", len(raw))
    new = process(cfg, raw)
    log.info("new matches: %d", len(new))
    if new:
        notify(cfg, new)
    return new

if __name__ == "__main__":
    matches = main()
    print(f"NEW MATCHES: {len(matches)}")
    for j in matches[:15]:
        print(f"  {j['score']:>3}%  {j['cv']:<13} {j['title'][:55]:<55} @ {j['company'][:25]} [{j['source']}]")
