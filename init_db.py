from app import app, db, User, Favorite  # Import Favorite model

# Run inside application context
with app.app_context():
    db.create_all()
    print("Database initialized successfully!")

    # Check if users exist
    users = User.query.all()
    for user in users:
        print(user.id, user.name, user.email)

    # ✅ Fix: Query Favorites within context
    favorites = Favorite.query.all()
    print("Saved Favorites:", favorites)  # Debugging
