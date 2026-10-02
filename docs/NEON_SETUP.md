# Neon setup (the database)

Neon is a hosted PostgreSQL database. We use the same Neon database on the laptop and for the deployed demo.

> **The one rule:** the connection string contains the database password. It goes into the `.env` file only. Never paste it into a chat, a commit, a screenshot or a document.

Neon changes its screens sometimes. Steps marked `TODO: verify` may look a little different.

## 1. Get the connection string

1. Open `console.neon.tech` and sign in.
2. Create a new project just for this work, for example `radhe-console`. Choose a region close to India (Singapore) if offered. `TODO: verify` region names.
3. On the project dashboard, click **Connect**. `TODO: verify` button name.
4. In the box that opens:
   - Leave branch, database and role at their defaults.
   - Turn **Connection pooling off**. The address must not contain `-pooler`. A direct connection is the safe choice for creating tables.
   - Click **Show password**, so the copied text has the real password and not dots.
5. Click **Copy**. The text starts with `postgresql://` and ends with something like `sslmode=require`.

## 2. Put it in `.env`

1. In VS Code, open `E:\radhe-console\.env`.
2. Find the line `DATABASE_URL=`.
3. Paste the string right after the `=` sign. No spaces, no quotes, all on one line.
4. Save with Ctrl+S.

Paste it exactly as Neon gives it. The backend changes `postgresql://` to the format it needs by itself (`backend/app/core/config.py`).

## 3. Create the tables

In a VS Code terminal (Terminal menu, New Terminal):

```
cd E:\radhe-console\backend
.\.venv\Scripts\Activate.ps1
alembic upgrade head
```

This runs the migration in `backend/alembic/versions/` and creates all 31 tables. Running it a second time is safe; it does nothing if the tables are already there.

## 4. Check it worked

- In Neon, open **Tables** in the left menu. You should see 32 tables: our 31 plus `alembic_version`, which is Alembic's own bookmark.
- Or start the backend and open the health page (see `docs/PROGRESS.md`).

## If something goes wrong

| What you see | What to do |
|---|---|
| `DATABASE_URL is empty` | The string is not saved in `.env`, or there is a space after `=`. |
| `password authentication failed` | You copied the string with dots. Click **Show password** in Neon and copy again. |
| The first command hangs for a few seconds | Normal. Neon's free plan sleeps after 5 minutes idle and wakes on the next query. |
| `Activate.ps1 cannot be loaded` | Run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once, then try again. |
| The string was shared by mistake | In Neon, open **Roles**, reset the password, copy the new string into `.env`. `TODO: verify` menu name. |

## Good to know

- Free plan: compute pauses after 5 minutes idle. Our data is small and fits the free storage limit.
- For the deployed backend (Phase 7), the same string is entered in Render's environment settings, never in the code.
