import json
from pathlib import Path
from datetime import datetime, timezone

SPEND_FILE = Path(__file__).parent / "spend.json"

def _month():
    return datetime.now(timezone.utc).strftime("%Y-%m")

def _load():
    try:
        return json.loads(SPEND_FILE.read_text())
    except Exception:
        return {}

def spent():
    return float(_load().get(_month(), 0.0))

def add(cost):
    data = _load()
    m = _month()
    data[m] = round(data.get(m, 0.0) + float(cost), 4)
    SPEND_FILE.write_text(json.dumps(data))
    return data[m]
