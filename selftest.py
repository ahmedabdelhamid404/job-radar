#!/usr/bin/env python3
"""Runs the REAL filter (score.relevant / tier / score) on example jobs so you can see
exactly what Job Radar keeps and drops, and why. Run: python3 selftest.py"""
import yaml
from pathlib import Path
import score

cfg = yaml.safe_load(open(Path(__file__).parent / "config.yaml"))

def J(title, desc="", tags=None, loc="Remote"):
    return {"title": title, "description": desc, "tags": tags or [], "location": loc}

# ---- 25 that SHOULD be selected (Angular-primary, or Angular in a front-end body) ----
SELECT = [
    J("Senior Angular Developer (Remote)"),
    J("Angular Developer", loc="Cairo, Egypt"),
    J("Angular Engineer", desc="Angular 17, RxJS, NgRx, standalone components"),
    J("Principal Angular Developer (Angular 19, Signals)"),
    J("Lead Angular Developer", loc="Dubai, UAE"),
    J("Angular Frontend Engineer", desc="Nx monorepo, micro-frontend, SSR, hydration"),
    J("Remote Angular Developer", desc="Tailwind, Bootstrap, Angular Material, CDK"),
    J("Mid-Level Angular Developer"),
    J("Angular.js Developer"),
    J("Senior Software Engineer - Angular"),
    J("Front End Engineer - Angular & RxJS"),
    J("Angular Developer (Hybrid)", loc="Giza, Egypt"),
    J("Frontend Developer (Angular, React)"),
    J("Angular / React Developer"),
    J("React / Angular Developer"),
    J("Vue / Angular Engineer"),
    J("Senior Frontend Engineer", desc="strong Angular required, RxJS, reactive forms"),
    J("Front-End Developer", desc="Angular + TypeScript, SCSS"),
    J("Web Developer", desc="building SPAs in Angular, REST APIs"),
    J("UI Engineer", desc="Angular Material, CDK, design system"),
    J("TypeScript Developer", desc="Angular, NgRx, signals"),
    J("Frontend Web Developer", desc="Angular, HTML, CSS, REST"),
    J("JavaScript Developer", desc="Angular SPA, RxJS"),
    J("Senior Angular Developer", desc="SSR, esbuild, Angular 21 migration"),
    J("Angular Developer", desc="Micro Frontend architecture, Nx", loc="Remote - Worldwide"),
]

# ---- 25 that SHOULD be dropped ----
DROP = [
    J("React Developer"),
    J("React.js Developer"),
    J("Vue.js Engineer"),
    J("Senior React Native Developer"),
    J("Svelte Frontend Developer"),
    J("Frontend Developer (React, Redux)"),
    J("Vue Frontend Developer", desc="Angular a plus / nice to have"),
    J("Full-Stack Angular Developer"),
    J("Full Stack Developer", desc="Angular front, Node back"),
    J("Java Full Stack Developer (with Angular)"),
    J(".NET Developer with Angular"),
    J("ASP.NET Core Developer", desc="Angular front-end"),
    J("Backend Developer", desc="APIs, microservices, some Angular"),
    J("Backend Node.js Engineer"),
    J("Senior DevOps Engineer", desc="CI/CD; stack includes Angular, React, Python"),
    J("RPG Engineer", desc="IBM RPG; the team also uses Angular"),
    J("Quality Engineering Manager", desc="test Angular and React apps"),
    J("Cyber Security Analyst", desc="review Angular and Java code"),
    J("Data Scientist", desc="Python, ML; some Angular dashboards"),
    J("Software Developer", desc="general dev; Angular among many skills"),
    J("Product Manager", desc="work with the Angular team"),
    J("Mobile Developer (iOS)"),
    J("WordPress Developer"),
    J("Angular Intern"),
    J("Junior Angular Developer"),
]

# ---- timezone ranking: same Angular role, differing only by location / required hours ----
TZ = [
    J("Angular Developer", loc="Remote - Cairo, Egypt"),
    J("Angular Developer", loc="Remote - Dubai, UAE"),
    J("Angular Developer", loc="Remote - London, UK"),
    J("Angular Developer", loc="Remote - Europe"),
    J("Angular Developer", desc="fully async, work anywhere in the world", loc="Remote - US"),
    J("Angular Developer", loc="Remote", desc="standard remote role, no timezone stated"),
    J("Angular Developer", loc="New York, NY"),
    J("Angular Developer", loc="San Francisco, CA"),
    J("Angular Developer", desc="must overlap with US Pacific (PST) hours", loc="Remote - US"),
]

# ---- LinkedIn hiring posts (loc = poster headline) ----
# KEEP = genuine Angular/front-end hiring posts. Trusted Arabic/Egyptian/Gulf channel stays
# lenient; English posts (any region) must name an actual front-end/Angular ROLE.
POSTS_KEEP = [
    J("مطلوب مطور Angular", loc="HR Specialist | Hiring in Egypt",
      desc="شركة بالقاهرة تعلن عن حاجتها لمطور Angular، للتقديم برجاء إرسال السيرة الذاتية على hr@company.com"),
    J("We're hiring a Senior Angular Developer", loc="Talent Acquisition at Sword Egypt",
      desc="Cairo-based, hybrid. Strong Angular & RxJS. Send your CV to jobs@sword.eg"),
    J("Exciting opportunity!", loc="Technical Recruiter",
      desc="We are thrilled to announce we're hiring an Angular Developer. Remote, async, work anywhere. Apply now!"),
    J("Hiring Angular dev", loc="Founder at a Dubai startup",
      desc="نوظف مطور Angular للعمل من دبي. أرسل CV"),
    J("We're hiring a Frontend Engineer", loc="Engineering Manager",
      desc="Remote-friendly. Stack: Angular, RxJS, Angular Material, NgRx. Send your CV."),
]
# DROP = the 10 real posts that leaked into Ahmed's Posts tab (reconstructed from their
# LinkedIn URL slugs + poster headlines) + classic tutorial/opinion noise.
POSTS_DROP = [
    # --- the 10 real leaks ---
    J("Most Software Engineering jobs are flooded with candidates.",  # career-coach commentary, not a job
      loc="AI Talent Acquisition | Resume & LinkedIn Expert | Career Coach | Qatar Top #3 in HR",
      desc="Most software engineering jobs are flooded with candidates, yet most use generic keyword searches. Roles like Angular Developer and Front End Developer are competitive. I help engineers stand out."),
    J("Vacancy | Senior Software Developer | Waterfall, Johannesburg",  # generic, no FE role term
      loc="47,886 followers",
      desc="We have a vacancy for a Senior Software Developer. Stack: Angular, micro frontend, REST, JavaScript, C#, SQL Server."),
    J("🚨 Hiring: Supply Chain Production Support Developer 🚨",       # non-FE role
      loc="US IT Recruiter at Logic Planet INC",
      desc="Hiring a Supply Chain Production Support Developer. Skills: SAP, SQL, Angular, Java. Send CV."),
    J("#Hiring",                                                       # full-stack blast (per URL slug)
      loc="Sr. Technical Recruiter",
      desc="#immediatehiring Full Stack Developer. Java, Spring Boot, Angular, REST. C2C. Send resume."),
    J("Hello LinkedIn,",                                               # no FE role term
      loc="NA",
      desc="Hello LinkedIn, we are hiring multiple positions. Skills include Angular, TypeScript, Node, Python. DM me."),
    J("🔍 WE'RE HIRING!",                                              # OPT/CPT student bench program
      loc="Helping graduate student with full time job in USA, entry level OPT/CPT placement",
      desc="We're hiring! OPT/CPT welcome. Get hired in the USA. Skills: Angular, JavaScript. bashish@magnustechnol.com"),
    J("Hiring !!",                                                     # US C2C staffing blast
      loc="US Recruitment Specialist || W2, C2C, 1099 || USC, GC, EAD || Hiring Top IT Talent",
      desc="Hiring !! Multiple roles. Angular, JavaScript, Java, .NET. C2C only. USC/GC/EAD."),
    J("Hiring !!",                                                     # Sr Full Stack Developer (per URL slug)
      loc="US Recruitment Specialist || W2, C2C, 1099 || USC, GC, EAD",
      desc="Job Title: Sr. Full Stack Developer. Angular, .NET, SQL. C2C. Send CV."),
    J("🚀 We're Hiring | Software Engineering Contractor | Remote",    # backend developer (per URL slug)
      loc="Hiring W2 fulltime roles Across USA, UK, Canada & LATAM",
      desc="We're hiring a Backend Developer (software engineer). Node, Python, Angular, TypeScript, REST. W2."),
    J("🚀 Hiring: Applications Development Analyst 🚀",                # non-FE role
      loc="Business Development Executive at CodeInsights",
      desc="Hiring an Applications Development Analyst. Skills: Angular, REST, JavaScript, SQL, .NET."),
    J("🚨 Hiring: Java Developer – Front End (Angular) 🚨",            # Java-primary, title leads non-FE
      loc="Aspiring cybersecurity enthusiast and data analyst",
      desc="Hiring a Java Developer - Front End (Angular). Toronto, ON (4 Days/Week Onsite). Face-to-Face interview required."),
    # --- classic noise ---
    J("How Angular signals work", loc="Software Engineer",
      desc="In this post I explain Angular signals and change detection — great for learning!"),
    J("Angular vs React in 2026", loc="Tech Lead",
      desc="My personal thoughts on the tradeoffs between Angular and React this year."),
    J("We're hiring a React Developer", loc="Recruiter",
      desc="React, Redux, TypeScript. Send your CV to careers@x.com"),
    J("Java Developer Junior", loc="HR",
      desc="Java, Spring Boot, some Angular exposure. Apply now"),
]

def show_posts():
    print(f"\n{'='*72}\n  HIRING POSTS (Angular front-end roles only; Egyptian/Arabic ranked first)\n{'='*72}")
    print("  -- SHOULD KEEP --")
    for j in POSTS_KEEP:
        if score.relevant_post(j, cfg):
            s, matched, label, reg = score.score_post(j, cfg)
            print(f"  ✅ {s:>3}  {label:<26} {j['title'][:42]}")
        else:
            print(f"  ⚠️  WRONGLY DROPPED            {j['title'][:42]}")
    print("  -- SHOULD DROP --")
    for j in POSTS_DROP:
        if score.relevant_post(j, cfg):
            s, matched, label, reg = score.score_post(j, cfg)
            print(f"  ⚠️  LEAKED [{s:>3}] {label:<20} {j['title'][:42]}")
        else:
            print(f"  ❌ DROP                        {j['title'][:42]}")
    bad_drop = sum(1 for j in POSTS_KEEP if not score.relevant_post(j, cfg))
    bad_keep = sum(1 for j in POSTS_DROP if score.relevant_post(j, cfg))
    print(f"\n  Posts summary: {len(POSTS_KEEP)-bad_drop}/{len(POSTS_KEEP)} kept correctly, "
          f"{len(POSTS_DROP)-bad_keep}/{len(POSTS_DROP)} dropped correctly.")

def show(label, jobs):
    print(f"\n{'='*72}\n  {label}\n{'='*72}")
    for j in jobs:
        if score.relevant(j, cfg):
            s, matched, tr = score.score(j, cfg)
            extra = f"  +{', '.join(matched[:3])}" if matched else ""
            print(f"  ✅ KEEP  [{tr}] {s:>3}  {j['title']}{extra}")
        else:
            print(f"  ❌ DROP        {j['title']}")

def show_tz():
    print(f"\n{'='*72}\n  TIMEZONE RANKING (same Angular role — work-life-balance vs Cairo)\n{'='*72}")
    rows = []
    for j in TZ:
        s, _, _ = score.score(j, cfg)
        _, label = score.timezone_fit(j)
        rows.append((s, label or "—", j["location"], j.get("description", "")[:34]))
    for s, label, loc, d in sorted(rows, reverse=True):
        print(f"  {s:>3}  {label:<16} {loc:<26} {d}")

# ---- AI-training / data-labeling gigs (down-ranked to the bottom, never built-Angular) ----
AI_GIGS = [
    J("Angular Developer", desc="micro1 is the leading AI data lab. Help train next-generation AI systems and guide model learning. RxJS, SCSS."),
    J("Senior Angular Engineer", desc="Mercor: critique code and provide feedback to train frontier models. No prior experience in AI is required."),
    J("Frontend Developer", desc="Join Outlier AI to evaluate AI agents and improve how models learn. RLHF, data annotation."),
]
NOT_AI_GIGS = [
    J("Angular Developer", desc="Build our SaaS analytics dashboard in Angular 17, RxJS, NgRx. Ship to production."),
    J("Frontend Angular Developer", desc="We're an AI startup; build the Angular frontend for our ML product and ship features to users."),
]

# ---- employment type: contract / part_time / full_time (fallback full_time) ----
EMPLOYMENT = [
    (J("Angular Developer", desc="6-month contract, outside IR35, day rate negotiable."), "contract"),
    (J("Angular Developer (Contract)", desc="United Kingdom. 4+ years building production Angular."), "contract"),
    (J("Angular Developer", tags=["Contract"], desc="Build SPAs with Angular."), "contract"),
    (J("Part-Time Angular Developer", desc="20 hours/week, flexible."), "part_time"),
    (J("Angular Developer", desc="Permanent, full-time role with benefits."), "full_time"),
    (J("Angular Developer", desc="Join our team building Angular apps."), "full_time"),  # unclear -> fallback
    (J("Angular Developer", desc="Permanent contract of employment, full benefits."), "full_time"),
]

def show_ai_gig():
    print(f"\n{'='*72}\n  AI-EVAL GIG DETECTION (these get sunk to the bottom)\n{'='*72}")
    ok = 0
    for j in AI_GIGS:
        hit = score.is_ai_eval_gig(j); ok += hit
        s, _, _ = score.score(j, cfg)
        print(f"  {'✅' if hit else '⚠️ '} gig={hit!s:<5} score={s:<3} {j['title']}")
    for j in NOT_AI_GIGS:
        hit = score.is_ai_eval_gig(j); ok += (not hit)
        print(f"  {'✅' if not hit else '⚠️ '} gig={hit!s:<5}         {j['title']} — real build role")
    print(f"  AI-gig summary: {ok}/{len(AI_GIGS)+len(NOT_AI_GIGS)} classified correctly.")

# ---- reachability from Egypt (flag only on real evidence; neutral when silent) ----
REACHABILITY = [
    (J("Senior Front End Angular Engineer", loc="United States",
       desc="Fully remote. BigBear.ai builds AI decision-intelligence for national security. McLean, Virginia. Equal opportunity, protected veterans. Angular v17+, RxJS, signals."), "locked"),
    (J("Angular Developer", loc="United Kingdom",
       desc="Contract. Production Angular SPAs. 4+ years. RxJS, AG Grid, REST."), "soft"),
    (J("Senior Frontend Developer Angular", loc="Remote",
       desc="100% remotely from anywhere in Germany. Angular, TypeScript, NgRx. Berlin office optional."), "locked"),
    (J("Angular Developer", loc="Remote",
       desc="We hire worldwide and work from anywhere. Contractors welcome via Deel. Angular, RxJS."), "global"),
    (J("Angular Developer", loc="Remote",
       desc="Join our team building Angular apps. RxJS, NgRx, SCSS."), ""),  # silent -> neutral
    (J("Angular Developer", loc="Remote - Egypt",
       desc="Cairo-based hybrid. Angular, TypeScript."), ""),               # home market -> neutral
]

def show_reachability():
    print(f"\n{'='*72}\n  REACHABILITY FROM EGYPT (flag only on evidence; silent -> neutral)\n{'='*72}")
    ok = 0
    for j, want in REACHABILITY:
        got = score.reachability(j); ok += (got == want)
        s, _, _ = score.score(j, cfg)
        tag = score.REACH_LABEL.get(got, "—")
        print(f"  {'✅' if got==want else '⚠️ '} {(got or 'neutral'):<8} score={s:<3} {tag:<18} {j['title'][:34]} @ {j['location']}")
    print(f"  Reachability summary: {ok}/{len(REACHABILITY)} classified correctly.")

def show_employment():
    print(f"\n{'='*72}\n  EMPLOYMENT TYPE (contract / part-time / full-time; unclear -> full-time)\n{'='*72}")
    ok = 0
    for j, want in EMPLOYMENT:
        got = score.employment_type(j); ok += (got == want)
        print(f"  {'✅' if got==want else '⚠️ '} {got:<10} (want {want:<10}) {j['title']}")
    print(f"  Employment summary: {ok}/{len(EMPLOYMENT)} classified correctly.")

if __name__ == "__main__":
    show("SHOULD SELECT (25)", SELECT)
    show("SHOULD DROP (25)", DROP)
    show_tz()
    show_posts()
    show_ai_gig()
    show_employment()
    show_reachability()
    bad_keep = sum(1 for j in DROP if score.relevant(j, cfg))
    bad_drop = sum(1 for j in SELECT if not score.relevant(j, cfg))
    print(f"\nSummary: {len(SELECT)-bad_drop}/{len(SELECT)} kept correctly, "
          f"{len(DROP)-bad_keep}/{len(DROP)} dropped correctly.")
