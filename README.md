# 📡 Job Radar

Automated daily Angular / front-end job discovery → a local dashboard you triage → you apply (with Claude's help for cover letters & interview prep).

Built for a **deep Angular/front-end specialist** targeting **remote / hybrid-in-Egypt** roles across **Remote-International, Gulf, and Egypt** markets.

## What it does
1. **6×/day** (cron, Cairo time) it pulls listings from ~6–8 legal job sources.
2. **Filters** to remote (any market) or hybrid-in-Egypt Angular & front-end roles, drops onsite/relocation.
3. **Dedups** against everything seen before, **scores fit (0–100)**, and **picks which CV** to use (International / Gulf / Egypt).
4. **Saves** to a local SQLite DB and **alerts you only when there are NEW matches** (Telegram / desktop / email).
5. A **local web dashboard** lets you triage: **Inbox → Applied / Interviewing / Dismissed**, with a **📋 Copy for Claude** button that hands a ready prompt to Claude Code for a tailored cover letter or interview prep.

## Access the dashboard
- Double-click the **Job Radar** launcher on your Desktop, **or** run `./dashboard.sh`.
- Opens **http://localhost:5000** — local-only, never exposed to the internet.

## CVs
Tailored CVs live in **`~/Documents/cvs/`** (`Ahmed-Abdelhamid-CV-International/Gulf/Egypt.pdf` + `.docx`). The dashboard's Claude prompt points here.

## Setup
```bash
pip3 install --user -r requirements.txt
cp config.example.yaml config.yaml     # then fill in your keys
python3 radar.py                        # test run
```
Cron (6×/day) and the dashboard launcher are installed during setup.

## Job sources
**No key:** RemoteOK, Remotive, Arbeitnow, Jobicy, Himalayas, We Work Remotely.
**Free key (more depth + Gulf/Egypt):** Jooble, Adzuna.

## Keys → `config.yaml`
| Key | Unlocks | Get it |
|---|---|---|
| `jooble` | Gulf + Egypt + global aggregation | https://jooble.org/api/about |
| `telegram_token` + `telegram_chat_id` | Phone alerts | @BotFather |
| `adzuna_app_id` + `adzuna_app_key` | More intl depth (optional) | https://developer.adzuna.com |

## How scoring works
Fast, deterministic heuristic: skill keyword matches + Angular/front-end in title + seniority + remote bonus. No LLM in the cron path (rock-solid, free). The LLM (Claude) is used *on demand* via the dashboard's Copy-for-Claude button.

## Honest limits
- **No LinkedIn / Wuzzuf / Bayt** — they have no legal candidate API and ban scrapers; do a quick manual scan there too.
- Remote/hybrid detection is heuristic (keyword-based).
- **Applying is manual by design** — safer (no account bans) and higher quality than auto-apply.

## Files
- `radar.py` — fetch → filter → dedup → score → save → alert (run by cron)
- `sources.py` — one fetcher per job source
- `score.py` — relevance, work-style filter, fit score, CV pick
- `alerts.py` — Telegram / desktop / email
- `dashboard.py` + `templates/` — local triage web app
- `db.py` — SQLite layer · `config.yaml` — your settings (gitignored)
- `run.sh` — cron entry · `dashboard.sh` — launcher
