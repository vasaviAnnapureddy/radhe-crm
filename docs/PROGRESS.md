# Progress

**Read this file first in any new session.** Then read `docs/SPEC.md` Section 0 (working rules) and the next phase in Section 15.

## Current status
- **Phase 1:** done.
- **Phase 2:** done and confirmed on Neon (`/api/health` shows ok).
- **Phase 3:** done (developer typed `continue` after the seed step; not separately confirmed in chat).
- **Phase 4:** done and confirmed on Neon (login worked in `/docs`; `/api/risks` shows 33 risks, 11 high).
- **Phase 5:** done (developer has both servers running: backend on 8000, frontend on 5173).
- **Phase 6:** code done and checked in a browser against the developer's running servers (02 Oct 2026). Not checked by Claude: a real sign-in with the `.env` password, and logout. Developer to try those.
- **Phase 7:** pages done and checked in a browser on a test database (02 Oct 2026). **Deploy is NOT done**: files and guide are ready (`render.yaml`, `frontend/vercel.json`, `docs/DEPLOYMENT.md`); it needs a git commit and push plus the developer's Vercel and Render accounts.
- **Phase 8:** done and checked in a browser on a test database (02 Oct 2026): `pages/console/Sales.tsx`, `Customers.tsx`, `Collections.tsx`. Chart clicks filter the table below (lead source, health band, bank). `DataTable` has a `search` prop and honours a starting `sort` in `params`; `SectionTabs` can be controlled; `FilterChip` shows the active chart filter.
- **Fixes on 02 Oct:** clicking a project NAME on Projects & Inventory now also switches the grid (before, only clicking the card body did). Seed: active negotiations are now touched 1 to 8 days ago, so the stalled list stays correct for about 5 days after seeding. **Reseed needed** to pick this up (`python -m seed.run --reset`).
- **Audit fixes on 02 Oct (after developer feedback):**
  - Date range now matters everywhere it sensibly can. Period KPIs change with it. "As of today" KPIs keep their value but show a note that follows the range (for example "37 new buyers in this period"); `/metrics` replies carry `is_flow` and `period_note`. Sales funnel, lead sources, lost and cancelled charts, and the lists All leads, Lost, All bookings and All demands now use the date range. Stalled, Overdue, Awaiting bank and Blocked stay "right now" lists on purpose.
  - Bug fixed: rows in the interactions, tickets, site-visits and commissions tables opened a drawer with the wrong id ("not found"). Rows now carry `target_id`; `tests/test_tables.py` checks every clickable row.
  - Health chart click filters to that exact bar (`health_min`, `health_max`). Stalled list reads its 14 days from `config/scoring.yaml`. Risk links read "14th floor slab" and "Booking A-1203" instead of "Tower B milestone" and "Booking" (needs a reseed to show).
  - KPI cards: no wrapping of long values; large crore values use fewer decimals (`₹2,851 Cr`); the trend line shows only on very wide screens.
  - Backend tests: 85 passed. Frontend tests: 11 passed.
- **Known limits (not fixed):** risk titles and facts are computed at seed time, so day counts in them go stale until the next reseed; "Today's site visits" is empty on any day after the seed day. Reseed on demo morning.
- **Date filter, second change (02 Oct, developer request):** the default range is now **All time** (last 730 days). The Customers page counts buyers who BOOKED in the chosen period: `buyers_of()` in `services/metrics.py`; all five Customers KPIs are period numbers (30 days 40 buyers, 90 days 144, 12 months 502, all time 798). Karthik Reddy booked 480 days ago, so he is on the Customers list only for "All time".
- **Phase 9:** done and checked in a browser on a test database (02 Oct 2026): `pages/console/Construction.tsx` (delay impact card, then the planned-vs-actual timeline, 6 tabs) and `Employees.tsx` (2 charts, People / Needs attention / Overdue tasks). Collections accepts `?tab=blocked`. Story 1 can be followed: Construction, delay card, buyers, "See the 41 blocked demands in Collections". Story 3: Employees, Needs attention, Arjun Varma (score 38).
- **Employees and Construction rework (02 Oct, developer request):**
  - Employees page is now a team directory: 5 KPIs (adds `new_joiners`), a **Teams** list (9 departments with headcount, head, average score, "need support", joined in period) and the **people of the selected team** as tiles (name with hover and drawer, role, score, headline, tags Team head / New joiner / On leave). Tabs: Top performers (3 leaderboards; sales and RM boards count the chosen period), New joiners, Needs support, Workload and scores, All 110 people, Overdue tasks. Backend: `teams()` and `leaderboards()` in `services/pages.py`.
  - Employee drawer has a new **Connections** tab: reports to, their team, colleagues in the same role, and for sales and RMs the colleagues they share buyers with. Quick view shows "Reports to" and "Team size".
  - Construction follows the date range: Average slip is a period number; Towers on schedule and Open quality issues carry a period note; Quality log and Safety log list the chosen period.
  - Seed: about one in seven non-head employees joined in the last 180 days (before, nobody had joined in the last 200 days, so "new joiners" was always empty). Silent-buyer story now only picks buyers who booked 40+ days ago (a reseed had made one of them too recent). **Reseed needed.**
  - Backend tests: 85 passed.
- **Phase 10:** done and checked in a browser on a test database (02 Oct 2026). `pages/console/Risks.tsx`: header count, category chips with counts, status filter, full risk cards (Observed, Suggested action, linked entities, owner), status buttons that PATCH and refresh the bell, the Overview list and the KPI. New `tests/test_links.py` proves every `{type,id,label}` in Overview, Construction, Employees, Projects, all risks, search results and a sample of drawers opens a real entity. Backend tests: 89 passed. All 8 sidebar pages are now built.
- **Git:** first commit pushed to `origin/main` on 02 Oct (phases 1 to 10). Portal work is committed locally after that; push when the developer says so.
- **Phase 10B: portals (02 Oct, developer request).** Built and checked in a browser on a test database. Backend tests: 96 passed.
  - **Logins:** every employee (110) and every buyer with an active booking (798) has a login, all sharing `PORTAL_PASSWORD` from `.env`. `users` has `employee_id` and `customer_id` (migration `0002`). Sample logins: `karthik.reddy@example.com`, `sneha.rao@radheconstructions.demo`, `arjun.varma@radheconstructions.demo`.
  - **One login page.** `/auth/login` and `/auth/me` return `role` and `home` (`/console/overview`, `/employee/day`, `/my/journey`). `AuthGuard` takes a role; a wrong role is sent to that person's home.
  - **Security:** the console router is admin-only (`require_admin`). Portal routes take no person id; the server uses the signed-in user. `services/portal.py` has `scope()` (the exact records a person may open) and `scrub()` (turns every link outside that list into plain text). Buyers may open only their own unit and demands; they never receive the admin's customer view. `tests/test_portal.py` tries to break this.
  - **Employee portal** `/employee/{day|work|meetings|scorecard|profile}`: role-aware numbers, a notice when something needs them, overdue and upcoming tasks, their own leads, buyers, milestones or tasks, scheduled site visits and buyer calls, scorecard with position in their role.
  - **Customer portal** `/my/{journey|payments|construction|requests|profile}`: a step-by-step journey (booking, agreement, home loan, construction and payments, registration, possession, interiors, after-sales) with "You are here" and "What happens next"; payment schedule and receipts; construction stages with an honest delay notice; their messages and service requests; their RM's contact.
  - **Frontend:** `app/PortalLayout.tsx` (`PortalLayout`, `PortalPage`, the two menus), `lib/entityBase.ts` (portal hover cards and drawers call `/api/portal/entity/{type}/{id}`), new block kinds `notice` and `journey` in `components/views/Blocks.tsx`. The server sends each page as `{title, subtitle, kpis, blocks}`.
  - **Seed:** tasks are now tied to real leads, buyers and milestones (follow-ups, replies to waiting buyers, scheduled calls, progress updates). Story characters have plain emails.
  - **Admin bell** now opens a list of the high-priority alerts instead of only linking to the Risks page.
  - **Portal fixes after developer review (02 Oct):** buyer journey and profile show a "My home" section (project, tower, floor, unit, type, areas, facing, agreement value, plan, booking date); the journey page explains the payment plan in words and lists all payments in order with Paid / Due / Overdue / Held / Not due yet; the Construction page says how many floors the tower has and which stages are tracked. RM "My work" has a table of overdue payments with the unpaid amount; the demands table shows "Unpaid" by default everywhere; late tasks say "Past due date" so "Overdue" always means money. Sample login emails live in `.env` (`PORTAL_CUSTOMER_EMAIL`, `PORTAL_RM_EMAIL`, `PORTAL_SALES_EMAIL`), are read by the seed, and are no longer in the frontend code.
  - **Limits:** read-only; departments without work data (legal, marketing, procurement, design, finance) see tasks and profile only; relationship managers' "meetings" are scheduled calls stored as tasks; villa and plot buyers get a shorter journey with no stage tracker.
- **DEPLOYED on 02 Oct 2026.** Live site (the one link to share): https://radhe-crm.vercel.app/ . Backend: https://radhe-console-api.onrender.com (check with `/api/health`). The developer confirmed sign-in, staying signed in after refresh, and the employee portal on the live site. Portals confirmed working on Neon data.
- **Data freshness:** all dates are relative to the day of seeding. Day counts and "today" lists drift a little each day. Reseed from the laptop on demo morning (`python -m seed.run --reset`); the live backend picks it up within 10 minutes, or at once after a restart on Render.
- **Next phase:** Phase 11 handover packaging (Docker, CI, README, demo script, architecture doc, final polish). Deploy and secret check are done.
- **Parked:** employee and customer portals (`docs/SPEC_PORTALS.md`, draft only; decide after the admin console is finished)
- **Deadline:** Sunday 04 Oct 2026, 6:00 pm
- **Project folder:** `E:\radhe-console`
- **GitHub:** https://github.com/vasaviAnnapureddy/radhe-crm (remote `origin` is set, nothing committed or pushed yet)

## Phase 1: done
Folder tree, docs, `README.md`, `.env.example`, `.gitignore`, `config/*.yaml`.

## Phase 2: done
`.env`, git init, `backend/.venv`, settings, logging, session, 31 models, `/api/health`, Alembic migration `0001`, `docs/NEON_SETUP.md`.
- Column types are generic (`Uuid`, `JSON`, `Numeric`), so tests run on SQLite and the app runs on Postgres.
- Five columns beyond Section 11: `customers.city`, `demands.reminders_sent`, `construction_milestones.owner_employee_id`, `quality_issues.contractor_id`, `quality_issues.owner_employee_id`.
- `alembic.ini` needs `prepend_sys_path = .` (fixed after the first run failed with "No module named app").

## Phase 3: code done
Built in `backend/seed/`: `stories.py` (story names and numbers), `world.py`, `names.py`, `org.py`, `inventory.py`, `sales.py`, `money.py`, `care.py`, `build.py`, `run.py`. Also `app/core/security.py` (argon2) and `tests/test_seed_stories.py`.

Result: 42,194 rows. 5 projects, 8 towers, 1,600 units, 4,000 leads, 850 bookings (36 cancelled), 834 customers, 110 employees, 30 channel partners, 12 contractors, 8 banks. Same ids and numbers on every run (fixed random seed).

### How the data works (Phase 4 services must follow these definitions)
- **Dates are relative to the day you seed.** "12 days without a reply" is 12 days on the seed day and 13 the next day. Reseed on demo morning.
- **Blocked by construction delay** = demands with status `not_raised` whose construction milestone has no `actual_date` and a `planned_date` in the past. Only Skyline Tower B `slab_14` qualifies: 41 bookings, Rs 6.8 Cr.
- **Overdue** = demand amount minus its receipts, where `due_on` is in the past. Part payments exist, so always subtract receipts. Do not trust `demands.status` alone.
- **Active buyer** = customer with at least one non-cancelled booking. RM workload counts active buyers. Sneha Rao has 62; the average over 21 RMs is 38.
- **Conversion** = bookings / site visits with status `done`, per sales person. Team is about 11%, Arjun Varma 4%.
- **Idle negotiation** = lead in stage `negotiation` whose latest `lead_activities.occurred_at` is 14+ days old. Value = `budget_max`. The Rs 2 Cr risk threshold applies to the owner's total (Arjun: 9 deals, Rs 14 Cr).
- **Possession soon** = buyer in a tower whose `handover` milestone is open and planned within 180 days (Greens Tower B). Upsell value = buyers without an interior project x average interior project value.
- **Buyer health** (so Karthik lands near 41): payment 40 x (share of receipts on or before due date) x (1 - worst overdue days / 90); engagement 25 x linear from full at 7 days to zero at 45 days since our last outbound contact; complaints 20 x max(0, 1 - 0.5 x open tickets - 0.25 x unanswered queries); loan 15 (none, sanctioned, disbursing, closed = 15; awaiting disbursement = 5).
- **Risks table is empty after seeding.** The Phase 4 risk engine fills it.
- Banks, contractors and channel partner firms are invented names.

### Test steps for Phase 3 (developer)
1. Terminal: `cd E:\radhe-console\backend`, then `.\.venv\Scripts\Activate.ps1`.
2. `pytest -q` should say `12 passed`.
3. `python -m seed.run --reset` prints a table of row counts ending in `TOTAL 42,195` (42,194 plus the admin user).
4. In Neon, open **Tables** and look at `customers`: search for Karthik Reddy.

## Phase 4: code done
Built in `backend/app/`:
- `services/snapshot.py`: all rows loaded into memory once (reloads every 10 minutes and at startup). Every service reads from it.
- `services/common.py`, `tables.py` (one column and row definition per table type), `metrics.py` (27 KPIs with Explain), `pages.py` (charts, unit grid, lists, search), `entities.py` (quick view and drawer for 11 entity types).
- `scoring/scores.py` (buyer health, lead score, project health, employee scorecard) and `risks/engine.py` (10 rules from `config/risk_rules.yaml`).
- `api/deps.py`, `auth.py`, `console.py`, `public.py`; `schemas/auth.py`.
- Tests: `test_scoring.py`, `test_risks.py`, `test_api.py`.
- The seed now also stores risks: 33 risks, 11 high. Row total is now 42,246.

### API contract the frontend (Phase 5 onward) builds on
- **Auth:** `POST /api/auth/login {email, password, remember}` sets httpOnly cookie `radhe_session`. `GET /api/auth/me`, `POST /api/auth/logout`. 401 means go to `/login`. 429 after 5 wrong tries in a minute.
- **Global filters** on every console route: `date_from`, `date_to`, `project_id`. Default range is the last 90 days.
- **KPI:** `GET /api/metrics?keys=a,b,c` or `/api/metrics/{key}` returns `{key, label, kind, value, previous_value, formula_text, filters, drilldown_url, row_count, sparkline}`. `/api/metrics/{key}/rows` returns a list.
- **List:** `{columns:[{key,label,kind,default}], items, total, page, page_size}`. Query: `page`, `page_size`, `sort`, `order`, `q`. Each item has `id` and (usually) `type`, which is the entity to open on hover or click.
- **Cell kinds:** `text, number, money, percent, date, datetime, days, ref, status, score`. A `ref` is `{type, id, label}`; a `status` is `{label, tone}`; a `score` is `{value, tone}`. Tones: `good, watch, risk, neutral`.
- **Entity:** `GET /api/{customers|units|towers|projects|employees|leads|bookings|channel-partners|demands|milestones|contractors}/{id}` with `?view=quick` for hover. Shape: `{type, id, title, subtitle, status, facts[], attention, last_activity, tabs[]}`. A tab has `blocks`; block kinds: `facts, table, timeline, score, scorecard, chart`.
- **Chart:** `{title, type: bar|line|stacked|funnel, kind, x[], series:[{name, data[]}]}`.
- **Pages:** `/api/overview`, `/projects`, `/projects/{id}/inventory?tower_id=`, `/sales/funnel`, `/sales/lost/summary`, `/customers/summary`, `/collections/summary`, `/construction/summary`, `/construction/delay-impact`, `/employees/summary`, `/risks`, `PATCH /risks/{id} {status}`, `/search?q=`.
- **Lists:** `/customers`, `/leads`, `/bookings`, `/demands?tab=all|overdue|awaiting_bank|blocked`, `/units?ageing=1`, `/employees`, `/channel-partners`, `/sales/stalled`, `/sales/lost`, `/towers`, `/construction/milestones|contractors|budgets|quality|safety`.
- **KPI keys by page:** Overview `bookings_value, collections_received, collections_overdue, unsold_inventory_value, open_high_risks`. Sales `new_leads, site_visits, visit_to_booking_conversion, bookings_value, cancellations`. Customers `total_buyers, nri_share, average_health, at_risk_buyers, open_queries`. Collections `demands_raised, collected, collection_efficiency, collections_overdue, blocked_by_delay`. Construction `towers_on_schedule, average_slip_days, milestones_due_this_month, cost_variance_pct, open_quality_issues`. Employees `headcount, avg_target_achievement, people_needing_attention, overdue_tasks`.

### Test steps for Phase 4 (developer)
1. `cd E:\radhe-console\backend`, `.\.venv\Scripts\Activate.ps1`.
2. `pytest -q` says `81 passed`.
3. `python -m seed.run --reset` ends with `TOTAL 42,246` (needed again, because risks are now stored).
4. `uvicorn app.main:app --reload`, then open `http://localhost:8000/docs`.
5. In `/docs`: open `POST /api/auth/login`, click **Try it out**, enter the email and password from `.env`, **Execute**. Expect code 200.
6. Still in `/docs`: try `GET /api/overview` and `GET /api/risks`. Expect 200 with data.

## Phase 5: code done
Built in `frontend/`:
- Setup: `package.json`, `vite.config.ts` (proxy `/api` to the backend, reads the root `.env`), `tsconfig.json`, `index.html`, `src/main.tsx`.
- `src/styles/theme.css`: Section 6 tokens for Tailwind v4 (`bg-bg`, `text-ink`, `border-line`, `bg-primary`, `bg-accent`, `text-good|watch|risk`, `font-display`, `rounded-card`, `rounded-sharp`).
- `src/lib/`: `format.ts` (+ `format.test.ts`), `api.ts`, `types.ts`, `urlState.ts` (`useFilters`, `useDrawer`, `useExplain`), `cn.ts`.
- `src/app/`: `App.tsx` (router), `auth.tsx` (`useMe`, `AuthGuard`, login and logout), `ConsoleLayout.tsx` (sidebar, top bar, filters, alerts bell), `SearchPalette.tsx` (Ctrl+K), `nav.ts`.
- `src/components/ui/`: `button`, `sheet`, `tabs`. `src/components/data/`: `KpiCard` + `KpiRow`, `ChartCard`, `DataTable`, `Cell`, `Value` (`Money`, `Area`, `DateText`, `StatusPill`, `ScorePill`, `RiskBadge`), `PageHeader` (`PageHeader`, `Card`, `SectionTabs`), `States` (`Skeleton`, `EmptyState`, `ErrorState`). `src/components/views/`: `EntityLink`, `QuickView`, `EntityDrawer`, `Blocks`, `ExplainDrawer`.
- Pages: working plain `Login`, holding `Landing`, `Placeholder` for the 8 console pages, `/console/styleguide`.

How a page is built from here (Phases 7 to 10): `<PageHeader>`, `<KpiRow keys={[...]}/>`, one or two `<ChartCard chart={...}/>`, then `<SectionTabs>` with `<DataTable endpoint="/customers" params={params}/>`. Any `{type,id,label}` goes in `<EntityLink entity={...}/>`. Replace the matching `Placeholder` route in `src/app/App.tsx`.

Notes:
- Library versions were whatever npm gave on 01 Oct 2026 (React 19.3, Vite 8, Tailwind 4.3, TypeScript 7, Recharts 3). `react-router` is pinned to 7 and `@tanstack/react-table` to 8, because their newest majors were unfamiliar. `motion` is installed for Phase 6.
- Components are hand-written on Radix (the base shadcn uses) instead of generated by the shadcn CLI.
- The preview browser on Claude's side used a throwaway database and a generated test login, on ports 8030 and 5180.

### Test steps for Phase 5 (developer). Two terminals are needed.
1. Terminal 1 (backend): `cd E:\radhe-console\backend`, `.\.venv\Scripts\Activate.ps1`, `uvicorn app.main:app --reload`. Leave it running.
2. Terminal 2 (frontend; the + button in the VS Code terminal panel opens it): `cd E:\radhe-console\frontend`, then `npm run dev`. Leave it running.
3. Browser: `http://localhost:5173/console/styleguide`. It sends you to the login page. Sign in with the `.env` admin email and password.
4. Open `http://localhost:5173/console/styleguide` again and check it against `docs/DESIGN.md` 6.3 and 6.4.
5. Try: hover "Karthik Reddy", click him, click "Sneha Rao" inside the drawer, press the browser Back button, click the small info icon on a KPI card, press Ctrl+K and type `skyway`.
6. Optional: in a third terminal, `cd E:\radhe-console\frontend` and `npm run test` (11 passed), `npm run build`.

## Phase 6: code done
- `frontend/src/pages/public/Landing.tsx` with `components/landing/Hero.tsx`, `Sections.tsx` (About, WhatWeBuild, Sustainability, FeaturedProjects, ClosingBand, Footer) and `Reveal.tsx` (gentle scroll reveal, off for reduced motion). `lib/brand.ts` mirrors `config/brand.yaml`.
- `pages/public/Login.tsx`: split screen (photo left, form right; photo hidden below 1024px).
- 8 WebP photos in `frontend/public/images/`, all about 300 KB or less; credits and licence notes in `docs/IMAGE_CREDITS.md`.
- Featured projects come from `GET /api/public/featured-projects`; a built-in fallback list is used only if the backend cannot be reached.
- The four "About" numbers are demo figures (marked in a code comment).

### Test steps for Phase 6 (developer), with both servers running
1. `http://localhost:5173/`: scroll the whole page slowly. Hover the five lines under "What we build"; the photo should change.
2. Narrow the browser window to about tablet width and scroll again.
3. Click **Admin login**. Try a wrong password (clear error), then the right one (lands on Overview).
4. Click **Log out** at the bottom of the sidebar (returns to the landing page). Then open `http://localhost:5173/console/overview` directly: it should send you to the login page.

## Phase 7: pages done, deploy pending
- `pages/console/Overview.tsx`: greeting, 5 KPIs, monthly chart, "What needs attention" (top 5 risks), project health strip, tabs (funnel, today's visits, handovers, top RMs, top partners).
- `pages/console/Projects.tsx` + `components/inventory/UnitGrid.tsx`: 5 project cards, unit grid with tower switch and four colourings (status, price, days unsold, buyer payment health), tabs (ageing, price trend, towers).
- `components/data/RiskCard.tsx` (compact form on Overview; full form is for the Risks page in Phase 10). A risk title links to the page for its category.
- `EntityLink` has a `plain` option (used by grid cells). New pages are registered in the `BUILT` map in `src/app/App.tsx`.
- Checked: Tower B shows 30 floors of 6 units; under "Buyer payment health" Karthik's unit B-3004 is red; clicking it opens the unit drawer with buyer Karthik Reddy, 45% paid.

### Test steps for Phase 7 (developer), with both servers running
1. Sign in. Overview: check the five KPIs, the chart, and the attention list (Tower B should be second).
2. Click "Tower B delay blocks ..." (it goes to Construction, still a placeholder until Phase 9). Go back.
3. Projects & Inventory: click the Radhe Skyline card, then **Tower B**. Hover a few units. Try the four colour buttons.
4. Click unit **B-3004**, then the buyer **Karthik Reddy** inside the drawer, then press Back.
5. Click the Radhe Greens card, **Tower B**, colour by **Days unsold**: west-facing units on floors 2 to 4 should stand out in red.

## What the developer must have ready
- Node.js 20 or newer (`node --version`), needed from Phase 5.

## Open questions
- None.
