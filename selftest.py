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

def show(label, jobs):
    print(f"\n{'='*72}\n  {label}\n{'='*72}")
    for j in jobs:
        if score.relevant(j, cfg):
            s, matched, tr = score.score(j, cfg)
            extra = f"  +{', '.join(matched[:3])}" if matched else ""
            print(f"  ✅ KEEP  [{tr}] {s:>3}  {j['title']}{extra}")
        else:
            print(f"  ❌ DROP        {j['title']}")

if __name__ == "__main__":
    show("SHOULD SELECT (25)", SELECT)
    show("SHOULD DROP (25)", DROP)
    bad_keep = sum(1 for j in DROP if score.relevant(j, cfg))
    bad_drop = sum(1 for j in SELECT if not score.relevant(j, cfg))
    print(f"\nSummary: {len(SELECT)-bad_drop}/{len(SELECT)} kept correctly, "
          f"{len(DROP)-bad_keep}/{len(DROP)} dropped correctly.")
