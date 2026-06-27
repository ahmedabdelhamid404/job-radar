import sqlite3, time
from pathlib import Path

DB_PATH = Path(__file__).parent / "jobs.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    id TEXT PRIMARY KEY,
    title TEXT, company TEXT, location TEXT, url TEXT,
    source TEXT, market TEXT, remote TEXT,
    score INTEGER, cv TEXT, pitch TEXT, matched TEXT, posted REAL,
    employment TEXT DEFAULT 'full_time',
    reach TEXT DEFAULT '',
    status TEXT DEFAULT 'new',
    first_seen REAL, last_seen REAL
);
"""

def conn():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c

def init():
    with conn() as c:
        c.executescript(SCHEMA)
        cols = {r["name"] for r in c.execute("PRAGMA table_info(jobs)")}
        if "employment" not in cols:                      # migrate older DBs
            c.execute("ALTER TABLE jobs ADD COLUMN employment TEXT DEFAULT 'full_time'")
        if "reach" not in cols:
            c.execute("ALTER TABLE jobs ADD COLUMN reach TEXT DEFAULT ''")

def exists(c, job_id):
    return c.execute("SELECT 1 FROM jobs WHERE id=?", (job_id,)).fetchone() is not None

def insert_job(c, j):
    now = time.time()
    c.execute(
        """INSERT OR IGNORE INTO jobs
           (id,title,company,location,url,source,market,remote,score,cv,pitch,matched,posted,employment,reach,status,first_seen,last_seen)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,'new',?,?)""",
        (j["id"], j["title"], j["company"], j["location"], j["url"], j["source"],
         j["market"], j["remote"], j["score"], j["cv"], j["pitch"],
         ",".join(j.get("matched", [])), j.get("posted"),
         j.get("employment", "full_time"), j.get("reach", ""), now, now),
    )

def set_status(job_id, status):
    with conn() as c:
        c.execute("UPDATE jobs SET status=?, last_seen=? WHERE id=?", (status, time.time(), job_id))

POST_SOURCE = "LinkedIn Post"

def _kind_clause(kind):
    return "source = ?" if kind == "posts" else "source <> ?"

def jobs_by_status(status, kind="jobs"):
    with conn() as c:
        rows = c.execute(
            f"SELECT * FROM jobs WHERE status=? AND {_kind_clause(kind)} "
            "ORDER BY score DESC, posted DESC, first_seen DESC", (status, POST_SOURCE)
        ).fetchall()
    return [dict(r) for r in rows]

def counts(kind="jobs"):
    with conn() as c:
        rows = c.execute(
            f"SELECT status, COUNT(*) n FROM jobs WHERE {_kind_clause(kind)} GROUP BY status",
            (POST_SOURCE,)).fetchall()
    return {r["status"]: r["n"] for r in rows}

def kind_counts():
    with conn() as c:
        posts = c.execute("SELECT COUNT(*) n FROM jobs WHERE source=?", (POST_SOURCE,)).fetchone()["n"]
        jobs = c.execute("SELECT COUNT(*) n FROM jobs WHERE source<>?", (POST_SOURCE,)).fetchone()["n"]
    return {"jobs": jobs, "posts": posts}

def clear_all():
    with conn() as c:
        c.execute("DELETE FROM jobs")
