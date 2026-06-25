GULF = ["uae", "u.a.e", "united arab", "dubai", "abu dhabi", "saudi", "ksa", "riyadh",
        "jeddah", "qatar", "doha", "kuwait", "bahrain", "oman", "gulf", "gcc"]
EGYPT = ["egypt", "cairo", "giza", "alexandria", "obour", "october", "مصر", "القاهرة"]
REMOTE_WORDS = ["remote", "work from home", "wfh", "anywhere", "worldwide", "distributed", "عن بعد"]
HYBRID_WORDS = ["hybrid", "هجين"]
SENIOR = ["senior", "lead", "principal", "staff", "sr."]
JUNIOR = ["junior", "intern", "trainee", "graduate", "apprentice"]
FE = ["frontend", "front-end", "front end"]

def text_of(j):
    return f"{j['title']} {j['location']} {' '.join(j.get('tags') or [])} {j['description']}".lower()

def is_remote(j):
    if j.get("remote") is True:
        return True
    return any(w in text_of(j) for w in REMOTE_WORDS)

def is_hybrid(j):
    return any(w in text_of(j) for w in HYBRID_WORDS)

def region(j):
    t = j["location"].lower()
    if any(w in t for w in GULF):
        return "gulf"
    if any(w in t for w in EGYPT):
        return "egypt"
    return None

def passes_workstyle(j, cfg):
    ws = cfg["work_style"]
    if is_remote(j) and ws.get("remote"):
        return True
    if is_hybrid(j) and ws.get("hybrid_egypt") and region(j) == "egypt":
        return True
    return False

def relevant(j, cfg):
    title = j["title"].lower()
    tags = " ".join(j.get("tags") or []).lower()
    p = cfg["profile"]
    if any(x in title for x in p.get("exclude_terms", [])):
        return False
    must = p.get("must_have_any", ["angular"])
    return (any(m in title or m in tags for m in must)
            or any(f in title for f in FE))

def score(j, cfg):
    t = text_of(j)
    title = j["title"].lower()
    s = 0
    matched = []
    for sk in cfg["profile"]["skills"]:
        if sk.lower() in t:
            matched.append(sk)
            s += 6
    if "angular" in title:
        s += 25
    elif "angular" in t:
        s += 10
    if any(f in title for f in FE):
        s += 12
    if any(sr in title for sr in SENIOR):
        s += 15
    elif "mid" in title:
        s += 5
    if any(jr in title for jr in JUNIOR):
        s -= 20
    if is_remote(j):
        s += 8
    return max(0, min(100, s)), matched

def pick_cv(j):
    r = region(j)
    return {"gulf": "Gulf", "egypt": "Egypt"}.get(r, "International")

def market_of(j):
    return region(j) or "remote/intl"

def pitch(j, matched, cv):
    top = ", ".join(matched[:5]) if matched else "your Angular / front-end stack"
    return f"Matches {top}. Recommended CV: {cv}."
