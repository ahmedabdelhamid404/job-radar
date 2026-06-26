import re, time

GULF = ["uae", "u.a.e", "united arab", "dubai", "abu dhabi", "saudi", "ksa", "riyadh",
        "jeddah", "qatar", "doha", "kuwait", "bahrain", "oman", "gulf", "gcc"]
EGYPT = ["egypt", "cairo", "giza", "alexandria", "obour", "october", "مصر", "القاهرة"]
REMOTE_WORDS = ["remote", "work from home", "wfh", "anywhere", "worldwide", "distributed", "عن بعد"]
HYBRID_WORDS = ["hybrid", "هجين"]
SENIOR = ["senior", "lead", "principal", "staff", "sr."]
JUNIOR = ["junior", "intern", "trainee", "graduate", "apprentice"]
FE = ["frontend", "front-end", "front end"]
JAVA_RE = re.compile(r"\bjava\b", re.I)   # whole word — never matches "javascript"
# competing front-end frameworks: fine ALONGSIDE Angular, but a title naming one of these
# WITHOUT Angular = a React/Vue-primary role -> dropped (the "where is Angular?" case).
COMPETING = ["react", "reactjs", "react.js", "react native", "vue", "vuejs", "vue.js",
             "svelte", "sveltekit", "next.js", "nextjs", "nuxt", "ember", "backbone", "blazor"]
# Tier D gate: a description-only Angular match counts ONLY if the TITLE is clearly a
# front-end / web / UI role — NOT DevOps, data, QA, security, mobile, RPG, generic "software".
FRONTEND_TITLE = ["frontend", "front-end", "front end", "web developer", "web engineer",
                  "ui developer", "ui engineer", "ui/ux", "javascript", "typescript"]
TIER_BONUS = {"A": 45, "B": 30, "C": 18, "D": 10}
TIER_LABEL = {"A": "⭐ Clean Angular", "B": "Angular-led", "C": "Angular (mixed)", "D": "Angular in description"}
# Angular-ecosystem signals that mean the role genuinely fits Ahmed's CV
DEPTH = ["rxjs", "ngrx", "signal", "nx ", "micro frontend", "micro-frontend", "ssr",
         "hydration", "angular material", " cdk", "esbuild", "standalone"]

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

def is_backend_primary(title, cfg):
    t = title.lower()
    if any(s in t for s in cfg["profile"].get("exclude_stacks", [])):
        return True
    return bool(JAVA_RE.search(t))

def relevant(j, cfg):
    title = j["title"].lower()
    tags = " ".join(j.get("tags") or []).lower()
    desc = (j.get("description") or "").lower()
    p = cfg["profile"]
    if any(x in title for x in p.get("exclude_terms", [])):
        return False
    if is_backend_primary(j["title"], cfg):          # backend / full-stack / .NET / Java
        return False
    ang_title = "angular" in title
    competing_title = any(c in title for c in COMPETING)
    if competing_title and not ang_title:            # React/Vue-primary title -> drop
        return False
    if ang_title or "angular" in tags:               # Angular named in title/tags -> keep
        return True
    # generic front-end / web / UI title + Angular in the body (Tier D)
    if not competing_title and "angular" in desc and any(d in title for d in FRONTEND_TITLE):
        return True
    return False

def tier(j):
    title = j["title"].lower()
    tags = " ".join(j.get("tags") or []).lower()
    ang_title = "angular" in title
    comp = [c for c in COMPETING if c in title]
    if ang_title and not comp:
        return "A"                                   # clean Angular title
    if ang_title and comp:                           # Angular + another framework in title
        return "B" if title.index("angular") < min(title.index(c) for c in comp) else "C"
    if "angular" in tags:
        return "B"
    return "D"                                       # Angular in the body only

def fresh(j, cfg):
    posted = j.get("posted")
    if posted is None:
        return True
    max_age = cfg.get("search", {}).get("max_age_days", 2)
    return posted >= time.time() - max_age * 86400

def score(j, cfg):
    t = text_of(j)
    title = j["title"].lower()
    s = 0
    matched = []
    for sk in cfg["profile"]["skills"]:
        if sk.lower() in t:
            matched.append(sk)
    s += 4 * min(len(matched), 6)                    # skills: secondary signal, capped at +24
    tr = tier(j)
    s += TIER_BONUS[tr]                              # Angular-primary dominates the ranking
    s += 3 * min(sum(1 for d in DEPTH if d in t), 5) # ecosystem depth = fits the CV (capped)
    if any(sr in title for sr in SENIOR):
        s += 12
    elif "mid" in title:
        s += 4
    if any(jr in title for jr in JUNIOR):
        s -= 25
    if is_remote(j):
        s += 6
    return max(0, min(100, s)), matched, tr

def pick_cv(j):
    r = region(j)
    return {"gulf": "Gulf", "egypt": "Egypt"}.get(r, "International")

def market_of(j):
    return region(j) or "remote/intl"

def pitch(j, matched, cv, tier_label=""):
    top = ", ".join(matched[:5]) if matched else "your Angular / front-end stack"
    lead = f"{tier_label} · " if tier_label else ""
    return f"{lead}Matches {top}. Recommended CV: {cv}."
