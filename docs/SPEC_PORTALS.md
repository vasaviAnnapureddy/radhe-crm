# MEGA PROMPT ADDENDUM: Employee and Customer portals (small, read-only)

> **STATUS: PARKED DRAFT (02 Oct 2026). Do not build from this yet.** The developer decided to finish the admin console first (Phases 7 to 11 of `docs/SPEC.md`) and look at portals afterwards. She also wants hover cards and drawers in the portals, so Sections 2.4, 8 (`strip_refs`) and 12 of this draft must be revised before building: entity views would need per-role ownership checks instead of being removed. `docs/PHASES.md` is unchanged and Phase 12 is not dropped.

> How to use: this file adds to `docs/SPEC.md`. Read `docs/PROGRESS.md` first, then this file. It is built as **Phase 10B**, after Phase 10 and before Phase 11. All working rules in `docs/SPEC.md` Section 0 still apply (explain each file, simple language, stop at the end for `continue`).
>
> This changes two rules of the original spec, on the developer's request (02 Oct 2026): Golden Rule 2 ("one admin, no other logins") and the V2 items "Buyer app" and employee access. Everything else stays.

## 1. What we are adding, in one paragraph

Two small portals next to the admin console. A **customer** signs in and sees only their own home, payments and requests. An **employee** signs in and sees only their own day, work and scorecard. Both use the same login page as the admin; the server decides where each person lands. Both are read-only. The pitch line: **"The same connected data, shown to each person at their own level."**

## 2. Hard limits (to protect the deadline and the token budget)

1. **Four menu items per portal.** No more.
2. **Read-only.** No forms, no edits. (One optional write is listed in Section 9 and is `[SHOULD]`.)
3. **Reuse, do not rebuild.** Use the existing `DataTable`, `KpiCard`, `Card`, `PageHeader`, `BlockView`, `StatusPill`, `Money`, `DateText` and the existing service functions. No new chart types, no new component library.
4. **No hover cards and no drawers in the portals.** Names and units are plain text there. This avoids exposing other people's records through entity links.
5. **No new design.** Same tokens, fonts and anti-congestion rules (`docs/DESIGN.md`). Max 4 KPI cards per page.
6. **Demo accounts only.** Three seeded logins (Section 5). No sign-up, no password reset, no user management screen.
7. Target size: about 250 lines of backend, 350 lines of frontend, 80 lines of tests. If it grows past that, stop and cut scope.

## 3. Roles and where they land

| Role | Signs in at | Lands on | Can call |
|---|---|---|---|
| `admin` | `/login` | `/console/overview` | all existing `/api/...` console routes |
| `employee` | `/login` | `/employee/day` | only `/api/portal/employee/...` |
| `customer` | `/login` | `/my/home` | only `/api/portal/customer/...` |

- A signed-in person who opens another role's area is sent to their own landing page.
- The landing page keeps one button, now labelled **Sign in** (not "Admin login"), since three kinds of people use it.

## 4. Security rules (most important section)

1. **Scope comes from the session, never from the request.** Portal routes take no customer id or employee id. The server reads the signed-in user, finds the linked `customer_id` or `employee_id`, and returns only that person's data.
2. **Console routes become admin-only.** Add a `require_role("admin")` dependency to the console router. An employee or customer calling `/api/customers` gets 403.
3. **Portal routes check the role too.** A customer calling an employee route gets 403, and the other way round.
4. **A customer never sees:** other buyers, health score, risk records, internal notes, lead score, the RM's workload, or channel partner commission.
5. **An employee never sees:** other employees' scorecards, or buyers and leads not assigned to them.
6. Phones and emails: a person sees their own in full. An employee sees their buyers' phones masked, as in the admin tables.
7. Tests must prove rules 1 to 3 (Section 8).

## 5. Data changes

One small migration, `0002_portal_users`:

```
users   add  employee_id  (nullable, FK employees.id, indexed)
        add  customer_id  (nullable, FK customers.id, indexed)
        role is now one of: 'admin', 'employee', 'customer'
```

Seed three extra users (argon2 hash, password from `.env`, never in code):

| Login | Role | Linked to | Why this person |
|---|---|---|---|
| `PORTAL_CUSTOMER_EMAIL` | customer | Karthik Reddy | Story 2: his demand is blocked by the Tower B delay, 3 unanswered queries |
| `PORTAL_RM_EMAIL` | employee | Sneha Rao (Relationship Manager) | Story 2: 62 buyers, open queries |
| `PORTAL_SALES_EMAIL` | employee | Arjun Varma (Sales Manager) | Story 3: stalled negotiations |

New `.env` variables (add to `.env.example` with comments): `PORTAL_CUSTOMER_EMAIL`, `PORTAL_RM_EMAIL`, `PORTAL_SALES_EMAIL`, `PORTAL_PASSWORD` (one shared demo password for the three). If `PORTAL_PASSWORD` is empty, the seed skips these users and says so.

## 6. Customer portal (`/my/...`)

Sidebar: **My home, Payments, Requests, Profile**, then Log out.

| Page | What it shows | Built from (already exists) |
|---|---|---|
| **My home** `/my/home` | Greeting. For each unit: unit number, type, area, facing, tower. Construction progress of the tower as a simple list of the 9 stages with planned and actual dates and a state pill (done, in progress, late). If a stage is late, one honest line: "The 14th floor slab is running 23 days late. Your next payment will be asked for only after it is complete." | `Unit`, `ConstructionMilestone`, `milestone_row` |
| **Payments** `/my/payments` | 3 KPI cards: Paid so far, Next due (amount and date), Overdue. Then the full payment schedule table and a receipts table. | `schedule()`, `demands`, `receipts` tables |
| **Requests** `/my/requests` | The customer's own messages and service tickets as a timeline, each with a state: "Answered" or "Waiting for our reply". | `CustomerInteraction`, `ServiceTicket` |
| **Profile** `/my/profile` | Name, phone, email, and their relationship manager's name and email. | `Customer`, `Employee` |

## 7. Employee portal (`/employee/...`)

Sidebar: **My day, My work, My scorecard, Profile**, then Log out.

| Page | What it shows | Built from (already exists) |
|---|---|---|
| **My day** `/employee/day` | Greeting. Up to 4 KPI cards chosen by role (below). Then "Needs my attention": tasks that are overdue or due this week. | `employee_scorecard`, `Task` |
| **My work** `/employee/work` | One or two tables by role (below). | `sales_stats`, `rm_stats`, existing tables |
| **My scorecard** `/employee/scorecard` | The scorecard block: each part with target, actual, achievement and weight, plus the formula line. For sales, the bookings-per-quarter chart. | `employee_scorecard`, `_trend` |
| **Profile** `/employee/profile` | Code, role, department, manager, joined date, email, phone. | `Employee` |

Role-specific content:

| Role | My day KPIs | My work tables |
|---|---|---|
| Sales Manager, NRI Desk Manager | Bookings (90 days), Site visits (90 days), My conversion, Stalled deals | Stalled negotiations; My open leads |
| Relationship Manager | Buyers handled, Open queries, Average reply time, Collection efficiency | Queries waiting for a reply; My buyers |
| Site Engineer, Project Manager | Milestones owned, On time %, Open quality issues | My milestones; My quality issues |
| Everyone else | Overdue tasks | My tasks |

## 8. API (all under `/api/portal`, session required)

```
GET /auth/me                         -> now also returns role and home path ("/console/overview", "/employee/day", "/my/home")

GET /portal/customer/home            -> { greeting, units:[{facts, stages}], notice }
GET /portal/customer/payments        -> { kpis:[...], schedule: table, receipts: table }
GET /portal/customer/requests        -> { timeline: block }
GET /portal/customer/profile         -> { facts }

GET /portal/employee/day             -> { greeting, kpis:[...], tasks: table }
GET /portal/employee/work            -> { tables:[table, ...] }
GET /portal/employee/scorecard       -> { scorecard block, trend chart or null }
GET /portal/employee/profile         -> { facts }
```

- Replies reuse the existing shapes (`facts`, `table`, `timeline`, `scorecard`, `chart` blocks), so the frontend renders them with `BlockView`.
- Before sending, a small `strip_refs()` helper turns every `ref` cell into plain text (its label), so no entity ids of other people leave the server.
- All logic goes in one new file, `backend/app/services/portal.py`, and one router, `backend/app/api/portal.py`.

Tests (`backend/tests/test_portal.py`):
- customer login can read all four customer routes and sees only Karthik's unit;
- customer gets 403 on `/api/customers`, `/api/overview` and every `/api/portal/employee/...` route;
- employee gets 403 on console routes and customer routes;
- admin still reaches the console routes;
- no reply from a customer route contains another customer's name, or the words "health" or "risk";
- no portal reply contains a `ref` object.

## 9. Frontend

- `src/app/PortalLayout.tsx`: the same sidebar and top-bar style as the console, but with the 4 menu items, no search, no filters, no bell. One layout serves both portals (it takes the menu as a prop).
- `src/app/auth.tsx`: `AuthGuard` takes an allowed role; a wrong role is redirected to that person's home path. After login, go to the `home` path from `/auth/me`.
- `src/pages/portal/CustomerPages.tsx` and `EmployeePages.tsx`: each page is a `PageHeader`, optional KPI cards, and `BlockView` for each block in the reply. Keep each page under about 40 lines.
- `KpiCard` gets a simple variant without the Explain icon (portal KPIs are plain numbers sent by the portal route).
- Landing page and login page: change "Admin login" to "Sign in"; the login heading becomes "Sign in" with the line "For the Radhe team and home owners."

`[SHOULD]`, only if every `[MUST]` in all phases is done: a "Raise a request" box on the customer Requests page that creates one `service_tickets` row, which then shows up in the admin console. This is the only write. Skip it if short on time.

## 10. Phase 10B checklist

1. Migration `0002`, model columns, seed the three portal users, `.env.example` variables.
2. `require_role` dependency; console router admin-only; `/auth/me` returns role and home.
3. `services/portal.py`, `api/portal.py`, `tests/test_portal.py`.
4. `PortalLayout`, role-aware `AuthGuard`, the eight small pages, wording changes on landing and login.
5. Update `docs/PROGRESS.md`, `docs/PHASES.md`, `docs/DECISIONS.md`, `docs/GLOSSARY.md` ("portal", "role").
6. Test steps for the developer:
   - add the four `PORTAL_...` lines to `.env`, run `alembic upgrade head`, then `python -m seed.run --reset`;
   - sign in as the customer: see Karthik's home, the late-stage notice, 45% paid, three requests waiting;
   - sign in as Sneha: see 62 buyers and her open queries; sign in as Arjun: see 9 stalled deals;
   - while signed in as the customer, open `/console/overview`: you are sent back to `/my/home`.

## 11. What to cut from the original plan to pay for this

- **Phase 12 (Interiors, Service & Handover, Reports pages) is dropped** and moved to `docs/ROADMAP_V2.md`.
- Demo script (Section 20 of the spec) gains one 40-second step after Sales: sign in as Karthik Reddy, show his home and the honest delay notice; then sign in as Sneha Rao and show the same three queries waiting in her list.

## 12. Definition of done for the portals

- [ ] Three demo logins work and each lands in the right place
- [ ] A customer cannot reach any console or employee data (proved by tests)
- [ ] An employee cannot reach console data or another employee's data (proved by tests)
- [ ] Each portal has exactly four menu items and passes the anti-congestion rules
- [ ] Karthik's portal shows the Tower B delay notice and his blocked next payment
- [ ] No hover cards, drawers or entity ids of other people in any portal reply
