"""
Database migration script to add ActivePowerUp table
Run this once to add the new table without losing existing data
"""

from app import app, db, ActivePowerUp

def create_powerup_table():
    with app.app_context():
        # Create only the new table
        try:
            # Check if table exists
            inspector = db.inspect(db.engine)
            if 'active_power_up' not in inspector.get_table_names():
                print("Creating ActivePowerUp table...")
                ActivePowerUp.__table__.create(db.engine)
                print("✅ ActivePowerUp table created successfully!")
                print("\nPower-up system is now ready to use!")
            else:
                print("✅ ActivePowerUp table already exists!")
                print("Power-up system is ready!")
        except Exception as e:
            print(f"❌ Error creating table: {e}")
            print("\nTrying alternative method...")
            try:
                db.create_all()
                print("✅ All tables created/updated successfully!")
            except Exception as e2:
                print(f"❌ Error: {e2}")

if __name__ == "__main__":
    create_powerup_table()
