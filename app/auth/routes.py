from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.auth import bp
from app.models import User
from app.extensions import db


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('admin.dashboard'))
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user, remember=True)
            next_page = request.args.get('next')
            if next_page and next_page.startswith('/'):
                return redirect(next_page)
            return redirect(url_for('admin.dashboard'))
        flash('इमेल वा पासवर्ड गलत छ।', 'danger')
    return render_template('auth/login.html')


@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('सफलतापूर्वक लगआउट भयो।', 'success')
    return redirect(url_for('main.home'))
