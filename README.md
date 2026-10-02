# Radhe Constructions Console

A business intelligence console for a premium real estate group in Hyderabad, with a public landing page and three signed-in areas: an **admin console**, an **employee portal** and a **customer portal**.

> Demo prepared for CGI. Radhe Constructions is a demo brand. **All data is fictional.**

**The idea:** see the chain from the construction site to the bank account, in one screen. A late floor slab delays payment demands, which hurts collections, which worries buyers. This project connects those steps so anyone can follow them.

[![CI](https://github.com/vasaviAnnapureddy/radhe-crm/actions/workflows/ci.yml/badge.svg)](https://github.com/vasaviAnnapureddy/radhe-crm/actions/workflows/ci.yml)

## Three ways to see it (easiest first)

### 1. Live link
**https://radhe-crm.vercel.app/**

Ask the project owner for the demo logins. The backend runs on a free plan that sleeps when idle, so the first sign-in can take up to a minute. If it fails once, wait and try again.

### 2. One command with Docker
```
git clone https://github.com/vasaviAnnapureddy/radhe-crm.git
cd radhe-crm
docker compose up --build
```
Then open **http://localhost:8080**. The first start takes a few minutes: it creates a local database and loads the demo data.

Local demo logins (they work only inside this Docker setup):

| Who | Email | Password |
|---|---|---|
| Admin | `admin@radhe.local` | `radhe-admin-demo` |
| Home owner (Karthik Reddy) | `karthik@radhe.local` | `radhe-portal-demo` |
| Relationship manager (Sneha Rao) | `sneha@radhe.local` | `radhe-portal-demo` |
| Sales manager (Arjun Varma) | `arjun@radhe.local` | `radhe-portal-demo` |

Stop with Ctrl+C. Remove everything, including the local data, with `docker compose down -v`.

### 3. Manual setup
You need Python 3.12, Node.js 20 or newer, and any PostgreSQL database (a free one from neon.tech works).

```
# 1. Settings
copy .env.example .env          (then fill in DATABASE_URL, JWT_SECRET, the admin and portal values)

# 2. Backend, in one terminal
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1    (on macOS or Linux: source .venv/bin/activate)
pip install -r requirements.txt
alembic upgrade head
python -m seed.run --reset
uvicorn app.main:app --reload

# 3. Frontend, in a second terminal
cd frontend
npm install
npm run dev
```
Open http://localhost:5173.

## What is inside

| Area | For whom | What it shows |
|---|---|---|
| Landing page | Everyone | The brand, what it builds, its sustainability principles, three projects |
| Admin console | Leadership | Overview, Projects & Inventory (unit grid), Sales & Leads, Customers, Collections, Construction, Employees & Teams, Risks & Alerts |
| Employee portal | Each employee | Their day, their own work, meetings, scorecard, profile |
| Customer portal | Each buyer | A step-by-step journey from booking to possession, payments, construction progress, requests, profile |

Things to try in the admin console:
- **Hover** any name, unit or tower for a quick view. **Click** to pin it as a drawer. Links inside stack with a breadcrumb.
- Click the small **info icon** on any KPI card to see its formula and the exact rows behind it.
- Press **Ctrl+K** to search.
- Open **Construction** and follow the Tower B delay through to the buyers it affects.

## How it is built

```
Browser (React 19, Vite, Tailwind)  --/api-->  FastAPI (Python 3.12)  -->  PostgreSQL
```
- The browser always calls `/api` on its own address, so the login cookie stays on one site.
- Every number is calculated from database rows, in plain Python functions under `backend/app/services/`.
- Each person sees only their own records: the server decides this, not the browser.
- 96 backend tests and 11 frontend tests. CI also builds the Docker images and starts the whole system.

More detail: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Documents

| File | What it is |
|---|---|
| [docs/SPEC.md](docs/SPEC.md) | The original specification |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | How the pieces fit, with a diagram |
| [docs/DEMO_SCRIPT.md](docs/DEMO_SCRIPT.md) | A seven-minute walk through the demo |
| [docs/DECISIONS.md](docs/DECISIONS.md) | Why each choice was made |
| [docs/DOMAIN.md](docs/DOMAIN.md), [docs/GLOSSARY.md](docs/GLOSSARY.md) | The real estate business in plain words |
| [docs/DESIGN.md](docs/DESIGN.md) | Colours, fonts and layout rules |
| [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) | How the live site is deployed |
| [docs/PROGRESS.md](docs/PROGRESS.md) | Build log, including known limits |
| [docs/ROADMAP_V2.md](docs/ROADMAP_V2.md) | What comes next (an AI copilot and more) |
| [docs/IMAGE_CREDITS.md](docs/IMAGE_CREDITS.md) | Photo credits and licence |

## Known limits
- Both portals are read-only. The only change anyone can make is an admin setting a risk's status.
- The demo data is dated from the day it was loaded, so day counts drift until it is loaded again.
- All portal logins share one demo password. A real system needs one per person and a reset flow.
- No AI features in this version. The plan for them is in `docs/ROADMAP_V2.md`.
