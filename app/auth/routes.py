from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.core.forms import UserLoginForm, UserRegistrationForm
from app.core.models import User
from app import db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('core.dashboard'))
    
    form = UserLoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(library_id=form.library_id.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page if next_page else url_for('core.dashboard'))
        flash('Invalid library ID or password', 'error')
    
    return render_template('auth/login.html', form=form)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('core.dashboard'))
    
    form = UserRegistrationForm()
    
    if form.validate_on_submit():
        user = User(
            library_id=form.library_id.data,
            name=form.name.data,
            email=form.email.data,
            phone=form.phone.data,
            address=form.address.data
        )
        user.set_password(form.password.data)
        
        db.session.add(user)
        try:
            db.session.commit()
            flash('Registration successful! You can now login.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            if 'UNIQUE constraint' in str(e):
                if 'library_id' in str(e):
                    flash('Library ID already registered.', 'error')
                elif 'email' in str(e):
                    flash('Email already registered.', 'error')
            else:
                flash('An error occurred during registration. Please try again.', 'error')
    
    return render_template('auth/register.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
