#!/usr/bin/env python3
from flask import Flask, render_template, request, redirect
from pathlib import Path
import yaml, db, time

ROOT = Path(__file__).parent
app = Flask(__name__)

TABS = [("new", "📥 Inbox"), ("applied", "✅ Applied"),
        ("interviewing", "🎯 Interviewing"), ("dismissed", "🗑️ Dismissed")]
VALID = {"new", "applied", "interviewing", "dismissed"}

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
    jobs = db.jobs_by_status(status)
    for j in jobs:
        j["claude_prompt"] = claude_prompt(j)
        j["matched_list"] = [m for m in (j.get("matched") or "").split(",") if m]
        j["age"] = age_str(j.get("posted"))
    return render_template("dashboard.html", jobs=jobs, status=status,
                           tabs=TABS, counts=db.counts())

@app.route("/action", methods=["POST"])
def action():
    new_status = request.form.get("status", "")
    if new_status in VALID:
        db.set_status(request.form["id"], new_status)
    return redirect("/?status=" + request.form.get("back", "new"))

if __name__ == "__main__":
    db.init()
    app.run(host="127.0.0.1", port=cfg()["dashboard"]["port"], debug=False)
