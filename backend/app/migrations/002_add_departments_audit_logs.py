"""
Migration 002 — Add departments, audit_logs tables; add is_active/email/status columns.

Run:  python -m app.migrations.002_add_departments_audit_logs
Or tables are auto-created on server startup via create_all().
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from sqlalchemy import inspect, text
from app.models.db_models import Base, engine


def column_exists(inspector, table: str, col: str) -> bool:
    return any(c["name"] == col for c in inspector.get_columns(table))


def upgrade():
    inspector = inspect(engine)
    existing = set(inspector.get_table_names())

    # Create missing tables
    missing = [t for t in Base.metadata.tables if t not in existing]
    if missing:
        Base.metadata.create_all(bind=engine, tables=[Base.metadata.tables[n] for n in missing])
        print(f"Created tables: {', '.join(missing)}")
    else:
        print("All tables already exist.")

    # Add columns to existing tables if they don't exist (SQLite ALTER TABLE)
    with engine.connect() as conn:
        if "users" in existing:
            if not column_exists(inspector, "users", "is_active"):
                conn.execute(text("ALTER TABLE users ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT 1"))
                print("Added users.is_active")
            if not column_exists(inspector, "users", "email"):
                conn.execute(text("ALTER TABLE users ADD COLUMN email VARCHAR(255)"))
                print("Added users.email")

        if "documents" in existing:
            if not column_exists(inspector, "documents", "status"):
                conn.execute(text("ALTER TABLE documents ADD COLUMN status VARCHAR(20) NOT NULL DEFAULT 'ready'"))
                print("Added documents.status")

        conn.commit()
    print("Migration 002 complete.")


if __name__ == "__main__":
    upgrade()
