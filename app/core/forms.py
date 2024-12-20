from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, TextAreaField, SubmitField, BooleanField, IntegerField, DateField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError, Optional, NumberRange
from app.core.models import User, Book

class AdminLoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class UserRegistrationForm(FlaskForm):
    library_id = StringField('Library ID', validators=[DataRequired(), Length(min=4, max=20)])
    name = StringField('Full Name', validators=[DataRequired(), Length(max=100)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    phone = StringField('Phone Number', validators=[Length(max=20)])
    address = StringField('Address', validators=[Length(max=200)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', 
                                   validators=[DataRequired(), EqualTo('password', message='Passwords must match')])
    submit = SubmitField('Register')

    def validate_library_id(self, field):
        if User.query.filter_by(library_id=field.data).first():
            raise ValidationError('Library ID already registered.')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered.')

class UserLoginForm(FlaskForm):
    library_id = StringField('Library ID', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class BookForm(FlaskForm):
    isbn = StringField('ISBN', validators=[Optional(), Length(max=13)],
                      description='Enter ISBN if available (13 digits)')
    title = StringField('Title', validators=[DataRequired(), Length(max=200)],
                       description='Book title (required)')
    author = StringField('Author', validators=[DataRequired(), Length(max=100)],
                        description='Book author (required)')
    publisher = StringField('Publisher', validators=[Optional(), Length(max=100)],
                          description='Publisher name')
    publication_year = IntegerField('Publication Year', validators=[Optional()],
                                  description='Year of publication')
    description = TextAreaField('Description', validators=[Optional()],
                              description='Book description')
    quantity = IntegerField('Quantity', validators=[DataRequired(), NumberRange(min=1)],
                          description='Number of copies available')
    location = StringField('Location', validators=[Optional(), Length(max=50)],
                         description='Shelf or section location')
    submit = SubmitField('Add Book')

    def validate_isbn(self, field):
        book = Book.query.filter_by(isbn=field.data).first()
        if book:
            raise ValidationError('This ISBN is already registered.')

class CategoryForm(FlaskForm):
    name = StringField('Category Name', validators=[DataRequired(), Length(max=50)])
    description = StringField('Description', validators=[Length(max=200)])
    submit = SubmitField('Submit Category')

class BorrowForm(FlaskForm):
    due_date = DateField('Due Date', validators=[DataRequired()])
    submit = SubmitField('Borrow Book')
