from app import create_app, db
from app.core.models import Book

def update_cover_urls():
    """Update all HTTP book cover URLs to HTTPS"""
    app = create_app()
    with app.app_context():
        # Get all books with HTTP cover images
        books = Book.query.filter(Book.cover_image.like('http:%')).all()
        
        updated_count = 0
        for book in books:
            if book.cover_image and book.cover_image.startswith('http:'):
                book.cover_image = 'https:' + book.cover_image[5:]
                updated_count += 1
        
        if updated_count > 0:
            db.session.commit()
            print(f"Successfully updated {updated_count} book cover URLs from HTTP to HTTPS")
        else:
            print("No HTTP book cover URLs found that need updating")

if __name__ == '__main__':
    update_cover_urls()
