"""
Migration 001 — Add chat_sessions and chat_messages tables.

Run:  python -m app.migrations.001_add_chat_sessions_messages
Or tables are auto-created on server startup via create_all().
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from sqlalchemy import inspect, text
from app.models.db_models import Base, engine


def upgrade():
    inspector = inspect(engine)
    existing = set(inspector.get_table_names())
    missing = [t for t in Base.metadata.tables if t not in existing]

    if not missing:
        print("All tables already exist — nothing to migrate.")
        return

    Base.metadata.create_all(bind=engine, tables=[Base.metadata.tables[n] for n in missing])
    print(f"Created tables: {', '.join(missing)}")

    with engine.connect() as conn:
        if engine.dialect.name == "sqlite":
            conn.execute(text(
                "CREATE INDEX IF NOT EXISTS ix_chat_sessions_user_updated "
                "ON chat_sessions (user_id, updated_at)"
            ))
            conn.execute(text(
                "CREATE INDEX IF NOT EXISTS ix_chat_messages_session_created "
                "ON chat_messages (session_id, created_at)"
            ))
        conn.commit()
    print("Indexes ensured.")


if __name__ == "__main__":
    upgrade()
    print("Migration 001 complete.")
