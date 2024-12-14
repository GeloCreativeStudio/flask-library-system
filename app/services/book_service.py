import requests
from typing import Optional, Dict, List
from app import db
from app.core.models import Category

class GoogleBooksService:
    BASE_URL = "https://www.googleapis.com/books/v1/volumes"

    @staticmethod
    def get_high_quality_cover_url(cover_url: str) -> Optional[str]:
        """Convert a Google Books thumbnail URL to its high-quality version"""
        if not cover_url:
            return None
        
        # Convert HTTP to HTTPS if needed
        if cover_url.startswith('http:'):
            cover_url = 'https:' + cover_url[5:]
        
        # Remove zoom and size parameters to get the high-quality version
        base_url = cover_url.split('&zoom=')[0] if '&zoom=' in cover_url else cover_url
        base_url = base_url.split('&img=')[0] if '&img=' in base_url else base_url
        base_url = base_url.split('&edge=')[0] if '&edge=' in base_url else base_url
        
        # Ensure we're getting the frontcover
        if 'printsec=frontcover' not in base_url:
            base_url += '&printsec=frontcover'
        
        # Add high-quality parameters
        if '?' not in base_url:
            base_url += '?'
        if 'zoom=' not in base_url:
            base_url += '&zoom=1'  # 1 for highest quality
        if 'img=1' not in base_url:
            base_url += '&img=1'  # 1 for full image
        
        return base_url

    @staticmethod
    def search_books(query: str) -> List[Dict]:
        """
        Search for books using the Google Books API
        """
        try:
            response = requests.get(
                GoogleBooksService.BASE_URL,
                params={
                    'q': query,
                    'maxResults': 5,
                    'printType': 'books'
                }
            )
            response.raise_for_status()
            data = response.json()
            
            books = []
            for item in data.get('items', []):
                volume_info = item.get('volumeInfo', {})
                categories = volume_info.get('categories', [])
                main_category = categories[0] if categories else 'Uncategorized'
                
                # Get cover image URL
                image_links = volume_info.get('imageLinks', {})
                cover_image = (image_links.get('thumbnail') or 
                             image_links.get('smallThumbnail'))
                
                # Convert to high-quality version
                cover_image = GoogleBooksService.get_high_quality_cover_url(cover_image)
                
                books.append({
                    'title': volume_info.get('title', ''),
                    'author': ', '.join(volume_info.get('authors', [])),
                    'isbn': next((identifier['identifier'] for identifier in volume_info.get('industryIdentifiers', []) 
                                if identifier['type'] in ['ISBN_13', 'ISBN_10']), ''),
                    'publisher': volume_info.get('publisher', ''),
                    'published_date': volume_info.get('publishedDate', ''),
                    'description': volume_info.get('description', ''),
                    'category': main_category,
                    'cover_image': cover_image
                })
            return books
        except requests.RequestException as e:
            print(f"Error fetching books: {e}")
            return []

    @staticmethod
    def get_book_by_isbn(isbn: str) -> Optional[Dict]:
        """
        Get a specific book by ISBN
        """
        try:
            response = requests.get(
                GoogleBooksService.BASE_URL,
                params={
                    'q': f'isbn:{isbn}',
                    'maxResults': 1
                }
            )
            response.raise_for_status()
            data = response.json()
            
            if not data.get('items'):
                return None
                
            volume_info = data['items'][0]['volumeInfo']
            categories = volume_info.get('categories', [])
            main_category = categories[0] if categories else 'Uncategorized'
            
            # Get cover image URL
            image_links = volume_info.get('imageLinks', {})
            cover_image = (image_links.get('thumbnail') or 
                         image_links.get('smallThumbnail'))
            
            # Convert to high-quality version
            cover_image = GoogleBooksService.get_high_quality_cover_url(cover_image)
            
            return {
                'title': volume_info.get('title', ''),
                'author': ', '.join(volume_info.get('authors', [])),
                'isbn': isbn,
                'publisher': volume_info.get('publisher', ''),
                'published_date': volume_info.get('publishedDate', ''),
                'description': volume_info.get('description', ''),
                'category': main_category,
                'cover_image': cover_image
            }
        except requests.RequestException as e:
            print(f"Error fetching book: {e}")
            return None

    @staticmethod
    def get_or_create_category(category_name: str) -> Category:
        """
        Get existing category or create a new one
        """
        category = Category.query.filter(Category.name.ilike(category_name)).first()
        if not category:
            category = Category(
                name=category_name,
                description=f'Category automatically created from Google Books API'
            )
            db.session.add(category)
            db.session.commit()
        return category
