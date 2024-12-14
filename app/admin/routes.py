from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from app.core.forms import BookForm, CategoryForm, AdminLoginForm
from app.core.models import Book, Category, BorrowRecord, User, Admin
from app import db
from datetime import datetime, timedelta
from app.services.book_service import GoogleBooksService
from app.utils.image_handler import save_image_from_url, delete_book_image
import requests

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not isinstance(current_user, Admin):
            flash('Access denied.', 'error')
            return redirect(url_for('admin.login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if isinstance(current_user, Admin):
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('core.dashboard'))

    form = AdminLoginForm()
    if form.validate_on_submit():
        admin = Admin.query.filter_by(username=form.username.data).first()
        if admin and admin.check_password(form.password.data):
            login_user(admin)
            return redirect(url_for('admin.dashboard'))
        flash('Invalid username or password', 'error')
    
    return render_template('admin/login.html', form=form)

@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    # Get total counts
    total_books = Book.query.count()
    total_users = User.query.count()
    active_borrows = BorrowRecord.query.filter_by(status='borrowed').count()
    overdue_borrows = BorrowRecord.query.filter(
        BorrowRecord.status == 'borrowed',
        BorrowRecord.due_date < datetime.utcnow()
    ).count()

    # Get category statistics
    categories = Category.query.all()
    category_stats = []
    for category in categories:
        total_books = Book.query.filter_by(category_id=category.id).count()
        borrowed_books = db.session.query(Book).join(BorrowRecord).filter(
            Book.category_id == category.id,
            BorrowRecord.status == 'borrowed'
        ).count()
        category_stats.append({
            'category': category,
            'total_books': total_books,
            'borrowed': borrowed_books
        })

    return render_template('admin/dashboard.html',
                         total_books=total_books,
                         total_users=total_users,
                         active_borrows=active_borrows,
                         overdue_borrows=overdue_borrows,
                         category_stats=category_stats)

@admin_bp.route('/books')
@login_required
@admin_required
def books():
    books = Book.query.all()
    form = BookForm()
    return render_template('admin/books.html', books=books, form=form)

@admin_bp.route('/books/add', methods=['POST'])
@login_required
@admin_required
def books_add():
    form = BookForm()
    
    if form.validate_on_submit():
        try:
            # Get book details from Google Books API if ISBN is provided
            book_details = None
            cover_image_path = None
            category = None
            
            if form.isbn.data:
                book_details = GoogleBooksService.get_book_by_isbn(form.isbn.data)
                if book_details:
                    if book_details.get('cover_image'):
                        # Download and save the cover image
                        cover_image_url = GoogleBooksService.get_high_quality_cover_url(book_details['cover_image'])
                        cover_image_path = save_image_from_url(cover_image_url, form.isbn.data)
                    
                    # Get or create category from API data
                    if book_details.get('category'):
                        category = GoogleBooksService.get_or_create_category(book_details['category'])
            
            # If no category from API, use default category
            if not category:
                category = Category.query.filter_by(name='Uncategorized').first()
                if not category:
                    category = Category(name='Uncategorized', description='Default category for books')
                    db.session.add(category)
                    db.session.commit()
            
            # Create new book with form data, using API data as fallback
            book = Book(
                isbn=form.isbn.data,
                local_id=Book.generate_local_id(),
                title=form.title.data,
                author=form.author.data,
                publisher=form.publisher.data or (book_details.get('publisher') if book_details else None),
                publication_year=form.publication_year.data or (int(book_details['published_date'][:4]) if book_details and book_details.get('published_date') else None),
                category_id=category.id,
                description=form.description.data or (book_details.get('description') if book_details else None),
                quantity=form.quantity.data,
                available_quantity=form.quantity.data,
                location=form.location.data,
                cover_image=cover_image_path
            )
            
            db.session.add(book)
            db.session.commit()
            flash('Book added successfully!', 'success')
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding book: {str(e)}', 'error')
            return redirect(url_for('admin.books'))
            
    return redirect(url_for('admin.books'))

@admin_bp.route('/books/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def books_edit(id):
    book = Book.query.get_or_404(id)
    form = BookForm()
    
    if request.method == 'GET':
        # Populate form with existing data
        form.isbn.data = book.isbn
        form.title.data = book.title
        form.author.data = book.author
        form.publisher.data = book.publisher
        form.publication_year.data = book.publication_year
        form.description.data = book.description
        form.quantity.data = book.quantity
        form.location.data = book.location
        
        return jsonify({
            'isbn': book.isbn,
            'title': book.title,
            'author': book.author,
            'publisher': book.publisher,
            'publication_year': book.publication_year,
            'description': book.description,
            'quantity': book.quantity,
            'location': book.location,
            'category': book.category.name
        })
    
    if form.validate_on_submit():
        try:
            # Update book details
            book.isbn = form.isbn.data
            book.title = form.title.data
            book.author = form.author.data
            book.publisher = form.publisher.data
            book.publication_year = form.publication_year.data
            book.description = form.description.data
            book.quantity = form.quantity.data
            book.location = form.location.data
            
            # If ISBN changed, try to get new category from API
            if book.isbn != form.isbn.data and form.isbn.data:
                book_details = GoogleBooksService.get_book_by_isbn(form.isbn.data)
                if book_details and book_details.get('category'):
                    category = GoogleBooksService.get_or_create_category(book_details['category'])
                    book.category_id = category.id
            
            db.session.commit()
            flash('Book updated successfully!', 'success')
            return jsonify({'success': True})
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)}), 400
            
    return jsonify({'success': False, 'errors': form.errors}), 400

@admin_bp.route('/books/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def books_delete(id):
    book = Book.query.get_or_404(id)
    
    # Check if book is currently borrowed
    if BorrowRecord.query.filter_by(book_id=id, status='borrowed').first():
        return jsonify({
            'success': False, 
            'message': 'Cannot delete book while it is borrowed'
        }), 400
        
    try:
        # Delete the book's cover image if it exists
        if book.cover_image:
            delete_book_image(book.cover_image)
            
        db.session.delete(book)
        db.session.commit()
        return jsonify({
            'success': True, 
            'message': 'Book deleted successfully'
        })
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting book: {str(e)}")
        return jsonify({
            'success': False, 
            'message': f'Error deleting book: {str(e)}'
        }), 500

@admin_bp.route('/books/<int:id>/data')
@login_required
@admin_required
def get_book_data(id):
    book = Book.query.get_or_404(id)
    return jsonify({
        'isbn': book.isbn,
        'title': book.title,
        'author': book.author,
        'publisher': book.publisher,
        'publication_year': book.publication_year,
        'category_id': book.category_id,
        'description': book.description,
        'quantity': book.quantity,
        'location': book.location
    })

@admin_bp.route('/books/api/search')
@login_required
@admin_required
def search_books_api():
    query = request.args.get('query', '')
    if not query or len(query) < 2:
        return jsonify([])
    
    try:
        # Call Google Books API
        url = f'https://www.googleapis.com/books/v1/volumes?q={query}'
        response = requests.get(url)
        data = response.json()
        
        books = []
        if 'items' in data:
            for item in data['items']:
                volume_info = item.get('volumeInfo', {})
                isbn = ''
                # Try to get ISBN-13 first, then ISBN-10
                for identifier in volume_info.get('industryIdentifiers', []):
                    if identifier['type'] == 'ISBN_13':
                        isbn = identifier['identifier']
                        break
                    elif identifier['type'] == 'ISBN_10':
                        isbn = identifier['identifier']

                books.append({
                    'isbn': isbn,
                    'title': volume_info.get('title', ''),
                    'author': ', '.join(volume_info.get('authors', [])),
                    'publisher': volume_info.get('publisher', ''),
                    'publication_year': volume_info.get('publishedDate', '')[:4] if volume_info.get('publishedDate') else '',
                    'description': volume_info.get('description', ''),
                    'image_url': volume_info.get('imageLinks', {}).get('thumbnail', '')
                })
        
        return jsonify(books)
    except Exception as e:
        print(f"Error searching books: {str(e)}")
        return jsonify([])

@admin_bp.route('/books/api/details')
@login_required
@admin_required
def get_book_api_details():
    isbn = request.args.get('isbn', '')
    if not isbn:
        return jsonify(None)
    
    try:
        # Search by ISBN
        url = f'https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}'
        response = requests.get(url)
        data = response.json()
        
        if 'items' in data and len(data['items']) > 0:
            volume_info = data['items'][0].get('volumeInfo', {})
            return jsonify({
                'isbn': isbn,
                'title': volume_info.get('title', ''),
                'author': ', '.join(volume_info.get('authors', [])),
                'publisher': volume_info.get('publisher', ''),
                'publication_year': volume_info.get('publishedDate', '')[:4] if volume_info.get('publishedDate') else '',
                'description': volume_info.get('description', ''),
                'image_url': volume_info.get('imageLinks', {}).get('thumbnail', '')
            })
        
        return jsonify(None)
    except Exception as e:
        print(f"Error fetching book details: {str(e)}")
        return jsonify(None)

@admin_bp.route('/categories')
@login_required
@admin_required
def categories():
    categories = Category.query.all()
    form = CategoryForm()
    return render_template('admin/categories.html', categories=categories, form=form)

@admin_bp.route('/categories/add', methods=['POST'])
@login_required
@admin_required
def categories_add():
    form = CategoryForm()
    if form.validate_on_submit():
        category = Category(
            name=form.name.data,
            description=form.description.data
        )
        db.session.add(category)
        try:
            db.session.commit()
            flash('Category added successfully', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Error adding category', 'error')
    return redirect(url_for('admin.categories'))

@admin_bp.route('/categories/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def categories_edit(id):
    category = Category.query.get_or_404(id)
    form = CategoryForm(obj=category)
    
    if form.validate_on_submit():
        category.name = form.name.data
        category.description = form.description.data
        try:
            db.session.commit()
            flash('Category updated successfully', 'success')
            return redirect(url_for('admin.categories'))
        except Exception as e:
            db.session.rollback()
            flash('Error updating category', 'error')
    
    return render_template('admin/categories_edit.html', form=form, category=category)

@admin_bp.route('/categories/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def categories_delete(id):
    category = Category.query.get_or_404(id)
    
    # Check if there are any books in this category
    if Book.query.filter_by(category_id=category.id).first():
        return jsonify({
            'success': False,
            'message': 'Cannot delete category that contains books. Please remove or reassign all books first.'
        })
    
    try:
        db.session.delete(category)
        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'Category deleted successfully'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error deleting category: {str(e)}'
        })

@admin_bp.route('/users')
@login_required
@admin_required
def users():
    users = User.query.all()
    # Add active borrows count for each user
    for user in users:
        user.active_borrows_count = BorrowRecord.query.filter_by(
            user_id=user.id,
            status='borrowed'
        ).count()
    return render_template('admin/users.html', users=users)

@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    
    # First check if trying to delete an admin
    if isinstance(user, Admin):
        if current_user.id == user_id:
            flash('You cannot delete your own admin account.', 'danger')
        else:
            flash('Cannot delete other admin accounts.', 'danger')
        return redirect(url_for('admin.users'))
    
    # Check if user has active borrows
    active_borrows = BorrowRecord.query.filter_by(
        user_id=user.id,
        status='borrowed'
    ).count()
    
    if active_borrows > 0:
        flash('Cannot delete user with active borrows.', 'danger')
        return redirect(url_for('admin.users'))
    
    try:
        # Delete the user - cascade will handle borrow records
        db.session.delete(user)
        db.session.commit()
        flash(f'User {user.username} has been deleted successfully.', 'success')
        return redirect(url_for('admin.users'))
        
    except Exception as e:
        db.session.rollback()
        import traceback
        print(f"Error deleting user: {str(e)}")
        print("Traceback:")
        print(traceback.format_exc())
        flash('An error occurred while deleting the user. Please try again.', 'danger')
        return redirect(url_for('admin.users'))

@admin_bp.route('/borrows')
@login_required
@admin_required
def borrows():
    status_filter = request.args.get('status', 'all')
    show_overdue = request.args.get('overdue')
    
    query = BorrowRecord.query
    
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    if show_overdue:
        query = query.filter(BorrowRecord.status == 'overdue')
    
    borrows = query.all()
    return render_template('admin/borrows.html', borrows=borrows, datetime=datetime)

@admin_bp.route('/borrows/<int:borrow_id>/return', methods=['POST'])
@login_required
@admin_required
def return_borrow(borrow_id):
    borrow = BorrowRecord.query.get_or_404(borrow_id)
    if borrow.status != 'borrowed':
        return jsonify({'success': False, 'message': 'This book has already been returned'}), 400
    
    try:
        borrow.mark_as_returned()
        db.session.commit()
        return jsonify({'success': True, 'message': 'Book marked as returned successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/get_book_details')
@login_required
@admin_required
def get_book_details():
    isbn = request.args.get('isbn', '')
    if not isbn:
        return jsonify({})
    
    book_details = GoogleBooksService.get_book_by_isbn(isbn)
    if not book_details:
        return jsonify({})

    # Get or create the category
    category = GoogleBooksService.get_or_create_category(book_details['category'])
    
    # Add category ID to the response
    book_details['category_id'] = category.id
    return jsonify(book_details)
