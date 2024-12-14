from app import create_app, db
from app.core.models import Admin, User, Category, Book, BorrowRecord
import click
from flask.cli import with_appcontext

app = create_app()

@app.cli.command('init-db')
@with_appcontext
def init_db():
    """Clear existing data and create new tables."""
    # Drop all tables
    db.drop_all()
    # Create all tables
    db.create_all()
    # Create default admin
    Admin.create_default_admin()
    click.echo('Initialized the database.')

if __name__ == '__main__':
    app.run(debug=True)
