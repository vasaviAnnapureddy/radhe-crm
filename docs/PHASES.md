# Phases

Build in this exact order. Full details are in `docs/SPEC.md` Section 15. Tick a box only when the phase's test steps pass.

## Day 1
- [x] **Phase 1: Plan, folders, spec saved.** Docs, config files, folder tree. No app code.
- [x] **Phase 2: Database and backend foundation.** Neon guide, FastAPI skeleton, `/health`, all models, first migration.
- [x] **Phase 3: Story-driven seed data.** Generators, 7 planted stories, admin user, `tests/test_seed_stories.py`.
- [x] **Phase 4: Auth and read APIs.** Login, all MUST endpoints, metrics with Explain, scoring, risk engine, tests.

## Day 2
- [x] **Phase 5: Frontend foundation and design system.** Vite, theme, layout, reusable components, formatters, styleguide page.
- [x] **Phase 6: Landing page and login.** Eight landing sections, login, redirects, image credits.
- [ ] **Phase 7: Overview and Projects & Inventory.** Unit grid. First deploy (Vercel + Render + Neon). (Pages done and liked by the developer; the deploy is still pending.)

## Day 3
- [x] **Phase 8: Sales, Customers, Collections.**
- [x] **Phase 9: Construction and Employees.** Delay impact panel, role-based quick views.

## Day 4
- [x] **Phase 10: Risks, search, cross-linking.**
- [ ] **Phase 10B: Employee and customer portals.** (added 02 Oct; code done; tick after the developer signs in as each role on Neon data)
- [ ] **Phase 11: Polish, deploy, demo.** Anti-congestion checklist, Docker, CI, README, demo script, secret check.
- [ ] **Phase 12: Should-have pages.** Interiors, Service & Handover, Reports. Only if 1 to 11 are fully done.

## Rules that apply to every phase
- Explain each file before creating it.
- End with: summary, test steps, update `docs/PROGRESS.md`, safety and privacy check, then stop for `continue`.
- `[MUST]` before `[SHOULD]`. Never build `[V2]`.
