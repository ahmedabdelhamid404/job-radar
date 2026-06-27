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

# ---- timezone / work-life-balance (Cairo UTC+3) — ranking only, never excludes ----
TZ_FRIENDLY_DESC = ["async", "asynchronous", "work anywhere", "work from anywhere",
                    "anywhere in the world", "any time zone", "any timezone", "no overlap",
                    "flexible hours", "flexible schedule", "results-only", "results only",
                    "your own schedule", "fully flexible", "worldwide", "anywhere"]
TZ_FAR_DESC = ["pacific time", "pacific standard", "pacific timezone", "eastern time",
               "eastern standard", "eastern timezone", "central time", "us hours",
               "u.s. hours", "us business hours", "american business hours", "us-based hours",
               "overlap with the us", "overlap with us team", "overlap with our us",
               "overlap with us", "overlap with pst", "overlap with est", "core us hours",
               "work us hours", "us pacific", "us eastern", "us central", "us time", "u.s. time"]
TZ_ABBR_RE = re.compile(r"\b(pst|pdt|est|edt|cst|cdt|mst|mdt)\b", re.I)
TZ_FRIENDLY_LOC = ["egypt", "cairo", "giza", "alexandria", "uae", "dubai", "abu dhabi",
                   "saudi", "riyadh", "jeddah", "qatar", "doha", "kuwait", "bahrain", "oman",
                   "gulf", "gcc", "mena", "europe", "european", "emea", "uk", "united kingdom",
                   "england", "london", "ireland", "germany", "berlin", "france", "paris",
                   "spain", "madrid", "netherlands", "amsterdam", "portugal", "lisbon",
                   "poland", "africa"]
US_STATES = {"al","ak","az","ar","ca","co","ct","de","fl","ga","hi","id","il","in","ia",
             "ks","ky","la","me","md","ma","mi","mn","ms","mo","mt","ne","nv","nh","nj","nm",
             "ny","nc","nd","oh","ok","or","pa","ri","sc","sd","tn","tx","ut","vt","va","wa",
             "wv","wi","wy","dc"}
US_WEST = {"ca","wa","or","nv","az","ut","id","mt","wy","co","nm","hi","ak"}

# ---- LinkedIn hiring-POST detection (Arabic-priority — the hidden, low-competition market) ----
HIRING_EN = [
    "hiring", "#hiring", "we're hiring", "we are hiring", "now hiring", "now recruiting",
    "recruiting", "we're recruiting", "i'm hiring", "i am hiring", "my team is hiring",
    "we're looking for", "we are looking for", "looking for a", "looking for an",
    "looking to hire", "seeking a", "seeking an", "we're seeking", "in search of",
    "join our team", "join us", "join our growing team", "be part of our team",
    "open position", "open positions", "open role", "open roles", "role available",
    "vacancy", "vacancies", "job opening", "job openings", "job opportunity",
    "career opportunity", "exciting opportunity", "we have an opening", "opening for",
    "immediate joiners", "immediate hiring", "immediate joining", "urgent requirement",
    "urgent hiring", "urgently hiring", "apply now", "to apply", "how to apply",
    "send your cv", "send your resume", "share your cv", "drop your cv", "send cv",
    "interested candidates", "dm me", "dm for", "inbox me", "reach out", "we'd love to hear",
    "we would love to hear", "wanted", "talent needed", "we're growing", "we are growing",
    # AI-written giveaways (recruiters increasingly use ChatGPT)
    "thrilled to announce", "excited to announce", "we are thrilled", "we are excited to",
    "if you're passionate", "if you are passionate", "passionate about",
]
HIRING_AR = [
    "مطلوب", "مطلوب للعمل", "مطلوب موظف", "مطلوب مطور", "مطلوب مهندس",
    "نوظف", "بنوظف", "هنوظف", "نعلن", "تعلن", "يعلن", "نعلن عن", "تعلن شركة",
    "نبحث عن", "نبحث", "نحتاج", "محتاج", "محتاجين",
    "فرصة عمل", "فرص عمل", "فرصة وظيفية", "فرص وظيفية", "فرصة توظيف",
    "وظيفة", "وظائف", "وظائف خالية", "وظيفة شاغرة", "وظائف شاغرة", "شاغرة",
    "للتقديم", "التقديم", "برجاء إرسال", "يرجى إرسال", "ارسل", "أرسل", "ابعت", "ابعتلي",
    "سيرة ذاتية", "السيرة الذاتية", "سي في",
    "التوظيف", "التعيين", "اعلان توظيف", "إعلان توظيف", "اعلان وظيفة", "إعلان وظيفة",
    "انضم", "انضم إلينا", "انضم لفريقنا", "هتنضم", "فريق العمل",
    "مطور واجهات", "واجهات أمامية", "فرونت اند", "فرونت إند",
]
ARABIC_RE = re.compile(r"[؀-ۿ]")
CONTACT_RE = re.compile(r"[\w.+-]+@[\w-]+\.[a-z]{2,}", re.I)

# A LinkedIn post's first line is a HOOK ("Hiring !!", "#Hiring", "🚀"), not the role — so the
# advertised role must be read from the WHOLE body. These let us decide if a post is actually
# about a front-end/Angular position vs a skill-soup blast where Angular is one of 20 tags.
FE_ROLE = [
    "angular developer", "angular engineer", "angular dev", "frontend developer",
    "front-end developer", "front end developer", "frontend engineer", "front-end engineer",
    "front end engineer", "frontend dev", "front-end dev", "ui developer", "ui engineer",
    "ui/ux developer", "web front", "مطور angular", "مطور أنجولار", "مطور انجولار",
    "مطور واجهات", "مطور فرونت", "فرونت اند", "فرونت إند",
]
NON_FE_ROLE = [
    "full stack", "full-stack", "fullstack", "backend", "back-end", "back end",
    "supply chain", "production support", "applications development analyst",
    "application development analyst", "data engineer", "data analyst", "data scientist",
    "devops", "site reliability", "sre engineer", "qa engineer", "test engineer",
    "automation engineer", "salesforce", "workday", "scrum master", "project manager",
    "business analyst", "product manager", "mobile developer", "android developer",
    "ios developer", "java developer", ".net developer", "dotnet developer",
    "python developer", "php developer", "node developer", "node.js developer",
    "golang developer", "ruby developer", "database administrator", "network engineer",
    "system administrator", "cloud engineer", "ml engineer", "ai engineer", "embedded",
]
# US bench-sales / C2C tells — work-authorization-gated, categorically useless from Egypt.
US_STAFFING_RE = re.compile(
    r"\b(c2c|corp[ -]to[ -]corp|w2|1099|usc|gc|ead|h1b|h-1b|opt|cpt|tn visa|"
    r"green card|us citizen|only locals|must be local|onsite from day)\b", re.I)
# generic multi-stack blast detection (Angular incidental among many)
BLAST_TERMS = [".net", "dotnet", "react", "python", " php", "devops", "salesforce", " sap"]
# job-SEEKER-facing advice / career-coaching content — NOT a vacancy. High-precision phrases
# only (never appear in a real job ad — note "send your resume" must stay safe).
SEEKER_NOISE = [
    "flooded with candidates", "how to stand out", "stand out from the", "how to get hired",
    "job seekers", "resume tips", "linkedin tips", "optimize your linkedin", "optimize your profile",
    "personal branding", "career coaching", "i help candidates", "i help engineers",
    "i help job", "generic keyword", "keyword searches", "tips to land", "land your dream",
]
# AI-training / data-labeling gigs dressed as Angular jobs — you CRITIQUE code to train a model,
# you never build production apps. Reachable but zero portfolio value -> sink to the bottom.
AI_GIG_COMPANIES = ["micro1", "mercor", "remotasks", "dataannotation", "data annotation",
                    "surge ai", "surgehq", "scale ai", "invisible technologies", "labelbox",
                    "alignerr", "snorkel ai", "toloka", "telus international", "outlier ai",
                    "handshake ai"]
AI_GIG_DEFINITIVE = [
    "ai data lab", "train ai", "training ai", "train next-generation ai", "train frontier",
    "training frontier model", "frontier model", "frontier ai", "evaluate ai agent",
    "evaluating ai agent", "guide model learning", "how models learn", "shape how models",
    "rlhf", "reinforcement learning from human feedback", "ai training data",
    "no prior experience in ai is required", "improve how ai", "data annotation",
    "data labeling", "data labelling", "label training data", "human intelligence layer",
]
AI_GIG_SOFT = ["training data", "human feedback", "feedback loops", "evaluate ai",
               "ai systems learn", "high-quality training", "annotate", "labeling tasks"]

def is_ai_eval_gig(j):
    """True for AI-training / data-annotation gigs (micro1/Mercor/Outlier-style) — reviewing code
    to train models, not building apps. High-precision: known lab, a definitive phrase, or 2+ soft."""
    blob = (f"{j.get('title','')} {j.get('company','')} {j.get('location','')} "
            f"{j.get('description','')}").lower()
    if any(co in blob for co in AI_GIG_COMPANIES):
        return True
    if any(p in blob for p in AI_GIG_DEFINITIVE):
        return True
    return sum(1 for p in AI_GIG_SOFT if p in blob) >= 2

# --- employment type: flag contract / part-time / full-time (fallback full-time when unclear) ---
EMP_CONTRACT_STRONG = re.compile(
    r"\b(contractor|freelance(?:r)?|fixed[- ]term|day rate|ir35|c2c|corp[- ]to[- ]corp|"
    r"1099|contract[- ]to[- ]hire|temporary)\b", re.I)
EMP_CONTRACT_WEAK = re.compile(r"\bcontract\b", re.I)
EMP_PART_RE = re.compile(r"\b(part[- ]time|parttime|p/t)\b", re.I)
EMP_PERM_RE = re.compile(r"\b(permanent|full[- ]time|fulltime|perm)\b", re.I)
EMP_LABEL = {"contract": "📄 Contract", "part_time": "⏳ Part-time", "full_time": "🗓️ Full-time"}

def employment_type(j):
    """contract | part_time | full_time. Reads title+tags+description (LinkedIn/Indeed put the type
    in tags). 'permanent' beats a bare 'contract' word; nothing clear -> full_time (Ahmed's default)."""
    blob = (f"{j.get('title','')} {' '.join(str(x) for x in (j.get('tags') or []))} "
            f"{j.get('description','')}")
    if EMP_CONTRACT_STRONG.search(blob):
        return "contract"
    if EMP_PART_RE.search(blob):
        return "part_time"
    if EMP_PERM_RE.search(blob):
        return "full_time"
    if EMP_CONTRACT_WEAK.search(blob):       # bare "contract" only when no permanent/part-time signal
        return "contract"
    return "full_time"                       # unclear -> full time

# --- reachability from Egypt: can Ahmed actually take it without relocating? Best-effort: the real
# work-auth rule usually lives on the ATS behind "Apply", not in the JD, so flag ONLY on real
# evidence and stay NEUTRAL when the text is silent (never falsely mark a reachable job as locked). ---
GLOBAL_FRIENDLY = ["work from anywhere", "anywhere in the world", "from any country",
                   "any country in the world", "globally remote", "global remote",
                   "remote worldwide", "worldwide remote", "fully distributed", "hiring worldwide",
                   "work from any location", "international applicants", "contractors welcome",
                   "open to contractors", "independent contractor", "via deel", "we use deel",
                   "employer of record", " eor ", "no matter where you live",
                   "no matter where you are", "timezone agnostic", "work from any timezone"]
LOCKED_EXPLICIT = ["authorized to work in", "must be authorized to work", "us citizen",
                   "u.s. citizen", "citizens only", "green card", "us person", "u.s. person",
                   "must reside in", "must be located in", "must be based in", "right to work in",
                   "eligible to work in", "valid work authorization", "work authorization in",
                   "no visa sponsorship", "not able to sponsor", "unable to sponsor",
                   "cannot sponsor", "without sponsorship", "remote within", "us-based only",
                   "security clearance", "active clearance", "ts/sci", "secret clearance",
                   "obtain a clearance", "itar", "legally authorized", "work permit"]
DEFENSE_GOV = ["national security", "defense contractor", "department of defense", " dod ",
               "intelligence community", "mission-based operating", "government contract",
               "federal contract", "public trust clearance"]
_COUNTRY_ALT = (r"(?:u\.?s\.?a?|united states|united kingdom|uk|england|scotland|wales|germany|"
                r"deutschland|canada|australia|netherlands|france|ireland|switzerland|sweden|norway|"
                r"denmark|finland|spain|italy|portugal|poland|belgium|austria|czech|romania|"
                r"singapore|new zealand|japan|south korea|india|mexico|brazil|argentina)")
FAR_COUNTRY_RE = re.compile(r"\b" + _COUNTRY_ALT + r"\b", re.I)              # location names a far country
# "remote from anywhere in Germany" / "within the US" / "based in the UK" — country bound, in the body
LOCKED_GEO_RE = re.compile(
    r"\b(?:anywhere in|within|based in|located in|reside in|residing in|remote (?:from|in|within))"
    r"\s+(?:the\s+)?" + _COUNTRY_ALT + r"\b", re.I)
REACH_LABEL = {"global": "✅ global-remote", "locked": "🌐 country-locked",
               "soft": "🌐 verify location"}

def reachability(j):
    """'global' = explicitly worldwide/contractor-friendly; 'locked' = needs local work rights
    (citizenship/clearance/defense, 'remote within <country>', no sponsorship); 'soft' = location
    names a far country with no global wording (verify on the company site — often hidden there);
    '' = unknown -> stay neutral. NOTE: best-effort; LinkedIn JDs usually omit the real work-auth rule."""
    blob = (f"{j.get('title','')} {j.get('location','')} "
            f"{' '.join(str(x) for x in (j.get('tags') or []))} {j.get('description','')}").lower()
    if (any(p in blob for p in LOCKED_EXPLICIT) or any(p in blob for p in DEFENSE_GOV)
            or LOCKED_GEO_RE.search(blob)):
        return "locked"
    if any(p in blob for p in GLOBAL_FRIENDLY):
        return "global"
    if FAR_COUNTRY_RE.search(j.get("location") or ""):   # location bound to a specific far country
        return "soft"
    return ""

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

def timezone_fit(j):
    """(delta, label) for work-life-balance vs Cairo (UTC+3). Ranking only — never excludes.
    Description requirements win; location is the fallback signal."""
    loc = (j["location"] or "").lower()
    desc = (j.get("description") or "").lower()
    if any(p in (loc + " " + desc) for p in TZ_FRIENDLY_DESC):
        return 12, "🌍 async/any-tz"
    if any(p in desc for p in TZ_FAR_DESC):
        return -15, "🌙 US-hours req"
    m = re.search(r",\s*([a-z]{2})\b", loc)          # "City, CA" style suffix
    st = m.group(1) if m else ""
    if st in US_WEST or any(w in loc for w in ["pacific", "san francisco", "los angeles", "seattle"]):
        return -15, "🌙 US-West"
    if (st in US_STATES or re.search(r"\b(us|usa)\b", loc)
            or any(w in loc for w in ["u.s", "united states", "america", "canada", "brazil", "mexico"])):
        return -8, "🌆 US/Americas"
    if any(f in loc for f in TZ_FRIENDLY_LOC):
        return 10, "✅ your tz"
    if TZ_ABBR_RE.search(desc):
        return -6, "🌙 US-tz?"
    return 0, ""

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
    s += timezone_fit(j)[0]                          # work-life-balance vs Cairo timezone
    if any(sr in title for sr in SENIOR):
        s += 12
    elif "mid" in title:
        s += 4
    if any(jr in title for jr in JUNIOR):
        s -= 25
    if is_remote(j):
        s += 6
    rk = reachability(j)
    if rk == "global":
        s += 8                                       # explicitly worldwide / contractor-friendly
    elif rk == "soft":
        s -= 12                                      # location-bound to a far country (verify)
    s = max(0, min(100, s))
    if is_ai_eval_gig(j):
        s = min(s, 15)                               # AI-training/data-labeling gig — sink to the bottom
    if rk == "locked":
        s = min(s, 18)                               # needs local work rights — sink, never exclude
    return s, matched, tr

def is_arabic(text):
    return bool(ARABIC_RE.search(text or ""))

def is_hiring_post(text):
    t = (text or "").lower()
    if any(k in t for k in HIRING_EN):
        return True
    if any(k in (text or "") for k in HIRING_AR):       # Arabic — don't lowercase
        return True
    if CONTACT_RE.search(text or ""):                   # an apply-to email = hiring intent
        return True
    return any(k in t for k in ["cv", "resume", "apply", "inbox", "dm "])

def blast_count(text_lower):
    """How many distinct non-Angular primary stacks the post lists (Angular incidental if high)."""
    return (1 if JAVA_RE.search(text_lower) else 0) + sum(1 for o in BLAST_TERMS if o in text_lower)

def relevant_post(j, cfg):
    """A post is kept ONLY if it actually advertises an Angular / front-end role.
    The role is read from the WHOLE body (the first line is just a hook on LinkedIn).
    Trusted Arabic channel stays lenient; every English post must name a real FE role."""
    text = f"{j.get('title','')} {j.get('description','')}"
    tl = text.lower()
    if "angular" not in tl:                      # stay Angular-focused
        return False
    if not is_hiring_post(text):                 # genuine hiring intent (drops tutorials/opinion)
        return False
    if any(p in tl for p in SEEKER_NOISE):       # career-coaching / job-seeker advice, not a vacancy
        return False
    has_fe_role = any(r in tl for r in FE_ROLE) or any(r in text for r in FE_ROLE)
    has_non_fe_role = any(r in tl for r in NON_FE_ROLE)
    # the first line, WHEN it names a role, is authoritative: "Java Developer – Front End (Angular)"
    # is a Java role, not a front-end one. Drop if the headline names a non-FE role and no FE role.
    title = j.get("title", "")
    title_l = title.lower()
    title_fe = any(r in title_l for r in FE_ROLE) or any(r in title for r in FE_ROLE)
    if any(r in title_l for r in NON_FE_ROLE) and not title_fe:
        return False
    # NOTE: US bench-sales (C2C/W2/OPT/USC/GC/EAD) is NOT excluded — Ahmed wants posts worldwide.
    # It's ranked DOWN in score_post instead (same "rank, never exclude" rule as far-tz jobs).
    if any(x in tl for x in cfg["profile"].get("exclude_terms", [])) and not has_fe_role:
        return False                             # junior/intern blast (unless explicitly an FE role)
    if has_non_fe_role and not has_fe_role:      # advertised role is backend/full-stack/data/etc.
        return False
    if blast_count(tl) >= 2 and not has_fe_role: # generic multi-tech staffing blast
        return False
    # --- positive gate ---
    if is_arabic(text):                          # trusted Arabic/Egyptian channel: lenient
        return True
    return has_fe_role                           # any English post must name an actual FE/Angular role

def poster_region(j):
    """Region of the POSTER, from headline (location field) + name + post text."""
    blob = f"{j.get('location','')} {j.get('company','')} {j.get('description','')}".lower()
    if any(w in blob for w in EGYPT):
        return "egypt"
    if any(w in blob for w in GULF):
        return "gulf"
    return None

def score_post(j, cfg):
    text = f"{j.get('title','')} {j.get('description','')}"
    t = text.lower()
    reg = poster_region(j)
    s = 50
    if reg == "egypt":
        s += 30                              # Egyptian poster = rank 1 (Ahmed's proven channel)
    elif reg == "gulf":
        s += 18                              # MENA/Gulf = rank 2
    if is_arabic(text):
        s += 8
    s += 3 * min(sum(1 for d in DEPTH if d in t), 4)
    if any(sr in t for sr in SENIOR):
        s += 5
    if "remote" in t or "عن بعد" in text:
        s += 4
    tz_delta, tz_label = timezone_fit(j)     # same work-life-balance rule as jobs — rank, never exclude
    s += tz_delta
    if US_STAFFING_RE.search(text):          # US C2C/W2/visa-gated bench post — keep but sink it
        s -= 20
    if blast_count(t) >= 2:
        s -= 18                              # generic multi-tech staffing blast, not Angular-focused
    rk = reachability(j)
    if rk == "global":
        s += 8
    elif rk == "soft":
        s -= 12
    s = max(0, min(100, s))
    ai = is_ai_eval_gig(j)
    if ai:
        s = min(s, 15)                       # AI-training/data-labeling gig — sink to the bottom
    if rk == "locked":
        s = min(s, 18)                       # needs local work rights — sink, never exclude
    matched = [sk for sk in cfg["profile"]["skills"] if sk.lower() in t][:6]
    base = {"egypt": "📣🇪🇬 Egyptian hiring post",
            "gulf": "📣🕌 MENA hiring post"}.get(reg, "📣🌍 hiring post")
    bits = [b for b in (("🤖 AI-eval gig" if ai else ""), REACH_LABEL.get(rk, ""), base, tz_label) if b]
    label = " · ".join(bits)
    return s, (matched or ["Angular"]), label, reg

def pick_cv(j):
    r = region(j)
    return {"gulf": "Gulf", "egypt": "Egypt"}.get(r, "International")

def market_of(j):
    return region(j) or "remote/intl"

def pitch(j, matched, cv, tier_label="", tz_label="", ai_gig=False, emp_label="", reach_label=""):
    top = ", ".join(matched[:5]) if matched else "your Angular / front-end stack"
    bits = [b for b in (("🤖 AI-eval gig" if ai_gig else ""), reach_label, emp_label,
                        tier_label, tz_label) if b]
    lead = (" · ".join(bits) + " · ") if bits else ""
    return f"{lead}Matches {top}. Recommended CV: {cv}."
