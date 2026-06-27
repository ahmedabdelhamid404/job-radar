#!/usr/bin/env python3
from flask import Flask, render_template, request, redirect
from pathlib import Path
import yaml, db, time, threading, radar, score

ROOT = Path(__file__).parent
app = Flask(__name__)

TABS = [("new", "📥 Inbox"), ("applied", "✅ Applied"),
        ("interviewing", "🎯 Interviewing"), ("dismissed", "🗑️ Dismissed")]
VALID = {"new", "applied", "interviewing", "dismissed"}

# in-memory state for the manual run buttons
_scan = {"running": False, "found": None, "tier": ""}

def _run_scan(tier):
    try:
        _scan["found"] = len(radar.main(tier))
    except Exception as e:
        _scan["found"] = f"error: {e}"
    finally:
        _scan["running"] = False

def cfg():
    with open(ROOT / "config.yaml") as f:
        return yaml.safe_load(f)

def age_str(posted):
    if not posted:
        return ""
    d = time.time() - posted
    if d < 0:
        return "just now"
    if d < 3600:
        return f"{int(d // 60)}m ago"
    if d < 86400:
        return f"{int(d // 3600)}h ago"
    return f"{int(d // 86400)}d ago"

def claude_prompt(j):
    if j.get("source") == "LinkedIn Post":
        return (f"This is a LinkedIn hiring POST. Write me (a) a short, warm DM/comment to the poster "
                f"and (b) a tailored cover letter, using my {j['cv']} CV "
                f"(~/Documents/cvs/Ahmed-Abdelhamid-CV-{j['cv']}.pdf).\n\n"
                f"Poster: {j['company']}\nPoster headline: {j['location']}\n"
                f"Role line: {j['title']}\nPost link: {j['url']}")
    return (f"Help me apply to this job. Write a tailored cover letter and a list of likely "
            f"interview questions with strong answers, using my {j['cv']} CV "
            f"(at ~/Documents/cvs/Ahmed-Abdelhamid-CV-{j['cv']}.pdf).\n\n"
            f"Role: {j['title']}\nCompany: {j['company']}\nLocation: {j['location']}\n"
            f"Source: {j['source']}\nLink: {j['url']}")

@app.route("/")
def index():
    status = request.args.get("status", "new")
    if status not in VALID:
        status = "new"
    kind = request.args.get("kind", "jobs")
    if kind not in ("jobs", "posts"):
        kind = "jobs"
    jobs = db.jobs_by_status(status, kind)
    for j in jobs:
        j["claude_prompt"] = claude_prompt(j)
        j["matched_list"] = [m for m in (j.get("matched") or "").split(",") if m]
        j["age"] = age_str(j.get("posted"))
        j["emp_label"] = score.EMP_LABEL.get(j.get("employment", "full_time"), "")
        j["ai_gig"] = score.is_ai_eval_gig(j)
        j["reach_label"] = score.REACH_LABEL.get(j.get("reach", ""), "")
    scanning = _scan["running"]
    found = _scan["found"]
    if not scanning and found is not None:
        _scan["found"] = None   # consume so the banner shows once
    return render_template("dashboard.html", jobs=jobs, status=status, kind=kind,
                           tabs=TABS, counts=db.counts(kind), kind_counts=db.kind_counts(),
                           scanning=scanning, scan_found=found, scan_tier=_scan.get("tier", ""))

@app.route("/action", methods=["POST"])
def action():
    new_status = request.form.get("status", "")
    if new_status in VALID:
        db.set_status(request.form["id"], new_status)
    return redirect(f"/?status={request.form.get('back', 'new')}&kind={request.form.get('kind', 'jobs')}")

@app.route("/run", methods=["POST"])
def run_scan():
    tier = request.form.get("tier", "all")
    if tier not in ("free", "all"):
        tier = "all"
    if not _scan["running"]:
        _scan["running"] = True
        _scan["found"] = None
        _scan["tier"] = tier
        threading.Thread(target=_run_scan, args=(tier,), daemon=True).start()
    return redirect(f"/?status={request.form.get('back', 'new')}&kind={request.form.get('kind', 'jobs')}")

@app.route("/clear", methods=["POST"])
def clear():
    db.clear_all()
    return redirect(f"/?status=new&kind={request.form.get('kind', 'jobs')}")

if __name__ == "__main__":
    db.init()
    app.run(host="127.0.0.1", port=cfg()["dashboard"]["port"], debug=False)
