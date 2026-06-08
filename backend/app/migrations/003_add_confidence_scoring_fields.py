"""Migration: Add detailed confidence scoring fields to ChatLog."""

import logging
import sqlite3
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# This migration adds vector_score, reranker_score, and confidence_reason to ChatLog
# for better debugging and analytics.

DB_PATH = Path(__file__).parent.parent.parent / "rag_backend.db"


def upgrade():
    """Add new columns to chat_logs table."""
    if not DB_PATH.exists():
        logger.info(f"Database not found at {DB_PATH}, skipping migration")
        return

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    try:
        # Check if columns already exist (idempotent)
        cursor.execute("PRAGMA table_info(chat_logs)")
        columns = {row[1] for row in cursor.fetchall()}

        if "vector_score" not in columns:
            cursor.execute("ALTER TABLE chat_logs ADD COLUMN vector_score FLOAT NULL")
            logger.info("Added vector_score column")

        if "reranker_score" not in columns:
            cursor.execute("ALTER TABLE chat_logs ADD COLUMN reranker_score FLOAT NULL")
            logger.info("Added reranker_score column")

        if "confidence_reason" not in columns:
            cursor.execute("ALTER TABLE chat_logs ADD COLUMN confidence_reason VARCHAR(80) NULL")
            logger.info("Added confidence_reason column")

        # Add index on confidence for analytics queries
        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS ix_chat_logs_confidence ON chat_logs(confidence)")
            logger.info("Created index on confidence column")
        except sqlite3.OperationalError as e:
            logger.debug(f"Index creation: {e}")

        # Add index on created_at for time-based queries
        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS ix_chat_logs_created ON chat_logs(created_at)")
            logger.info("Created index on created_at column")
        except sqlite3.OperationalError as e:
            logger.debug(f"Index creation: {e}")

        conn.commit()
        logger.info("Migration completed successfully")

    except sqlite3.OperationalError as e:
        logger.error(f"Migration error: {e}")
        raise
    finally:
        conn.close()


def downgrade():
    """Rollback migration (columns kept for safety, indices dropped)."""
    if not DB_PATH.exists():
        logger.info(f"Database not found at {DB_PATH}, skipping downgrade")
        return

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    try:
        cursor.execute("DROP INDEX IF EXISTS ix_chat_logs_confidence")
        cursor.execute("DROP INDEX IF EXISTS ix_chat_logs_created")
        logger.info("Dropped indices")
        conn.commit()
    except sqlite3.OperationalError as e:
        logger.warning(f"Index drop warning: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    logger.info(f"Running migration: add_confidence_scoring_fields (DB: {DB_PATH})")
    upgrade()
