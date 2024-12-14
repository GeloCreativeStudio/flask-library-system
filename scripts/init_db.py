from app import create_app, db
from app.core.models import Admin

def init_db():
    """Initialize the database with proper schema"""
    app = create_app()
    with app.app_context():
        # Drop all tables
        db.drop_all()
        # Create all tables
        db.create_all()
        # Create default admin
        Admin.create_default_admin()
        print("Database initialized successfully!")

if __name__ == '__main__':
    init_db()
