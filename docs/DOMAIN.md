# Domain: how Radhe Constructions works

> Copied from docs/SPEC.md. If the two ever differ, SPEC.md wins.

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


