# Demo script (about 7 minutes)

## Before the demo
1. **Load fresh data that morning**, so the day counts match this script. On the laptop, in the backend terminal: `python -m seed.run --reset`. Then in Render, restart the service (or wait 10 minutes).
2. **Wake the site** five minutes before: open https://radhe-crm.vercel.app/ and sign in once.
3. Keep the top bar on **All time** (the default).
4. Have `.env` open in another window for the four logins. Do not show it on screen.
5. Keep a recorded video of this walk as a backup.

Numbers below are what a fresh load gives. Unit numbers and a few counts can differ slightly after a reseed; the story is the same.

## 1. Landing page (30 seconds)
Scroll slowly through the story, "What we build" (hover the five lines) and the sustainability principles. Click **Sign in**.

> "This is the public face. Calm, premium, and it invites the team and the home owners to sign in."

## 2. Admin: Overview (45 seconds)
Sign in as admin. Point at the five cards, the bookings and collections chart, and the project health strip.

> "Leadership sees the whole group on one screen. Every card has a small icon that explains the number."

Click the info icon on **Collections overdue**: formula, filters, and the exact rows. Close it.

## 3. What needs attention (20 seconds)
In the list on the right, click **"Tower B delay blocks ₹6.8 Cr in demands"**.

## 4. Construction (60 seconds)
> "The 14th floor slab of Tower B is 23 days late. Here is what that costs."

Show the delay card: ₹6.8 Cr not yet raised, 41 bookings, the contractor and the reported cause. Scroll to the timeline: one red cell. Hover it.

> "A site problem becomes a cash-flow problem. This screen makes that link visible."

## 5. Collections and Customers (60 seconds)
Click **"See the 41 blocked demands in Collections"**. Hover **Karthik Reddy**, then click him.

> "He is an NRI buyer in Dallas. He has paid 45 percent. He has written three times about possession and nobody has replied for 12 days. His health score is in the red."

In his drawer, click his relationship manager, **Sneha Rao**.

> "She looks after 62 buyers. The team average is 38. The problem is workload, not attitude."

Press the browser Back button to show the drawer steps back.

## 6. Inventory grid (45 seconds)
Open **Projects & Inventory**, click **Radhe Greens**, then **Tower B**, then **Days unsold**.

> "The west-facing homes on floors 2 to 4 light up. Twenty-two units, unsold for 300 days. That is locked money."

## 7. Sales and people (45 seconds)
Open **Employees & Teams**, click **Sales**, hover **Arjun Varma**, then click him.

> "Plenty of site visits, but 4 percent conversion against a team average of 11. Nine negotiations with no activity, ₹14 Cr at risk."

Show the **Connections** tab.

## 8. The same data, for each person (60 seconds)
Log out. Sign in as the **home owner**.

> "This is what Karthik sees. Where he is, what happens next, and an honest line about the delay: his next payment is on hold until the slab is complete."

Scroll to **My home** and the table of all 11 payments. Log out. Sign in as the **relationship manager**.

> "And this is Sneha's day: the same three emails are in her list, waiting for a reply. She sees only her own buyers."

## 9. Close (30 seconds)
> "Every number traces back to real rows. Each person sees only what is theirs. Next, an AI copilot will answer questions on this same connected data, using only these tested calculations."

Show `docs/ROADMAP_V2.md`.

## If something goes wrong
| Problem | What to do |
|---|---|
| First sign-in hangs | The backend was asleep. Wait a minute, try again. |
| Numbers differ from this script | The data is older than today. Reseed and restart the Render service. |
| The site is down | Play the recorded video. |
