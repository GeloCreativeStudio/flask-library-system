from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from app.core.forms import BookForm, CategoryForm, AdminLoginForm
from app.core.models import Book, Category, BorrowRecord, User, Admin
from app import db
from datetime import datetime, timedelta

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
    # Redirect to home page which now serves as dashboard
    return redirect(url_for('core.index'))

@admin_bp.route('/books')
@login_required
@admin_required
def books():
    books = Book.query.all()
    form = BookForm()
    form.category.choices = [(c.id, c.name) for c in Category.query.all()]
    return render_template('admin/books.html', books=books, form=form)

@admin_bp.route('/books/add', methods=['POST'])
@login_required
@admin_required
def books_add():
    form = BookForm()
    form.category.choices = [(c.id, c.name) for c in Category.query.all()]
    
    if form.validate_on_submit():
        try:
            book = Book(
                isbn=form.isbn.data,
                title=form.title.data,
                author=form.author.data,
                publisher=form.publisher.data,
                publication_year=form.publication_year.data,
                category_id=form.category.data,
                description=form.description.data,
                quantity=form.quantity.data,
                available_quantity=form.quantity.data,
                location=form.location.data
            )
            db.session.add(book)
            db.session.commit()
            flash('Book added successfully', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding book: {str(e)}', 'error')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{getattr(form, field).label.text}: {error}', 'error')
    
    return redirect(url_for('admin.books'))

@admin_bp.route('/books/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def books_edit(id):
    book = Book.query.get_or_404(id)
    form = BookForm(obj=book)
    form.category.choices = [(c.id, c.name) for c in Category.query.all()]
    
    if form.validate_on_submit():
        book.isbn = form.isbn.data
        book.title = form.title.data
        book.author = form.author.data
        book.publisher = form.publisher.data
        book.publication_year = form.publication_year.data
        book.category_id = form.category.data
        book.description = form.description.data
        # Calculate the change in quantity and update available_quantity accordingly
        quantity_change = form.quantity.data - book.quantity
        book.quantity = form.quantity.data
        book.available_quantity = max(0, book.available_quantity + quantity_change)
        book.location = form.location.data
        
        try:
            db.session.commit()
            flash('Book updated successfully', 'success')
            return redirect(url_for('admin.books'))
        except Exception as e:
            db.session.rollback()
            flash('Error updating book', 'error')
    
    return render_template('admin/books_edit.html', form=form, book=book)

@admin_bp.route('/books/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def books_delete(id):
    book = Book.query.get_or_404(id)
    try:
        db.session.delete(book)
        db.session.commit()
        flash('Book deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting book', 'error')
    return redirect(url_for('admin.books'))

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
    try:
        db.session.delete(category)
        db.session.commit()
        flash('Category deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting category', 'error')
    return redirect(url_for('admin.categories'))

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
    if current_user.id == user_id:
        flash('You cannot delete your own admin account.', 'danger')
        return redirect(url_for('admin.users'))

    user = User.query.get_or_404(user_id)
    
    # Prevent deleting admin users
    if isinstance(user, Admin):
        flash('Cannot delete admin users.', 'danger')
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
        # Delete all borrow records for this user first
        BorrowRecord.query.filter_by(user_id=user.id).delete()
        db.session.commit()

        # Now delete the user
        db.session.delete(user)
        db.session.commit()
        
        flash(f'User {user.username} has been deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting user: {str(e)}")  # Log the actual error
        flash('An error occurred while deleting the user.', 'danger')
    
    return redirect(url_for('admin.users'))

@admin_bp.route('/borrows')
@login_required
@admin_required
def borrows():
    # Get filter parameters
    status = request.args.get('status', 'all')
    overdue = request.args.get('overdue', type=bool)
    
    # Update status and fines for all borrowed books
    borrowed_books = BorrowRecord.query.filter_by(status='borrowed').all()
    for borrow in borrowed_books:
        borrow.update_status()
    db.session.commit()
    
    # Base query
    query = BorrowRecord.query
    
    # Apply filters
    if status != 'all':
        query = query.filter_by(status=status)
    if overdue:
        query = query.filter(
            BorrowRecord.status == 'overdue'
        )
    
    borrows = query.order_by(BorrowRecord.borrowed_at.desc()).all()
    return render_template('admin/borrows.html', borrows=borrows)

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
