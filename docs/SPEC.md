# MEGA PROMPT: Build "Radhe Constructions Console", a business intelligence admin console for a premium real estate group

> How to use this file: paste this whole file into your AI coding tool (Claude Code, Cursor, etc.) as the first message in an empty project folder in VS Code. The tool will first save this spec inside the repo (Phase 1), so every later phase can be resumed even in a new session.
>
> **Radhe Constructions** is a premium real estate group in Hyderabad (demo brand). It builds luxury apartments, villas and plotted developments, runs its own construction, offers interior design to buyers, and holds a land bank. CGI has asked for a demo. All data is fictional. The brand name, colours and logo live in `config/brand.yaml`.

---

## 0. WHO YOU ARE AND HOW YOU MUST WORK

You are a senior full-stack engineer and product designer who has built admin consoles for real estate developers. I am the developer (a fresher AI/ML engineer). I want to understand every decision, not just receive code.

Working rules for the whole project:

1. **Explain every file before you create it.** 2 to 4 plain sentences: what it is, why it exists, how it connects to other files. Then create it.
2. **Work phase by phase** (Section 15). At the end of each phase: list what was built, give exact test steps, update `docs/PROGRESS.md`, then STOP and wait for me to type `continue`. If I type `continue without stopping`, run the remaining phases back to back, still explaining each file.
3. **Never skip ahead.** Do not build features from a later phase early.
4. **Simple language.** Short, plain English. Any domain or tech word gets a one-line explanation the first time and goes into `docs/GLOSSARY.md`.
5. **Respect the deadline: 4 days.** Every feature is tagged `[MUST]`, `[SHOULD]` or `[V2]`. Finish all `[MUST]` items first. Touch `[SHOULD]` only if every `[MUST]` is done. Never build `[V2]` items; they go to `docs/ROADMAP_V2.md`.
6. **Read-only console.** The admin views and explores data. No create, edit or delete forms in this version. The only writes allowed: login, logout, and changing a risk's status. This keeps the scope realistic.
7. **Every number is traceable.** No hard-coded dashboard numbers. Every KPI, chart point and alert is calculated from database rows, and the admin can see which rows (Section 7.3).
8. **Nothing hard-coded that will change.** Brand, scoring weights, risk thresholds and demo credentials live in config files or `.env`.
9. **Honesty over guessing.** If a library API or setup step might have changed, say so, check the docs, and leave a `TODO: verify` comment.
10. **Security by default.** Secrets only in `.env`. Never log passwords, tokens or customer phone numbers.
11. **Small, working steps.** Before changing code: read the existing files, change the smallest thing, run it, fix errors, explain what changed. Never rewrite working code. Never create duplicate files.
12. **No AI features in this version.** The AI copilot is `[V2]`. But design the backend so V2 can plug in later (Section 13).

---

## 1. THE PRODUCT IN ONE PARAGRAPH

Radhe Constructions Console is a public landing page plus **one admin console**. The landing page introduces Radhe Constructions with a calm, sustainable, premium look and invites the admin to log in. Inside, the leadership sees the whole business in one place: projects and unit inventory, leads and bookings, buyers, payment collections, construction progress, employees, and risks. There are no separate portals and no employee or customer logins. Every page follows the same pattern: a few KPI cards, two or three clear visuals, one rich table, and **hover to peek, click to pin**, so the admin understands any person, unit, deal or tower without leaving the page. The pitch: **"See the chain from the construction site to the bank account, in one screen."**

### Why this matters (keep these reasons in mind while building)

- In real estate, data lives in silos: leads in a CRM, construction progress in site reports and Excel, collections in accounts software. Leadership sees each piece, never the chain.
- Under-construction homes are mostly sold on a **construction-linked payment plan**: the buyer pays when a construction stage (like a floor slab) is finished. A construction delay directly delays payment demands, which hurts cash flow, which upsets buyers asking about possession. This chain is the heart of the demo.
- Luxury buyers (often NRIs) expect fast, informed replies. The relationship manager needs the full picture of a buyer in seconds.
- Unsold units that sit for months lock up money. Leadership must see which units are not moving.

---

## 2. UNDERSTANDING THE CLIENT'S BUSINESS

Save this section as `docs/DOMAIN.md`.

### 2.1 Business lines
1. **Luxury apartments**: gated high-rise communities, 3 BHK and 4 BHK homes, clubhouse.
2. **Villas**: independent luxury villas in gated communities.
3. **Plotted developments**: open plots sold per square yard.
4. **Construction**: Radhe builds its own projects (towers, floors, slabs, finishing).
5. **Interiors**: design and execution packages for buyers.
6. **Land bank**: land parcels at different stages of purchase or joint development.
7. **After-sales**: handover, snag fixing, complaints.

### 2.2 Customers
| Type | What they care about |
|---|---|
| End-user home buyers (IT professionals, business families) | Possession date, quality, loan help |
| NRI buyers (US, UK, Gulf, Singapore) | Trust, remote updates, documents, time-zone friendly contact |
| HNI villa buyers | Privacy, customisation, personal attention |
| Investors | Price appreciation, resale or rental |
| Corporate buyers | Bulk units for executives |
| Existing owners | Referrals, interiors |

### 2.3 Lead sources
Website, property portals, digital ads, walk-ins, property expos, channel partners (brokers), referrals, corporate tie-ups, NRI roadshows.

### 2.4 Teams and roles
| Team | Roles | What the admin wants to know |
|---|---|---|
| Pre-sales | Tele-callers, lead qualifiers | Response time, site visits booked |
| Sales | Sales managers, relationship managers (RMs), NRI desk | Site visits, conversion, bookings vs target, stalled deals |
| CRM (post-booking) | Customer relationship executives | Collections, open buyer queries, response time |
| Projects and construction | Project managers, site engineers, QA/QC, safety officers | Milestones on time, delays, quality issues |
| Procurement | Purchase officers | Material delays, vendor performance |
| Design | Architects, interior designers | Interior projects on time |
| Finance and collections | Accountants, collection officers | Overdue amounts, loan disbursements |
| Legal | Legal officers | Agreements and registrations pending |
| Marketing | Campaign managers | Lead quality by source |

### 2.5 External partners (tracked, not employees)
Channel partners, contractors, banks for home loans.

### 2.6 Lifecycle
```
Land -> Approvals -> Launch -> Leads -> Site visit -> Booking
                                                        |
Referrals <- After-sales <- Handover <- Collections <- Construction
```

### 2.7 Sales stages
`New lead -> Contacted -> Site visit scheduled -> Site visit done -> Negotiation -> Unit blocked (token) -> Booked -> Agreement signed -> Registered -> Possession`, plus `Lost` (with reason) and `Cancelled` (after booking, with reason).

### 2.8 Glossary (save as `docs/GLOSSARY.md`)
BHK, carpet area, super built-up area (SBA), price per sq ft, PLC (preferred location charge), floor rise charge, facing, EOI, booking amount, agreement for sale, construction-linked plan (CLP), demand letter, registration, possession, OC (occupancy certificate), snag, JDA (joint development agreement), RERA (real estate regulator; each project has a registration number), channel partner, site visit.

---

## 3. GOLDEN RULES (apply to every screen)

1. **Breathing room first.** The client must feel relaxed, never crowded. Follow Section 6.4 strictly.
2. **One admin, one console.** No portals, no other logins.
3. **Hover to peek, click to pin, link to follow.** Hovering a name, unit, deal or tower shows a quick view card. Clicking pins it as a right-side drawer. Links inside the drawer open the related entity as a stacked drawer with a breadcrumb (Customer > Unit > Tower). The admin never loses the page they started from.
4. **Every number is traceable.** Each KPI has an "Explain" icon showing the formula, filters and the rows behind it.
5. **Facts, signals and suggestions are separate.** Label them "Observed", "Possible reasons" and "Suggested action". Never show a guess as a fact.
6. **Indian formats everywhere.** ₹ with lakh and crore (₹4.25 Cr, ₹38.6 L), `en-IN` grouping, IST, dates like 01 Oct 2026.
7. **Colour carries meaning only.** Status and risk get colour. Nothing else is coloured for decoration.
8. **Privacy by default.** Phone numbers and emails are masked in tables (98xxxxxx21), shown fully only inside a pinned drawer.

---

## 4. TECH STACK (and why)

| Layer | Choice | Why |
|---|---|---|
| Frontend | React 19 + Vite + TypeScript | Admin console behind a login, no SEO needed, so React with Vite is simpler than Next.js. New shadcn projects use React 19 |
| Styling | Tailwind CSS v4 (Vite plugin, theme tokens in CSS, no `tailwind.config` file) | Current version used by shadcn |
| UI components | shadcn/ui (Radix): HoverCard, Sheet, Command, Tabs, Tooltip, Dialog | Accessible, fully customisable, so it will not look like a template once themed |
| Icons | lucide-react, one stroke width everywhere | Consistent, quiet icons |
| Motion | Motion (formerly Framer Motion), used lightly | Smooth drawer and landing page reveals |
| Tables | TanStack Table | Sorting, filtering, column pinning |
| Server data | TanStack Query | Caching, loading and error states |
| Charts | Recharts | Good tooltips, easy to theme |
| Backend | FastAPI (Python 3.12) | Fast to build, automatic API docs, Python ready for V2 AI |
| Database | PostgreSQL on **Neon** (same database for local and deployed) | No Docker setup needed, which saves hours; free plan is enough for this data size |
| ORM and migrations | SQLAlchemy 2.0 + Alembic | Standard and safe |
| Validation | Pydantic v2 | Typed request and response models |
| Auth | Email + password (argon2 hash) + JWT in httpOnly cookie | Simple and secure for one admin |
| Seed data | Python + Faker (`en_IN`) + hand-written Hyderabad lists | Realistic Indian names and localities |
| Tests | pytest (backend), Vitest (formatters and helpers) | Core calculations must be tested |
| Deployment | Frontend on Vercel, backend on Render, database on Neon | Public demo link |
| Handover packaging | Dockerfiles + `docker-compose.yml` (local Postgres 16 + backend + frontend, auto migrate and seed), added in Phase 11 | Reviewers can run everything with one command, without my Neon account |
| CI | GitHub Actions: run tests and build the Docker images on every push | Proves the project builds on a clean machine, even if Docker will not run on my laptop |

**Rule: develop without Docker (fast), ship with Docker (reproducible).** Docker is not used during Phases 1 to 10.

### 4.1 Connection rule (important)
The frontend always calls `/api/...` on its own domain. Locally, Vite's dev proxy forwards `/api` to `http://localhost:8000`. In production, a Vercel rewrite forwards `/api` to the Render backend. This keeps the login cookie same-site and avoids cross-site cookie and CORS problems.

### 4.2 Hosting facts to plan around
- Render's free web services sleep after about 15 minutes without traffic, and the first request after that is slow. For demo week, either upgrade the backend to the cheapest paid instance or open the site a few minutes before the demo. Write this into `docs/DEPLOYMENT.md`.
- Neon's free plan pauses compute after 5 minutes idle and wakes on the next query. Our data is small and fits the free storage limit.

---

## 5. INFORMATION ARCHITECTURE

### 5.1 Public pages
- `/` Landing page `[MUST]` (Section 8)
- `/login` Admin login `[MUST]` (Section 8.3)

### 5.2 Console sidebar (after login)
```
RADHE CONSTRUCTIONS

Overview                     [MUST]
Projects & Inventory         [MUST]
Sales & Leads                [MUST]
Customers                    [MUST]
Collections                  [MUST]
Construction                 [MUST]
Employees & Teams            [MUST]
Risks & Alerts               [MUST]
-------------------------
Interiors                    [SHOULD]
Service & Handover           [SHOULD]
Reports                      [SHOULD]
-------------------------
Admin profile, Log out
```
Land Bank, Administration and AI Copilot are `[V2]`.

### 5.3 Top bar (every console page)
- **Global search (Ctrl+K)** `[MUST]`: finds customers, units, projects, employees, leads, channel partners. Selecting a result opens its drawer.
- **Global filters** `[MUST]`: date range, project. They persist across pages through the URL.
- **Alerts bell** with the count of high risks.

---

## 6. DESIGN DIRECTION (this decides whether it looks premium or "AI-made")

Save as `docs/DESIGN.md`. Every phase must follow it.

### 6.1 Mood
Quiet luxury, natural materials, architecture with greenery. Think a well-designed architecture studio website, not a SaaS template. Calm, confident, a lot of white space.

### 6.2 Tokens (put in `config/brand.yaml` and the CSS theme)
- Background: warm off-white `#F7F5F0`; surfaces `#FFFFFF`; subtle surface `#EFECE5`
- Ink (text): `#1C1F1D`; secondary text `#5E635F`; borders `#E3DFD6`
- Primary: deep forest `#2F4A3A`; sidebar `#1F2E27` with off-white text
- Accent: clay `#B5643C`, used rarely (one call to action per screen, active states)
- Status (muted, not neon): good `#3E7C59`, watch `#C08A2E`, risk `#B4483C`, neutral `#7A7F7B`
- Charts: forest, sage `#8FA88F`, sand `#C9B38C`, clay; never more than 4 colours in one chart
- Fonts: **Fraunces** for landing headings and big console page titles; **Manrope** for everything else; tabular numbers for all figures
- Radius: 10px for console cards, 2px on landing page images and buttons (sharper, architectural feel)
- Borders over shadows: 1px borders, shadows only on hover cards and drawers
- Spacing on an 8px grid; 24 to 32px between sections

### 6.3 Avoid these "AI-made" signs
Purple or blue gradients, glassmorphism, emoji as icons, every element centred, identical three-card feature grids with icons in circles, count-up number animations, generic copy like "Welcome to the future of...", lorem ipsum, stock "business people shaking hands" photos, ten different colours on one page, random badges everywhere.

### 6.4 Anti-congestion rules `[MUST]`
- Max **4 KPI cards** in a row. Max 5 KPI cards on any page.
- Above the fold: KPI row plus at most **two** main visuals. Everything else goes below or into **tabs** inside the page.
- Tables show 6 to 7 columns by default. Extra columns are available from a column chooser.
- Hover cards show 8 to 12 facts maximum.
- Drawers use tabs; each tab fits on one screen where possible.
- Content max width 1440px, centred, with generous side padding.
- Every chart has a short title that says what it shows ("Collections vs demands, last 12 months"), not just "Chart".
- Empty, loading (skeleton) and error states exist for every data block.

### 6.5 Interaction feel
- Hover cards open after about 300 ms and close on mouse leave; keyboard focus also opens them; on touch, tap opens the drawer.
- Transitions 150 to 250 ms. Respect `prefers-reduced-motion`.
- Rows highlight softly on hover. The cursor shows what is clickable.
- Drawer state lives in the URL (`?view=customer:123`), so the browser Back button closes drawers naturally.

---

## 7. THE INTERACTION PATTERN (build once, reuse everywhere)

### 7.1 Reusable components `[MUST]`
- `KpiCard`: value, change vs previous period, tiny sparkline, Explain icon.
- `ChartCard`: title, chart, exact-value tooltips, click a bar or point to filter the table.
- `DataTable`: search, filters, sort, column chooser, row hover quick view, row click opens drawer, CSV export.
- `QuickView`: hover card per entity type.
- `EntityDrawer`: right drawer with tabs, stack and breadcrumb.
- `ExplainDrawer`: formula, filters, rows behind a number.
- `PageHeader`, `SectionTabs`, `StatusPill`, `RiskBadge`, `Money`, `Area`, `DateText`.
- `EmptyState`, `ErrorState`, `Skeleton`.

### 7.2 Quick view content rule
Same order for every entity: identity line, the 3 or 4 numbers that matter most, status, one "attention" line if something is wrong, last activity. The admin learns the layout once.

### 7.3 Explain this number `[MUST]`
Every metric endpoint returns `{ value, previous_value, formula_text, filters, drilldown_url }`. Example: "Collections overdue ₹4.2 Cr = sum of unpaid demands past their due date, 18 customers, 3 projects", followed by those 18 rows.

---

## 8. LANDING PAGE AND LOGIN `[MUST]`

### 8.1 Feel
Sustainable and premium: earthy colours from Section 6.2, large architecture photos with greenery and natural light, serif headlines, lots of space, slow gentle reveals on scroll. It should feel like a respected builder's website, not a software product.

### 8.2 Landing page sections (`/`)
1. **Top navigation**: Radhe Constructions wordmark (text logo in Fraunces), links (About, What we build, Sustainability, Projects), and an "Admin login" button in clay.
2. **Hero**: full-width photo (architecture with trees). Headline example: "Homes that grow with the land." Subline: one sentence on luxury homes, villas and plots built in Hyderabad with care for people and nature. Buttons: "Discover Radhe" (scrolls) and "Admin login".
3. **About**: two-column editorial layout: a short story paragraph on one side, four quiet numbers on the other (projects delivered, families, acres developed, years). Mark these as demo figures in code comments.
4. **What we build**: Apartments, Villas, Plots, Construction, Interiors. Use an editorial list with a photo that changes on hover, not five icon cards.
5. **Sustainability**: design principles such as rainwater harvesting, solar-ready rooftops, native landscaping, waste segregation, low-VOC interior materials, natural ventilation. Call them "principles", never claim real certifications for a fictional company.
6. **Featured projects**: three fictional projects (from the seed data) with locality, type and status. Clicking a card opens the login page.
7. **Closing band**: "For the Radhe leadership team" with the login button.
8. **Footer**: address placeholder (Hyderabad), a line "Demo prepared for CGI. All data is fictional."

Images: download free-to-use photos (check each licence, for example Unsplash) into `frontend/public/images/`, convert to WebP, keep each under about 300 KB, and record credits in `docs/IMAGE_CREDITS.md`. Never use photos of real, recognisable projects by other builders.

### 8.3 Login page (`/login`)
- Split screen: left half a calm architecture photo with one short line of text; right half the form.
- Fields: email, password with show/hide, "Keep me signed in" checkbox, Sign in button with loading state.
- Clear error message for wrong credentials. Rate-limit login attempts on the backend.
- Demo credentials come from `.env` (`ADMIN_EMAIL`, `ADMIN_PASSWORD`, `ADMIN_NAME`) and are seeded as an argon2 hash. They are never written in frontend code.
- An optional small "Demo access" hint below the form shows only when `VITE_SHOW_DEMO_HINT=true`, so it can be hidden for the client demo.
- After login: redirect to `/console/overview`. Any `/console/*` route without a valid session redirects to `/login`. Logout clears the cookie and returns to `/`.

---

## 9. CONSOLE PAGES

For each page: the question it answers, KPIs (max 5), main visuals, tabs, table, quick view, drawer tabs.

### 9.1 Overview `[MUST]`
**Question:** "How is Radhe doing, and what needs my attention?"
- Greeting with the admin's name and date.
- KPIs: Bookings value, Collections received, Collections overdue, Unsold inventory value, Open high risks.
- Main visual 1: Bookings vs collections, monthly, last 12 months.
- Main visual 2: **"What needs attention"**: top 5 risks, each clickable.
- Below: project health strip (one mini card per project: sold %, construction %, collection efficiency, health score), sales funnel, today's site visits and handovers, top 5 RMs and top 5 channel partners.

### 9.2 Projects & Inventory `[MUST]`
**Question:** "What are we building, what is sold, and what is not moving?"
- Project cards: type, locality, RERA number (fictional format), launch date, expected possession, sold/total, construction %, health score.
- **Unit inventory grid (the wow screen)**: choose project and tower. Rows are floors, columns are units. Each cell is coloured by status (Available, Blocked, Booked, Registered, Handed over). Toggle colouring by status, price per sq ft, days unsold, or buyer payment health. Hover a unit: number, BHK, carpet and SBA, facing, price, status, buyer, % paid, overdue. Click: unit drawer.
- Tabs below: Inventory ageing, Price trend, Towers.
- Project drawer tabs: Summary, Towers, Sales, Collections, Construction, Team.

### 9.3 Sales & Leads `[MUST]`
**Question:** "Is our sales engine healthy, and where are deals stuck?"
- KPIs: New leads, Site visits, Visit-to-booking conversion, Bookings value, Cancellations.
- Main visuals: funnel by stage; lead source performance.
- Tabs: Stalled negotiations (no activity for 14+ days, threshold in config), Lost and cancelled reasons, Channel partners (leads, bookings, value, commission pending days), All leads, All bookings.
- Quick view of a lead: budget, preferred BHK, source, owner, stage, last activity, lead score with reasons.
- Quick view of a booking: unit, value, payment plan, % paid, RM, channel partner.

### 9.4 Customers `[MUST]`
**Question:** "Who are our buyers, and who is unhappy or at risk?"
- KPIs: Total buyers, NRI share, Average health, At-risk buyers, Open queries.
- Main visuals: health distribution; buyers by type and country.
- Table: name, type, units, agreement value, % paid, overdue, last contact, health, RM.
- Quick view: units, % paid, next due, overdue, last contact and channel, open complaints, health, RM, attention line.
- Drawer tabs: Profile, Units and payments (full schedule), Interactions timeline, Complaints, Health breakdown.

### 9.5 Collections `[MUST]`
**Question:** "How much money is due, what came in, and what is stuck?"
- KPIs: Demands raised, Collected, Collection efficiency %, Overdue, **Blocked by construction delay**.
- Main visuals: receivables ageing (0-30, 31-60, 61-90, 90+ days) by project; overdue by bank.
- Tabs: All demands, Awaiting bank disbursement, Blocked demands.
- Quick view of a demand: customer, unit, milestone, amount, due date, days overdue, bank, reminders sent.

### 9.6 Construction `[MUST]`
**Question:** "Are we building on time, and what does a delay cost us?"
- KPIs: Towers on schedule, Average slip (days), Milestones due this month, Cost variance %, Open quality issues.
- Main visuals: planned vs actual milestone timeline per tower; **Delay impact panel**: for each delayed milestone, the demands it blocks, buyers affected and money not yet raised. This links Construction to Collections to Customers.
- Tabs: Contractors (on-time %, open issues), Budgets vs actual, Quality and safety log.
- Quick view of a milestone: tower, planned and actual dates, slip, contractor, cause, demands blocked.

### 9.7 Employees & Teams `[MUST]`
**Question:** "Which teams and people are doing well, and who needs support?"
- KPIs: Headcount, Average target achievement, People needing attention, Overdue tasks.
- Main visuals: performance by department; workload (for example buyers per RM).
- Table with role-specific columns. Quick view changes by role:
  - Sales: bookings vs target, site visits, conversion, stalled deals, pipeline at risk.
  - RM / CRM: buyers handled, open queries, average response time, collection efficiency.
  - Site engineer / PM: milestones owned, on-time %, open quality issues.
- Drawer tabs: Profile, Scorecard (with formula), Work, Activity, Trend.

### 9.8 Risks & Alerts `[MUST]`
- Header: "N high-priority items need attention".
- Filter by category: Construction, Collections, Sales, Customer, Inventory, People, Partner.
- Risk card: severity, title, observed facts with numbers, linked entities (clickable), suggested action, status (Open, Acknowledged, Resolved), owner. The admin can change the status.

### 9.9 Interiors `[SHOULD]`
KPIs: Active interior projects, Value, On-time %, Upsell opportunity (buyers with possession in 6 months and no package). Pipeline by stage.

### 9.10 Service & Handover `[SHOULD]`
Upcoming handovers, snags per unit, complaints by category, SLA breaches, average resolution time.

### 9.11 Reports `[SHOULD]`
Five reports: Sales MIS, Collections ageing, Inventory status, Construction progress, Team performance. Date filter, CSV export, print-friendly view.

---

## 10. SCORES AND RULES (`config/scoring.yaml`, `config/risk_rules.yaml`)

Every score shows its parts in the UI. Weights live in config. Each formula has a unit test.

- **Buyer health (0-100):** payment timeliness 40, engagement recency 25, open complaints 20, loan status 15.
- **Lead score (0-100):** budget fit with available inventory, source quality (past conversion of that source), engagement, days since last contact.
- **Project health:** schedule variance, cost variance, sales velocity vs plan, collection efficiency, open high risks.
- **Employee scorecard:** role-specific (Section 9.7), each part shows target, actual, achievement %.
- **Risk rules** (id, category, condition, severity, message template, linked entities). Examples:
  - Milestone slip > 15 days that blocks demands > ₹1 Cr: High, Construction.
  - Buyer demands overdue > 60 days: Medium; > 90 days: High.
  - Booked buyer with an open query and no contact for 21 days: Medium, Customer.
  - Negotiation idle 14+ days with value > ₹2 Cr: High, Sales.
  - Unit unsold > 270 days: Medium, Inventory.
  - RM workload > 1.5x team average: Medium, People.
  - Sales manager conversion < half the team average with 30+ site visits: Medium, People.
  - Channel partner commission pending > 45 days: Medium, Partner.

---

## 11. DATA MODEL

UUID keys, `created_at` and `updated_at`, foreign keys, indexes on every foreign key and common filters. Money as `NUMERIC(14,2)` in rupees. Area in sq ft (plots in sq yd).

```
-- access
users                id, email, name, password_hash, role ('admin'), is_active, last_login_at
audit_logs           id, user_id, action, entity_type, entity_id, details_json, created_at

-- organisation
departments          id, name
employees            id, code, name, email, phone, department_id, role_title, manager_id,
                     joined_on, status ('active','on_leave','exited')
employee_targets     id, employee_id, period_start, period_end, metric, target_value

-- projects and inventory
projects             id, name, type ('apartments','villas','plots'), locality, rera_no,
                     launch_date, expected_possession, total_acres, status, hero_image
towers               id, project_id, name, floors, units_per_floor
units                id, project_id, tower_id (nullable), unit_no, floor, config, carpet_sft,
                     sba_sft, plot_sqyd, facing, base_price_psf, plc_amount, floor_rise_amount,
                     status, listed_on, status_changed_at
price_history        id, project_id, config, price_psf, effective_from

-- sales
channel_partners     id, firm_name, contact_name, phone, city, commission_pct, status
leads                id, name, phone, email, source, channel_partner_id, budget_min, budget_max,
                     preferred_config, preferred_project_id, country, owner_employee_id,
                     stage, lost_reason, created_at
lead_activities      id, lead_id, employee_id, type ('call','whatsapp','email','meeting','note'),
                     summary, occurred_at
site_visits          id, lead_id, project_id, employee_id, scheduled_at, status, feedback
customers            id, lead_id, name, phone, email, type, is_nri, country, rm_employee_id
bookings             id, unit_id, customer_id, employee_id, channel_partner_id, booked_on,
                     agreement_value, payment_plan_id, status, cancel_reason,
                     agreement_on, registered_on, possession_on
cp_commissions       id, booking_id, channel_partner_id, amount, due_on, paid_on

-- payments
payment_plans        id, name
plan_milestones      id, payment_plan_id, seq, name, percent, construction_milestone_type
demands              id, booking_id, plan_milestone_id, construction_milestone_id (nullable),
                     amount, raised_on, due_on, status ('not_raised','raised','paid','overdue')
receipts             id, demand_id, amount, received_on, mode, from_bank_loan
home_loans           id, booking_id, bank, sanctioned_amount, disbursed_amount, status

-- construction
contractors          id, name, trade
construction_milestones  id, tower_id, type, seq, planned_date, actual_date, percent_complete,
                     contractor_id, delay_cause
project_budgets      id, project_id, category, budget_amount, actual_amount, as_of
quality_issues       id, tower_id, raised_on, category, status
safety_incidents     id, project_id, occurred_on, severity, description

-- interiors and service [SHOULD, tables created now so seed is complete]
interior_projects    id, customer_id, unit_id, designer_employee_id, package, value, stage,
                     start_date, target_date
service_tickets      id, unit_id, customer_id, category, description, status, raised_on,
                     resolved_on, sla_hours, assigned_employee_id

-- interactions and risks
customer_interactions id, customer_id, employee_id, channel, direction, summary, occurred_at,
                     needs_reply, replied_at
tasks                id, title, owner_employee_id, entity_type, entity_id, priority, due_on, status
risks                id, rule_id, category, severity, title, facts_json, entity_refs_json,
                     suggested_action, status, owner_employee_id, detected_at, resolved_at
```

---

## 12. STORY-DRIVEN SEED DATA `[MUST]`

Random data makes a boring demo. Generate realistic background data **and** plant stories the demo walks through. `tests/test_seed_stories.py` must prove each story exists after seeding.

### 12.1 Scale
- 5 projects in Hyderabad localities:
  - Radhe Skyline (apartments, Narsingi): 3 towers, under construction
  - Radhe Greens (apartments, Tellapur): 3 towers, partly delivered
  - Radhe Aranya (apartments, Gachibowli): 2 towers, recently launched
  - Radhe Vanam Villas (villas, Kokapet)
  - Radhe Bhoomi (plots, Kollur)
- About 1,600 units, 4,000 leads, 850 bookings, 18 months of history, 110 employees, 30 channel partners, 12 contractors, 8 banks.
- Seed price ranges for premium projects: about ₹8,500 to ₹14,000 per sq ft; 3 BHK 2,000 to 2,800 sq ft; 4 BHK 3,000 to 4,500 sq ft; villas ₹6 Cr to ₹14 Cr; plots priced per sq yd.
- Realistic Indian names (mostly Telugu, plus other regions); NRI buyers in Dallas, Bay Area, London, Dubai, Singapore.

### 12.2 Planted stories (numbers are targets; seed so calculations land close)
1. **Tower B delay:** Radhe Skyline, Tower B, 14th floor slab 23 days late. Cause: shuttering contractor "Sri Balaji Formworks" short of labour plus a steel delivery delay. Blocks demands of about ₹6.8 Cr for 41 bookings.
2. **Unhappy NRI buyer:** Karthik Reddy (Dallas), 4 BHK in Tower B, paid 45%, 3 emails about possession with no reply for 12 days, one open complaint. Health about 41. His RM, Sneha Rao, handles 62 active buyers vs a team average of 38.
3. **Stuck sales manager:** Arjun Varma has many site visits but 4% conversion vs team 11%, 9 negotiations idle 14+ days, about ₹14 Cr pipeline at risk.
4. **Star channel partner:** "Skyway Realty Advisors" brought 31% of villa bookings this year; commission pending 45+ days.
5. **Ageing inventory:** 22 west-facing units on floors 2 to 4 at Radhe Greens unsold for 300+ days.
6. **Bank bottleneck:** 18 buyers overdue 60+ days, about ₹4.2 Cr; 6 waiting on the same bank's disbursement.
7. **Interiors upsell:** 63 buyers with possession in the next 6 months and no interior package, about ₹9 Cr opportunity.

One command reseeds everything: `python -m seed.run --reset`.

---

## 13. READY FOR V2 AI (design now, build later)

Do not build any AI now. But structure the backend so the V2 copilot is easy:
- All calculations live in `backend/app/services/` as plain, tested Python functions (for example `get_delay_impact(tower_id)`, `get_customer_360(customer_id)`). The API routes call these. In V2, the same functions become the AI's tools.
- Keep `customer_interactions.summary` and similar text fields, so V2 can search them.
- Write the V2 copilot design into `docs/ROADMAP_V2.md` (Section 17).

---

## 14. API DESIGN

All under `/api`. Cookie session required except `/auth/login` and `/health`.

```
POST /auth/login, POST /auth/logout, GET /auth/me
GET  /health                          -> { status, database }
GET  /public/featured-projects        -> for the landing page (no auth, no personal data)
GET  /search?q=
GET  /overview
GET  /metrics/{metric_key}            -> value, previous, formula_text, filters, drilldown_url
GET  /metrics/{metric_key}/rows
GET  /projects, /projects/{id}, /projects/{id}/inventory?tower_id=
GET  /units/{id}
GET  /leads, /leads/{id}, /bookings, /bookings/{id}
GET  /sales/funnel, /sales/stalled, /sales/lost, /channel-partners, /channel-partners/{id}
GET  /customers, /customers/{id}
GET  /collections/summary, /collections/ageing, /demands
GET  /construction/summary, /construction/milestones, /construction/delay-impact
GET  /employees, /employees/{id}, /employees/{id}/scorecard
GET  /risks, PATCH /risks/{id}
GET  /interiors, /service-tickets, /reports/{key}   [SHOULD]
```
List endpoints support pagination, sorting and global filters. Every entity supports `?view=quick` (small, fast response for hover cards).

---

## 15. PHASES (build in this exact order)

At the end of **every** phase: summary, exact test steps, update `docs/PROGRESS.md`, then STOP and wait for `continue`.

### Phase 1: Plan, folders, and saving this spec
Goal: I see the whole project map in VS Code before any real code.
1. Explain the architecture in plain words (landing page, login, console, API, database, and how one hover travels through them).
2. Show and explain the folder tree below.
3. Create folders and these files:
   - `docs/SPEC.md` (this entire prompt, copied exactly), `docs/DOMAIN.md`, `docs/GLOSSARY.md`, `docs/DESIGN.md`
   - `docs/PHASES.md` (checkboxes), `docs/PROGRESS.md`, `docs/DECISIONS.md`, `docs/ROADMAP_V2.md`
   - `README.md`, `.env.example` (every variable with a comment), `.gitignore`
   - `config/brand.yaml`, `config/scoring.yaml`, `config/risk_rules.yaml`
4. No application code yet.

```
radhe-console/
├── docs/
├── config/                 # brand, scoring, risk rules
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── core/           # settings, security, logging
│   │   ├── db/             # session, base, models/
│   │   ├── schemas/        # pydantic models
│   │   ├── api/            # routers per area
│   │   ├── services/       # all business calculations (future AI tools)
│   │   ├── scoring/        # health, lead score, scorecards
│   │   └── risks/          # rule engine
│   ├── alembic/
│   ├── seed/               # generators + planted stories
│   └── tests/
└── frontend/
    ├── public/images/      # landing and login photos (WebP)
    └── src/
        ├── app/            # router, providers, auth guard
        ├── pages/
        │   ├── public/     # landing, login
        │   └── console/    # one folder per sidebar page
        ├── components/
        │   ├── ui/         # shadcn components (themed)
        │   ├── data/       # KpiCard, ChartCard, DataTable, Money, StatusPill
        │   ├── views/      # QuickView + EntityDrawer per entity
        │   ├── inventory/  # unit grid
        │   └── landing/    # landing sections
        ├── lib/            # api client, formatters (INR, dates), url state
        └── styles/         # theme tokens
```

### Phase 2: Database and backend foundation `[MUST]`
- Neon setup guide in `docs/NEON_SETUP.md` (click by click, mark changeable steps `TODO: verify`)
- FastAPI skeleton, settings, logging, `/health`
- SQLAlchemy models for all tables in Section 11, first Alembic migration, indexes
- Test: run migration against Neon, open `/health` and `/docs`

### Phase 3: Story-driven seed data `[MUST]`
- Background generators, planted stories, admin user from `.env`
- `python -m seed.run --reset`, row counts printed
- `tests/test_seed_stories.py` passes

### Phase 4: Auth and read APIs `[MUST]`
- Login, logout, `/me`, rate limit on login
- Services and routers for every `[MUST]` endpoint in Section 14, with `?view=quick`
- Metrics registry with Explain, scoring, risk engine, unit tests
- Test: log in through `/docs`, call each endpoint, `pytest` passes

### Phase 5: Frontend foundation and design system `[MUST]`
- Vite + React 19 + TS + Tailwind v4 + shadcn, themed with Section 6 tokens and fonts
- Vite proxy for `/api`, auth guard, console layout (sidebar, top bar, Ctrl+K, global filters)
- All components from Section 7.1 with loading, empty and error states
- INR and date formatters with Vitest tests
- A hidden `/console/styleguide` page showing every component, so I can review the look in one place
- Test: open the styleguide and check it against Section 6.3 and 6.4

### Phase 6: Landing page and login `[MUST]`
- Landing page sections from Section 8.2 with images, gentle scroll reveals, responsive down to tablet
- Login page from Section 8.3, real login against the backend, redirects, logout
- Image credits file
- Test: open `/`, scroll on desktop and tablet width, log in with demo credentials, log out

### Phase 7: Overview and Projects & Inventory `[MUST]`
- Overview (Section 9.1) and Projects & Inventory with the unit grid (Section 9.2)
- **Deploy now** (Vercel + Render + Neon, with the Vercel `/api` rewrite) and write `docs/DEPLOYMENT.md`. Deploying early catches cookie and environment problems while there is still time.
- Test: hover units in Radhe Skyline Tower B, open Karthik Reddy's drawer, repeat on the deployed link

### Phase 8: Sales, Customers, Collections `[MUST]`
- Pages 9.3, 9.4, 9.5 with quick views, drawers and Explain on every KPI
- Test: follow story 2 (Karthik Reddy) and story 6 (bank bottleneck)

### Phase 9: Construction and Employees `[MUST]`
- Pages 9.6 and 9.7, including the delay impact panel and role-based quick views
- Test: follow story 1 from Construction to Collections to Customers, and story 3 (Arjun)

### Phase 10: Risks, search, and cross-linking `[MUST]`
- Risks page with status changes, alerts bell, Overview attention list
- Check that every name, unit, tower, deal and partner opens its quick view and drawer
- Test: every planted story appears as a risk with clickable entities

### Phase 11: Polish, deploy, demo `[MUST]`
- Run the anti-congestion checklist (Section 6.4) on every page and fix what fails
- Performance (hover cards feel instant on the deployed link), keyboard pass, tablet pass
- Final deploy, `docs/ARCHITECTURE.md` with a diagram, `docs/DEMO_SCRIPT.md` (Section 20), final `docs/PROGRESS.md`
- **Handover packaging for CGI reviewers:**
  - `backend/Dockerfile`, `frontend/Dockerfile` (build, then serve with nginx, which also forwards `/api` to the backend)
  - `docker-compose.yml`: `postgres:16` with a healthcheck, backend waits for the database, runs migrations and seed on first start, frontend on `http://localhost:8080`
  - `.github/workflows/ci.yml`: install, run pytest and Vitest, build both Docker images, and run `docker compose up` with a smoke test on `/api/health`
  - `README.md` with three ways to see the project, easiest first: (1) live link with demo credentials, (2) `docker compose up`, (3) manual setup (Python, Node, any Postgres). Add screenshots, the architecture diagram, and a link to the demo video
  - Secret check: confirm no `.env`, Neon URL, password or token exists anywhere in the repo or its git history
- Test: CI is green, and `docker compose up` on a clean clone shows the landing page and lets me log in

### Phase 12: Should-have pages `[SHOULD]`
- Interiors, Service & Handover, Reports. Start only if Phases 1 to 11 are fully done.

---

## 16. FOUR-DAY PLAN

| Day | Phases | End-of-day check |
|---|---|---|
| Day 1 | 1, 2, 3, 4 | API returns seeded data, story tests pass |
| Day 2 | 5, 6, 7 | Landing, login, Overview and unit grid work, first deploy live |
| Day 3 | 8, 9 | Sales, customers, collections, construction, employees work with hover and drawers |
| Day 4 | 10, 11 (12 only if time is left) | Risks live, polished, deployed, demo rehearsed, no new features |

---

## 17. VERSION 2 ROADMAP (`docs/ROADMAP_V2.md`, do not build now)

**AI Copilot (top V2 item):** a floating "Ask" panel that knows the current page and pinned entity. Gemini with function calling, using only the tested service functions from Section 13 as tools (no free-form SQL), a read-only database user, answers in "Observed / Possible reasons / Suggested next steps / Sources" format, source chips that open drawers, a check that every number in an answer appears in tool results, and RAG over brochures, site reports and meeting notes using pgvector. Example questions: "What is the impact of the Tower B delay?", "Which NRI buyers need a call today?", "Why is Arjun's conversion low?"

Other V2 ideas for Radhe:
- Land Bank page and Administration page (users, roles, audit log viewer)
- Data entry: create and edit leads, bookings, milestones
- WhatsApp Business updates and payment reminders for buyers
- Buyer app: payment schedule, receipts, progress photos, raise snags
- Channel partner portal: register leads, track commissions
- Site engineer mobile app: daily progress, photos, issues, safety checklist
- Drone and 360 photo progress linked to milestones
- Integration with the existing ERP for accounts and procurement
- Predictions: cancellation risk, lead conversion, collection delay, price per unit
- Role-based access for each team, then SSO

---

## 18. KNOWN PROBLEMS AND HOW WE HANDLE THEM

| Problem | Solution |
|---|---|
| Too much for 4 days | Read-only console, reusable components, `[MUST]` first, AI moved to V2 |
| Looks AI-made or template-like | Section 6 tokens, fonts and avoid-list; styleguide review in Phase 5 |
| Pages feel crowded | Section 6.4 rules, tabs, column chooser, checklist in Phase 11 |
| Fake-looking data | Story-driven seed with Hyderabad localities and realistic prices |
| Login breaks after deploy | Same-site `/api` via Vercel rewrite; deploy early in Phase 7 |
| Backend sleeps before the demo | Paid instance for demo week, or warm it up a few minutes before; keep a recorded demo video as backup |
| Library setup changed | `TODO: verify` and check official docs |
| Client asks for more | Everything new goes to `docs/ROADMAP_V2.md` |
| Reviewers cannot run the code | Live link first, Docker Compose second, manual steps third; CI proves the build works |
| Docker will not install on my laptop | CI builds and runs the containers on GitHub's Linux machines instead |

---

## 19. DEFINITION OF DONE

- [ ] Landing page looks premium and calm on desktop and tablet, with no "AI-made" signs from Section 6.3
- [ ] Admin logs in with demo credentials from `.env`; wrong password shows a clear error; logout works
- [ ] Console routes are protected
- [ ] Admin understands the business from Overview within 30 seconds
- [ ] Every page passes the anti-congestion rules in Section 6.4
- [ ] Every KPI opens Explain with formula and rows
- [ ] Hover any person, unit, deal, tower or partner shows a quick view; click pins a drawer; links stack with a breadcrumb
- [ ] Unit grid works with all four colourings
- [ ] Tower B story can be followed: Construction > delay impact > blocked demands > buyers > Karthik Reddy > Sneha Rao's workload
- [ ] All 7 planted stories appear in Risks & Alerts
- [ ] Ctrl+K search finds any entity
- [ ] Money in ₹ lakh/crore, dates in IST
- [ ] Tests pass for scores, risk rules, metrics, formatters and seed stories
- [ ] Deployed demo link works
- [ ] A fresh clone runs with `docker compose up` and CI is green
- [ ] README lets a reviewer see the project in under 5 minutes; no secrets in the repo or history

---

## 20. DEMO SCRIPT (about 6 minutes, save as `docs/DEMO_SCRIPT.md`)

1. **Landing page (30 s):** scroll slowly through the story and sustainability section, click Admin login.
2. **Login and Overview (45 s):** bookings, collections, unsold value, project health. "Leadership sees the whole group on one screen."
3. **Attention list (20 s):** click "Tower B delay blocks ₹6.8 Cr in demands".
4. **Construction (60 s):** 23-day slip, contractor and cause, delay impact panel with 41 buyers.
5. **Collections and Customers (60 s):** hover a blocked demand, hover Karthik Reddy, pin his drawer: 3 unanswered emails, health 41. Click his RM, Sneha Rao: 62 buyers vs average 38.
6. **Inventory grid (45 s):** switch Radhe Greens to "days unsold"; the west-facing low floors light up.
7. **Sales (45 s):** hover Arjun Varma, idle negotiations, pipeline at risk. Click Explain on conversion.
8. **Close (30 s):** "Every number traces back to real rows. Next, an AI copilot will answer questions on this same connected data." Show `ROADMAP_V2.md`.

---

## START NOW

Begin with **Phase 1 only**. Explain the architecture in plain words, show and explain the folder tree, then explain and create each Phase 1 file one by one (including saving this whole prompt as `docs/SPEC.md`). Then summarise, update `docs/PROGRESS.md`, and wait for me to type `continue`.
