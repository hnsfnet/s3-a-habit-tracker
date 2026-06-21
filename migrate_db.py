import sqlite3
import os

db_path = "habit_tracker.db"

if not os.path.exists(db_path):
    print("Database not found, no migration needed.")
    exit(0)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='habit_logs'")
    if cursor.fetchone():
        cursor.execute("PRAGMA table_info(habit_logs)")
        columns = [col[1] for col in cursor.fetchall()]
        if 'note' not in columns:
            print("Adding 'note' column to habit_logs...")
            cursor.execute("ALTER TABLE habit_logs ADD COLUMN note TEXT DEFAULT ''")
            print("Done.")
        else:
            print("'note' column already exists.")

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='challenges'")
    if not cursor.fetchone():
        print("Creating 'challenges' table...")
        cursor.execute("""
            CREATE TABLE challenges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                habit_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                name VARCHAR NOT NULL,
                target_days INTEGER NOT NULL,
                start_date DATE NOT NULL,
                end_date DATE NOT NULL,
                is_completed BOOLEAN DEFAULT 0,
                completed_date DATE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (habit_id) REFERENCES habits (id),
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        print("Done.")
    else:
        print("'challenges' table already exists.")

    conn.commit()
    print("\nMigration completed successfully!")

except Exception as e:
    print(f"Error during migration: {e}")
    conn.rollback()
finally:
    conn.close()
