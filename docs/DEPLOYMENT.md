# Deployment

Three services, all on free plans:

```
Browser  ->  Vercel (frontend)  --/api-->  Render (backend)  ->  Neon (database)
```

The browser only ever talks to the Vercel address. Vercel forwards anything starting with `/api` to Render. This keeps the login cookie on one address, so there are no cross-site cookie problems.

Steps marked `TODO: verify` may look a little different on the day; the dashboards change.

## Before you start
- The code is pushed to GitHub: https://github.com/vasaviAnnapureddy/radhe-crm
- You have your Neon connection string (the same one that is in `.env`).
- You have the `JWT_SECRET` value from `.env`.
- **Never paste these into a chat, a commit or a screenshot.** They are typed only into the Render dashboard.

## 1. Backend on Render
1. Go to `render.com`, sign in with GitHub.
2. **New** -> **Blueprint**. Pick the `radhe-crm` repository. Render reads `render.yaml`. `TODO: verify` menu names.
3. It asks for two secret values:
   - `DATABASE_URL`: paste the Neon string, exactly as in `.env`.
   - `JWT_SECRET`: paste the value from `.env`.
4. Click **Apply**. The first build takes a few minutes.
5. When it says **Live**, copy the service address. It looks like `https://radhe-console-api.onrender.com`. If that name was taken, yours will be slightly different.
6. Check: open `<that address>/api/health`. Expected: `{"status":"ok","database":"ok"}`.

If you prefer not to use a Blueprint: **New** -> **Web Service**, root directory `backend`, build command `pip install -r requirements.txt`, start command `uvicorn app.main:app --host 0.0.0.0 --port $PORT`, and add the environment variables listed in `render.yaml` by hand.

## 2. Point the frontend at your backend
Open `frontend/vercel.json`. If your Render address is not exactly `https://radhe-console-api.onrender.com`, change it on the first `destination` line. Keep `/api/:path*` at the end. Commit and push.

## 3. Frontend on Vercel
1. Go to `vercel.com`, sign in with GitHub.
2. **Add New** -> **Project**. Import `radhe-crm`.
3. Set **Root Directory** to `frontend`. Framework preset: **Vite**. Build command `npm run build`, output directory `dist` (these are usually filled in for you). `TODO: verify`.
4. Environment variables: add `VITE_SHOW_DEMO_HINT` = `false`.
5. Click **Deploy**.
6. Open the Vercel address. You should see the landing page.

## 4. Check the deployed site
The deployed site uses the same Neon database as your laptop, so the logins are the ones in your `.env`. Nothing has to be seeded on Render.

1. Landing page loads, with photos and the three project cards.
2. **Sign in** with the `.env` admin email and password. You land on Overview.
   - If the very first sign-in fails or takes long, Render was asleep. Wait a minute and try again.
3. Refresh the page: you stay signed in (this proves the cookie works across Vercel and Render).
4. Open **Projects & Inventory**, pick Radhe Skyline, Tower B. Hover a unit. Click unit `B-3004` and then the buyer, Karthik Reddy.
5. Log out. Open `/console/overview` directly: you are sent to the login page.
6. Sign in with `PORTAL_CUSTOMER_EMAIL` and `PORTAL_PASSWORD`: you land on "My journey". Then try opening `/console/overview`: you are sent back to your own page.
7. Sign in with `PORTAL_RM_EMAIL`: you land on "My day".

## Things to know for demo week
- **Render's free plan sleeps** after about 15 minutes without visitors. The first request after that can take 30 to 60 seconds. Either open the site a few minutes before the demo, or upgrade the backend to the cheapest paid instance for the week.
- **Neon's free plan** pauses after 5 minutes idle and wakes on the next query, in a second or two.
- **Reseed on demo morning** so day counts are fresh: on your laptop run `python -m seed.run --reset` (it writes to the same Neon database the deployed site uses). The backend picks up new data within 10 minutes, or straight away if you restart the Render service (**Manual Deploy** -> **Restart**). `TODO: verify` button name.
- Keep a **recorded demo video** as a backup.
- The API docs page (`/docs`) is switched off in production.

## If something goes wrong
| What you see | Likely cause |
|---|---|
| Landing page works, login says "Cannot reach the server" | The address in `frontend/vercel.json` is wrong, or Render is still waking up. |
| Login works but you are signed out on refresh | `COOKIE_SECURE` is not `true` on Render, or the frontend is calling Render directly instead of `/api`. |
| Render build fails on `psycopg` | Python version is not 3.12; check `PYTHON_VERSION` in `render.yaml`. |
| `/api/health` shows `"database":"error"` | `DATABASE_URL` on Render is wrong or has a space at the end. |
| Opening `/console/overview` directly gives a Vercel 404 | The second rewrite in `vercel.json` (everything to `/index.html`) is missing. |
