from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from app.core.models import Book, Category, BorrowRecord, User, Admin
from app.core.forms import BookForm, CategoryForm, BorrowForm
from app import db
from sqlalchemy import case

core_bp = Blueprint('core', __name__)

@core_bp.route('/')
def index():
    if current_user.is_authenticated:
        if isinstance(current_user, Admin):
            # Get library statistics
            total_books = Book.query.count()
            total_users = User.query.count()
            total_borrows = BorrowRecord.query.count()
            active_borrows = BorrowRecord.query.filter_by(status='borrowed').count()

            # Get overdue books
            overdue_borrows = BorrowRecord.query.filter(
                BorrowRecord.status == 'borrowed',
                BorrowRecord.due_date < datetime.utcnow()
            ).count()

            # Get recent borrows
            recent_borrows = BorrowRecord.query.order_by(
                BorrowRecord.borrowed_at.desc()
            ).limit(5).all()

            return render_template('admin/dashboard.html',
                                total_books=total_books,
                                total_users=total_users,
                                total_borrows=total_borrows,
                                active_borrows=active_borrows,
                                overdue_borrows=overdue_borrows,
                                recent_borrows=recent_borrows)
        return redirect(url_for('core.dashboard'))
    return render_template('core/index.html')

@core_bp.route('/dashboard')
@login_required
def dashboard():
    if isinstance(current_user, Admin):
        return redirect(url_for('admin.dashboard'))
    
    # Get user's current borrows
    current_borrows = BorrowRecord.query.filter_by(
        user_id=current_user.id,
        status='borrowed'
    ).all()
    
    # Update status of all current borrows
    for borrow in current_borrows:
        borrow.update_status()
    db.session.commit()
    
    # Get user's borrow history
    borrow_history = BorrowRecord.query.filter_by(
        user_id=current_user.id,
        status='returned'
    ).order_by(BorrowRecord.returned_at.desc()).limit(5).all()
    
    # Get books due soon (within next 7 days)
    due_soon = BorrowRecord.query.filter(
        BorrowRecord.user_id == current_user.id,
        BorrowRecord.status == 'borrowed',
        BorrowRecord.due_date <= datetime.now() + timedelta(days=7)
    ).count()
    
    # Get total number of books borrowed historically
    total_borrowed = BorrowRecord.query.filter_by(
        user_id=current_user.id
    ).count()
    
    return render_template('core/dashboard.html',
                         current_borrows=current_borrows,
                         borrow_history=borrow_history,
                         due_soon=due_soon,
                         total_borrowed=total_borrowed)

@core_bp.route('/catalog')
def catalog():
    page = request.args.get('page', 1, type=int)
    per_page = 12
    
    # Get filter parameters
    category_id = request.args.get('category', type=int)
    search_query = request.args.get('search', '').strip()
    sort_by = request.args.get('sort', 'relevance' if search_query else 'title')
    order = request.args.get('order', 'asc')
    
    # Define sort options with consistent labels
    sort_options = [
        {'value': 'title', 'label': 'Title', 'show_if_search': True},
        {'value': 'author', 'label': 'Author', 'show_if_search': True},
        {'value': 'date_added', 'label': 'Date Added', 'show_if_search': True},
        {'value': 'availability', 'label': 'Availability', 'show_if_search': True},
        {'value': 'publisher', 'label': 'Publisher', 'show_if_search': True},
        {'value': 'year', 'label': 'Publication Year', 'show_if_search': True},
        {'value': 'relevance', 'label': 'Relevance', 'show_if_search': False}  # Only show for search
    ]
    
    # Validate sort_by parameter
    valid_sort_values = [opt['value'] for opt in sort_options]
    if sort_by not in valid_sort_values:
        sort_by = 'title'  # Default to title if invalid
    
    # Base query
    query = Book.query
    
    # Apply category filter
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    # Apply search filter with improved relevance
    search_filters = []
    if search_query:
        # Split search query into terms but keep quoted phrases together
        import re
        terms = []
        # Match quoted phrases first
        quoted = re.findall(r'"([^"]*)"', search_query)
        # Remove quoted phrases from the query
        remaining = re.sub(r'"[^"]*"', '', search_query)
        # Add quoted phrases as exact terms
        terms.extend(quoted)
        # Add remaining individual words
        terms.extend(word for word in remaining.split() if word)
        
        # Join with Category for category name search
        query = query.join(Category)
        
        # Create term filters
        for term in terms:
            term_filters = []
            # Exact matches (higher weight)
            term_filters.extend([
                Book.title.ilike(f"{term}"),  # Exact title match
                Book.author.ilike(f"{term}"),  # Exact author match
                Book.isbn == term,  # Exact ISBN match
            ])
            # Partial matches (lower weight)
            term_filters.extend([
                Book.title.ilike(f"%{term}%"),
                Book.author.ilike(f"%{term}%"),
                Book.isbn.ilike(f"%{term}%"),
                Book.description.ilike(f"%{term}%"),
                Book.publisher.ilike(f"%{term}%"),
                Category.name.ilike(f"%{term}%")
            ])
            search_filters.append(db.or_(*term_filters))
    
    # Apply search filters
    if search_filters:
        query = query.filter(db.and_(*search_filters))
    
    # Apply sorting with improved options
    if sort_by == 'relevance' and search_query:
        # Custom relevance scoring with fixed case syntax
        relevance_score = (
            case(
                (Book.title.ilike(search_query), 100),
                (Book.author.ilike(search_query), 90),
                (Book.isbn == search_query, 80),
                (Book.title.ilike(f"%{search_query}%"), 70),
                (Book.author.ilike(f"%{search_query}%"), 60),
                (Book.isbn.ilike(f"%{search_query}%"), 50),
                (Book.description.ilike(f"%{search_query}%"), 40),
                (Book.publisher.ilike(f"%{search_query}%"), 30),
                (Category.name.ilike(f"%{search_query}%"), 20),
                else_=0
            )
        )
        query = query.order_by(relevance_score.desc())
    else:
        # Standard sorting options with complete mapping
        sort_column = {
            'title': Book.title,
            'author': Book.author,
            'date_added': Book.added_at,
            'availability': Book.available_quantity,
            'publisher': Book.publisher,
            'year': Book.publication_year
        }.get(sort_by)
        
        if sort_column:  # Only apply sort if we have a valid column
            if order == 'desc':
                sort_column = sort_column.desc()
            query = query.order_by(sort_column)
            
            # Add secondary sort by title for consistency
            if sort_by != 'title':
                query = query.order_by(Book.title.asc())
        else:
            # Default to title if no valid sort column found
            query = query.order_by(Book.title.asc())
    
    # Execute query with pagination
    try:
        books = query.paginate(page=page, per_page=per_page, error_out=False)
        
        # If no results and multiple terms, try OR logic
        if not books.items and len(terms) > 1:
            query = Book.query.join(Category)
            if category_id:
                query = query.filter_by(category_id=category_id)
            
            # Create OR filters
            or_filters = []
            for term in terms:
                term_filter = db.or_(
                    Book.title.ilike(f"%{term}%"),
                    Book.author.ilike(f"%{term}%"),
                    Book.isbn.ilike(f"%{term}%"),
                    Book.description.ilike(f"%{term}%"),
                    Book.publisher.ilike(f"%{term}%"),
                    Category.name.ilike(f"%{term}%")
                )
                or_filters.append(term_filter)
            
            query = query.filter(db.or_(*or_filters))
            if sort_by == 'relevance':
                query = query.order_by(Book.title.asc())
            books = query.paginate(page=page, per_page=per_page, error_out=False)
    except Exception as e:
        print(f"Search error: {str(e)}")
        books = Book.query.paginate(page=page, per_page=per_page, error_out=False)
    
    # Get all categories for the filter dropdown
    categories = Category.query.order_by(Category.name).all()
    
    # Count total results
    total_results = books.total
    
    return render_template('core/catalog.html',
                         books=books,
                         categories=categories,
                         search_query=search_query,
                         current_sort=sort_by,
                         current_order=order,
                         sort_options=sort_options,
                         total_results=total_results)

@core_bp.route('/book/<int:book_id>')
def book_detail(book_id):
    book = Book.query.get_or_404(book_id)
    form = BorrowForm()
    return render_template('core/book_detail.html', book=book, form=form)

@core_bp.route('/borrow/<int:book_id>', methods=['POST'])
@login_required
def borrow_book(book_id):
    if isinstance(current_user, Admin):
        return jsonify({'status': 'error', 'message': 'Admins cannot borrow books'}), 403
    
    book = Book.query.get_or_404(book_id)
    form = BorrowForm()
    
    if not book.is_available:
        flash('This book is currently unavailable', 'error')
        return redirect(url_for('core.book_detail', book_id=book_id))
    
    if form.validate_on_submit():
        # Check if user already has this book
        existing_borrow = BorrowRecord.query.filter_by(
            user_id=current_user.id,
            book_id=book_id,
            status='borrowed'
        ).first()
        
        if existing_borrow:
            flash('You already have this book borrowed', 'error')
            return redirect(url_for('core.book_detail', book_id=book_id))
        
        # Create new borrow record
        borrow = BorrowRecord(
            user_id=current_user.id,
            book_id=book_id,
            borrowed_at=datetime.utcnow(),
            due_date=form.due_date.data
        )
        
        # Update book availability
        book.available_quantity -= 1
        
        db.session.add(borrow)
        try:
            db.session.commit()
            flash('Book borrowed successfully', 'success')
            return redirect(url_for('core.dashboard'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while borrowing the book', 'error')
    
    return redirect(url_for('core.book_detail', book_id=book_id))

@core_bp.route('/return/<int:borrow_id>', methods=['POST'])
@login_required
def return_book(borrow_id):
    if isinstance(current_user, Admin):
        return jsonify({'status': 'error', 'message': 'Admins cannot return books'}), 403
    
    borrow = BorrowRecord.query.get_or_404(borrow_id)
    
    # Verify the borrow record belongs to the current user
    if borrow.user_id != current_user.id:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403
    
    # Mark the book as returned
    borrow.mark_as_returned()
    
    # Increment the available quantity
    book = Book.query.get(borrow.book_id)
    book.available_quantity += 1
    
    try:
        db.session.commit()
        flash('Book returned successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while returning the book', 'error')
    
    return redirect(url_for('core.dashboard'))

@core_bp.route('/my-books')
@login_required
def my_books():
    # Get current borrows
    current_borrows = BorrowRecord.query.filter_by(
        user_id=current_user.id,
        status='borrowed'
    ).order_by(BorrowRecord.borrowed_at.desc()).all()
    
    # Update status of all current borrows
    for borrow in current_borrows:
        borrow.update_status()
    db.session.commit()
    
    # Get borrow history
    borrow_history = BorrowRecord.query.filter_by(
        user_id=current_user.id,
        status='returned'
    ).order_by(BorrowRecord.borrowed_at.desc()).all()
    
    return render_template('core/my_books.html',
                         current_borrows=current_borrows,
                         borrow_history=borrow_history)

@core_bp.route('/search/suggestions')
def search_suggestions():
    query = request.args.get('q', '').strip()
    if not query or len(query) < 2:
        return jsonify([])
    
    try:
        # Search across multiple fields
        suggestions = []
        
        # Search in titles
        title_results = Book.query.filter(
            Book.title.ilike(f'%{query}%')
        ).limit(5).all()
        for book in title_results:
            suggestions.append({
                'type': 'title',
                'text': book.title,
                'id': book.id,
                'icon': 'book',
                'url': url_for('core.book_detail', book_id=book.id)
            })
        
        # Search in authors
        author_results = db.session.query(Book.author).filter(
            Book.author.ilike(f'%{query}%')
        ).distinct().limit(3).all()
        for author in author_results:
            suggestions.append({
                'type': 'author',
                'text': f'Author: {author[0]}',
                'query': author[0],
                'icon': 'user',
                'url': url_for('core.catalog', search=author[0])
            })
        
        # Search in categories
        category_results = Category.query.filter(
            Category.name.ilike(f'%{query}%')
        ).limit(3).all()
        for category in category_results:
            suggestions.append({
                'type': 'category',
                'text': f'Category: {category.name}',
                'id': category.id,
                'icon': 'tag',
                'url': url_for('core.catalog', category=category.id)
            })
        
        # Search in ISBN
        isbn_results = Book.query.filter(
            Book.isbn.ilike(f'%{query}%')
        ).limit(2).all()
        for book in isbn_results:
            suggestions.append({
                'type': 'isbn',
                'text': f'ISBN: {book.isbn}',
                'id': book.id,
                'icon': 'barcode',
                'url': url_for('core.book_detail', book_id=book.id)
            })
        
        return jsonify(suggestions)
    except Exception as e:
        print(f"Error in search suggestions: {str(e)}")
        return jsonify([])
