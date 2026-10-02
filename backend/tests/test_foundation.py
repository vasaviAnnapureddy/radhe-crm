from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect

from app.core.config import Settings
from app.db.models import Base
from app.main import app


def test_health_reports_api_and_database():
    response = TestClient(app).get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


def test_all_31_tables_can_be_created():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    assert len(inspect(engine).get_table_names()) == 31


def test_every_foreign_key_is_indexed():
    for table in Base.metadata.tables.values():
        for column in table.columns:
            if column.foreign_keys:
                assert column.index, f"{table.name}.{column.name} has no index"


def test_neon_url_is_switched_to_the_psycopg_driver():
    settings = Settings(database_url="postgresql://u:p@host/db?sslmode=require")
    assert settings.database_url == "postgresql+psycopg://u:p@host/db?sslmode=require"
