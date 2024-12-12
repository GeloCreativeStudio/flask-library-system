from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from app.core.models import Book, Category, BorrowRecord, User, Admin
from app.core.forms import BookForm, CategoryForm, BorrowForm
from app import db

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
    search_query = request.args.get('q', '')
    
    # Base query
    query = Book.query
    
    # Apply filters
    if category_id:
        query = query.filter_by(category_id=category_id)
    if search_query:
        query = query.filter(
            db.or_(
                Book.title.ilike(f'%{search_query}%'),
                Book.author.ilike(f'%{search_query}%'),
                Book.isbn.ilike(f'%{search_query}%')
            )
        )
    
    # Get paginated results
    books = query.paginate(page=page, per_page=per_page, error_out=False)
    categories = Category.query.all()
    
    return render_template('core/catalog.html',
                         books=books,
                         categories=categories,
                         category_id=category_id,
                         search_query=search_query)

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
