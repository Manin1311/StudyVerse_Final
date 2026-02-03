
import os
from app import app, db
from sqlalchemy import text

# This script runs within the Flask app context to ensure valid DB connection (PostgreSQL/SQLite)
def update_schema():
    print("Connecting to database...")
    with app.app_context():
        try:
            # Check if columns exist using SQLAlchemy introspection logic (or direct SQL for speed)
            # This is robust for PostgreSQL
            with db.engine.connect() as conn:
                # Add due_time
                try:
                    conn.execute(text("ALTER TABLE todo ADD COLUMN due_time VARCHAR(20)"))
                    print("Added column: due_time")
                except Exception as e:
                    print(f"Column 'due_time' might already exist or error: {e}")
                
                # Add is_notified
                try:
                    conn.execute(text("ALTER TABLE todo ADD COLUMN is_notified BOOLEAN DEFAULT FALSE"))
                    print("Added column: is_notified")
                except Exception as e:
                    print(f"Column 'is_notified' might already exist or error: {e}")
                    
                conn.commit()
                print("Schema update completed successfully.")
                
        except Exception as e:
            print(f"Database error: {e}")

if __name__ == "__main__":
    update_schema()
