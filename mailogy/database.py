from collections import Counter
from pathlib import Path
import sqlite3
from mailogy.utils import mailogy_dir

class Database:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self._setup_db()

    def _setup_db(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                timestamp TEXT,
                from_email TEXT,
                from_name TEXT,
                to_email TEXT,
                to_name TEXT,
                subject TEXT,
                content TEXT,
                links TEXT,
                attachments TEXT,
                source TEXT,
                message_index INTEGER
            );
        """)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.conn.close()

    def insert(self, records):
        try:
            with self.conn:
                self.conn.executemany("""
                    INSERT INTO messages (
                        id,
                        timestamp,
                        from_email,
                        from_name,
                        to_email,
                        to_name,
                        subject,
                        content,
                        links,
                        attachments,
                        source,
                        message_index
                    ) VALUES (
                        :id,
                        :timestamp,
                        :from_email,
                        :from_name,
                        :to_email,
                        :to_name,
                        :subject,
                        :content,
                        :links,
                        :attachments,
                        :source,
                        :message_index
                    ) ON CONFLICT(id) DO UPDATE SET
                        timestamp = excluded.timestamp,
                        from_email = excluded.from_email,
                        from_name = excluded.from_name,
                        to_email = excluded.to_email,
                        to_name = excluded.to_name,
                        subject = excluded.subject,
                        content = excluded.content,
                        links = excluded.links,
                        attachments = excluded.attachments,
                        source = excluded.source,
                        message_index = excluded.message_index;
                """, records)
        except sqlite3.Error as e:
            print(f"An error occurred: {e}")

    def schema(self):
        try:
            with self.conn:
                return [row[1] for row in self.conn.execute("PRAGMA table_info(messages);")]
        except sqlite3.Error as e:
            print(f"An error occurred: {e}")
            return []

    def summary(self):
        try:
            with self.conn:
                message_count = self.conn.execute("SELECT COUNT(*) FROM messages;").fetchone()[0]
                email_counter_query = """
                    SELECT from_email FROM messages
                    UNION ALL
                    SELECT to_email FROM messages;
                """
                all_emails = self.conn.execute(email_counter_query).fetchall()
                email_counts = Counter(email for email, in all_emails)
                return {
                    "message_count": message_count,
                    "email_counts": email_counts,
                    "top_5": email_counts.most_common(5),
                }
        except sqlite3.Error as e:
            print(f"An error occurred: {e}")
            return {}

# Singleton management
_db_instance = None
_db_path = mailogy_dir / "messages.db"
def get_db():
    global _db_instance
    if _db_instance is None:
        _db_instance = Database(_db_path)
    return _db_instance