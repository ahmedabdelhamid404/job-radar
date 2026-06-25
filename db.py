import sqlite3, time
from pathlib import Path

DB_PATH = Path(__file__).parent / "jobs.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    id TEXT PRIMARY KEY,
    title TEXT, company TEXT, location TEXT, url TEXT,
    source TEXT, market TEXT, remote TEXT,
    score INTEGER, cv TEXT, pitch TEXT, matched TEXT, posted REAL,
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

def exists(c, job_id):
    return c.execute("SELECT 1 FROM jobs WHERE id=?", (job_id,)).fetchone() is not None

def insert_job(c, j):
    now = time.time()
    c.execute(
        """INSERT OR IGNORE INTO jobs
           (id,title,company,location,url,source,market,remote,score,cv,pitch,matched,posted,status,first_seen,last_seen)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,'new',?,?)""",
        (j["id"], j["title"], j["company"], j["location"], j["url"], j["source"],
         j["market"], j["remote"], j["score"], j["cv"], j["pitch"],
         ",".join(j.get("matched", [])), j.get("posted"), now, now),
    )

def set_status(job_id, status):
    with conn() as c:
        c.execute("UPDATE jobs SET status=?, last_seen=? WHERE id=?", (status, time.time(), job_id))

def jobs_by_status(status):
    with conn() as c:
        rows = c.execute(
            "SELECT * FROM jobs WHERE status=? ORDER BY score DESC, posted DESC, first_seen DESC", (status,)
        ).fetchall()
    return [dict(r) for r in rows]

def counts():
    with conn() as c:
        rows = c.execute("SELECT status, COUNT(*) n FROM jobs GROUP BY status").fetchall()
    return {r["status"]: r["n"] for r in rows}

def clear_all():
    with conn() as c:
        c.execute("DELETE FROM jobs")
