from app import app, db
from sqlalchemy import text, inspect

def fix_schema():
    with app.app_context():
        print("Starting schema fix...")
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        
        # 1. Fix SyllabusDocument (is_active)
        if 'syllabus_document' in tables:
            cols = [c['name'] for c in inspector.get_columns('syllabus_document')]
            if 'is_active' not in cols:
                print("Adding is_active column to syllabus_document...")
                with db.engine.connect() as conn:
                    # Use standard SQL boolean default (1/TRUE)
                    conn.execute(text("ALTER TABLE syllabus_document ADD COLUMN is_active BOOLEAN DEFAULT TRUE"))
                    conn.commit()
                print("Done adding is_active.")
            else:
                print("syllabus_document.is_active already exists.")
        
        # 2. Fix Todo (syllabus_id)
        if 'todo' in tables:
            cols = [c['name'] for c in inspector.get_columns('todo')]
            if 'syllabus_id' not in cols:
                print("Adding syllabus_id column to todo...")
                with db.engine.connect() as conn:
                    # Add column first
                    conn.execute(text("ALTER TABLE todo ADD COLUMN syllabus_id INTEGER"))
                    
                    # Try adding foreign key constraint, handle if syllabus_document doesn't exist or other issues
                    try:
                         print("Adding FK constraint...")
                         conn.execute(text("ALTER TABLE todo ADD CONSTRAINT fk_todo_syllabus FOREIGN KEY (syllabus_id) REFERENCES syllabus_document(id)"))
                    except Exception as e:
                        print(f"Warning: Could not add FK constraint (maybe sqlite?): {e}")
                    
                    conn.commit()
                print("Done adding syllabus_id.")
            else:
                print("todo.syllabus_id already exists.")

        # 3. Fix User (is_public_profile, last_seen)
        if 'user' in tables:
            cols = [c['name'] for c in inspector.get_columns('user')]
            with db.engine.connect() as conn:
                if 'is_public_profile' not in cols:
                    print("Adding is_public_profile to user...")
                    conn.execute(text("ALTER TABLE user ADD COLUMN is_public_profile BOOLEAN DEFAULT 1"))
                    conn.commit()
                if 'last_seen' not in cols:
                    print("Adding last_seen to user...")
                    try:
                        conn.execute(text("ALTER TABLE user ADD COLUMN last_seen DATETIME"))
                        conn.commit()
                    except Exception as e:
                         print(f"Could not add last_seen: {e}")

        # 4. Create any missing tables (Friendship, TopicProficiency, etc.)
        db.create_all()
        print("Ensured all tables exist.")

        print("Schema fix completed.")

if __name__ == "__main__":
    fix_schema()
