# Radhe Constructions Console

A business intelligence admin console for a premium real estate group in Hyderabad. One public landing page, one admin login, and one console that shows projects, inventory, sales, buyers, collections, construction, employees and risks in a single place.

> Demo prepared for CGI. Radhe Constructions is a demo brand. **All data is fictional.**

**The pitch:** see the chain from the construction site to the bank account, in one screen.

## Status
Phase 1 of 12 is done (plan, folders, docs, config). See `docs/PROGRESS.md`.

## How it fits together
```
Browser (React + Vite)  --/api-->  FastAPI backend  -->  PostgreSQL on Neon
  landing, login, console          services, scoring,     projects, units, bookings,
                                   risk engine            demands, milestones, ...
```

## Where to look
| File | What it is |
|---|---|
| `docs/SPEC.md` | The full specification. The source of truth. |
| `docs/PROGRESS.md` | Where the build is right now. Read this first. |
| `docs/PHASES.md` | The 12 phases as a checklist. |
| `docs/DOMAIN.md` | How the real estate business works. |
| `docs/GLOSSARY.md` | Plain meanings of every special word. |
| `docs/DESIGN.md` | Colours, fonts, and the anti-congestion rules. |
| `docs/DECISIONS.md` | Why each choice was made. |
| `docs/ROADMAP_V2.md` | What comes after this version (AI copilot and more). |
| `config/` | Brand, scoring weights, risk rules. |

## How to run
Setup steps arrive with the code: backend in Phase 2, frontend in Phase 5, Docker in Phase 11.
