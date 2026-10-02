"""Tells Alembic which tables we want (our models) and which database to compare against."""
from alembic import context

from app.db.models import Base
from app.db.session import get_engine

target_metadata = Base.metadata

if context.is_offline_mode():
    raise SystemExit("Offline mode is not used in this project. Run: alembic upgrade head")

with get_engine().connect() as connection:
    context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
    with context.begin_transaction():
        context.run_migrations()
