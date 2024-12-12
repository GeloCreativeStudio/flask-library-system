from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db

class Admin(UserMixin, db.Model):
    __tablename__ = 'admin'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)

    @property
    def is_admin(self):
        return True

    def get_id(self):
        return f'a_{self.id}'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @staticmethod
    def create_default_admin():
        admin = Admin.query.filter_by(username='admin').first()
        if not admin:
            admin = Admin(username='admin')
            admin.set_password('admin123')  # Default password
            db.session.add(admin)
            db.session.commit()
            return True
        return False

class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    library_id = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(20))
    address = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    borrowed_books = db.relationship('BorrowRecord', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Category(db.Model):
    __tablename__ = 'category'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(200))
    books = db.relationship('Book', backref='category', lazy=True)

class Book(db.Model):
    __tablename__ = 'book'
    id = db.Column(db.Integer, primary_key=True)
    isbn = db.Column(db.String(13), unique=True, nullable=False)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    publisher = db.Column(db.String(100))
    publication_year = db.Column(db.Integer)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    description = db.Column(db.Text)
    quantity = db.Column(db.Integer, default=1)
    available_quantity = db.Column(db.Integer, default=1)
    location = db.Column(db.String(50))  # Shelf or section location
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    borrow_records = db.relationship('BorrowRecord', backref='book', lazy=True)

    @property
    def is_available(self):
        return self.available_quantity > 0

class BorrowRecord(db.Model):
    __tablename__ = 'borrow_record'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    borrowed_at = db.Column(db.DateTime, default=datetime.utcnow)
    due_date = db.Column(db.DateTime, nullable=False)
    returned_at = db.Column(db.DateTime)
    fine_amount = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(20), default='borrowed')  # borrowed, returned, overdue

    def calculate_fine(self):
        if self.status == 'borrowed' and self.is_overdue:
            # For unreturned books, calculate fine up to current date
            days_overdue = (datetime.utcnow() - self.due_date).days
            return max(0, days_overdue * 2.0)  # ₱2 per day
        elif self.returned_at and self.returned_at > self.due_date:
            # For returned books, calculate fine up to return date
            days_overdue = (self.returned_at - self.due_date).days
            return max(0, days_overdue * 2.0)  # ₱2 per day
        return 0.0

    def mark_as_returned(self):
        self.returned_at = datetime.utcnow()
        self.status = 'returned'
        self.fine_amount = self.calculate_fine()
        self.book.available_quantity += 1

    @property
    def is_overdue(self):
        if self.status == 'borrowed':
            return datetime.utcnow() > self.due_date
        return False

    def update_status(self):
        if self.status == 'borrowed':
            if self.is_overdue:
                self.status = 'overdue'
                # Update fine amount for display
                self.fine_amount = self.calculate_fine()
            else:
                self.status = 'borrowed'
                self.fine_amount = 0.0