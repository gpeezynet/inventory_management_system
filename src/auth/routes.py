# src/auth/routes.py
from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from src.auth.models import User
from src.main import app, db

auth_bp = Blueprint('auth', __name__)

# Login Manager Setup
from flask_login import LoginManager

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "auth.login"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# User Login Route
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash("Login successful!", "success")
            return redirect(url_for('index'))
        else:
            flash("Invalid username or password!", "error")

    return render_template('login.html')

# User Logout Route
@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Logged out successfully!", "success")
    return redirect(url_for('auth.login'))

# User Registration Route
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if User.query.filter_by(username=username).first():
            flash("Username already taken!", "error")
            return redirect(url_for('auth.register'))

        # Make the first user an admin
        role = "admin" if User.query.count() == 0 else "user"

        new_user = User(username=username, role=role)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        flash(f"User registered successfully! Role: {role}", "success")
        return redirect(url_for('auth.login'))

    return render_template('register.html')
