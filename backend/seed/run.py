"""Fill the database with demo data.

Run from the backend folder:
    python -m seed.run --reset                 wipe everything, then seed
    python -m seed.run --reset --as-of 2026-10-04   seed as if today were that date
"""
import argparse
from datetime import date

from sqlalchemy import func, select, text

from app.core.config import get_settings
from app.core.security import hash_password
from app.db.models import Base, Project, User
from app.db.session import get_engine
from seed.build import add_portal_users, build_world, insert_rows


def wipe(conn) -> None:
    """Empty our tables. Alembic's own bookmark table is left alone."""
    tables = list(reversed(Base.metadata.sorted_tables))
    if conn.dialect.name == "postgresql":
        conn.execute(text("TRUNCATE TABLE " + ", ".join(t.name for t in tables) + " CASCADE"))
    else:
        for table in tables:
            conn.execute(table.delete())


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed the Radhe Constructions demo data.")
    parser.add_argument("--reset", action="store_true", help="delete all existing data first")
    parser.add_argument("--as-of", type=date.fromisoformat, default=date.today(), help="treat this date as today")
    args = parser.parse_args()

    settings = get_settings()
    if not (settings.admin_email and settings.admin_password and settings.admin_name):
        raise SystemExit("ADMIN_EMAIL, ADMIN_PASSWORD and ADMIN_NAME must be set in .env")

    print(f"Building demo data as of {args.as_of:%d %b %Y} ...")
    world = build_world(args.as_of)
    world.add(User(email=settings.admin_email.lower(), name=settings.admin_name, role="admin", is_active=True,
                   password_hash=hash_password(settings.admin_password)))
    if settings.portal_password:
        count = add_portal_users(world, hash_password(settings.portal_password))
        print(f"Added {count:,} portal logins (employees and buyers). They share the PORTAL_PASSWORD from .env.")
    else:
        print("PORTAL_PASSWORD is empty in .env, so no employee or customer logins were created.")

    # One transaction: if anything fails, the database is left exactly as it was.
    with get_engine().begin() as conn:
        has_data = conn.execute(select(func.count()).select_from(Project)).scalar()
        if has_data and not args.reset:
            raise SystemExit("The database already has data. Add --reset to wipe it and seed again.")
        if args.reset:
            print("Wiping existing data ...")
            wipe(conn)
        print("Inserting rows (this can take a minute on Neon) ...")
        counts = insert_rows(conn, world.rows)

    for name, count in counts.items():
        print(f"  {name:<26}{count:>7,}")
    print(f"  {'TOTAL':<26}{sum(counts.values()):>7,}")
    print("Done. The admin login is the ADMIN_EMAIL and ADMIN_PASSWORD from your .env file.")


if __name__ == "__main__":
    main()
