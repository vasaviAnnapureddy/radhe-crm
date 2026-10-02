"""Test setup. Tests use a throwaway SQLite file, never the real Neon database."""
import os
import tempfile
from datetime import date
from pathlib import Path

import pytest

# Must be set before any app code is imported. These override whatever is in .env.
_db_file = Path(tempfile.mkdtemp(prefix="radhe_test_")) / "test.db"
os.environ.update({
    "DATABASE_URL": f"sqlite:///{_db_file.as_posix()}",
    "ENVIRONMENT": "test",
    "JWT_SECRET": "test-only-secret-not-used-anywhere-else",
    "ADMIN_EMAIL": "admin@test.local",
    "ADMIN_PASSWORD": "test-only-password",
    "ADMIN_NAME": "Test Admin",
    "PORTAL_PASSWORD": "portal-test-only",
    "COOKIE_SECURE": "false",
})


@pytest.fixture(scope="session")
def world():
    """The full seed data, built once for the whole test run."""
    from app.core.security import hash_password
    from seed.build import add_portal_users, build_world
    built = build_world(date.today())
    add_portal_users(built, hash_password(os.environ["PORTAL_PASSWORD"]))
    return built


@pytest.fixture(scope="session")
def snapshot(world):
    from app.services.snapshot import Snapshot
    return Snapshot(world.rows, world.today)
