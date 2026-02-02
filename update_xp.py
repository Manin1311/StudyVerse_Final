from app import app, db, User, GamificationService

def update_xp():
    with app.app_context():
        print("--- Starting XP and Rank Update ---")

        # 1. Update Daksh's XP
        # Search for 'daksh' (case-insensitive)
        target_name = 'daksh'
        # searching specifically for 'Daksh' or 'daksh' if ilike is tricky in some envs, but ilike is standard.
        # Let's try to match it robustly.
        users_found = User.query.filter(User.first_name.ilike(target_name)).all()
        
        if not users_found:
            print(f"Warning: User with first_name '{target_name}' not found.")
        else:
            for user in users_found:
                print(f"Found user: {user.first_name} {user.last_name} (ID: {user.id})")
                print(f"  Current XP: {user.total_xp}, Level: {user.level}")
                
                # Set XP to 100,000
                user.total_xp = 100000
                print(f"  > Setting XP to 100,000")

        # 2. Recalculate Levels for ALL users
        print("\n--- Recalculating Levels for All Users ---")
        all_users = User.query.all()
        updated_count = 0
        
        for u in all_users:
            old_level = u.level
            # Calculate correct level based on total_xp
            # Using the static method from GamificationService as defined in app.py
            correct_level = GamificationService.calculate_level(u.total_xp)
            
            if u.level != correct_level:
                u.level = correct_level
                print(f"User {u.first_name} (ID: {u.id}): Level adjusted {old_level} -> {correct_level} (XP: {u.total_xp})")
                updated_count += 1
            
            # Since rank is derived from level dynamically in this app (not stored in DB),
            # updating the level effectively "fixes" the rank for display.

        db.session.commit()
        print(f"\n--- Update Complete ---")
        print(f"Total users level-corrected: {updated_count}")

if __name__ == "__main__":
    update_xp()
