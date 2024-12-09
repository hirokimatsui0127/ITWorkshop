from flask import render_template, redirect, url_for, request
from flask_login import login_user, login_required, logout_user, current_user
from app import app
from .models import User, users

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users and users[username]['password'] == password:
            user = User(username)
            login_user(user)
            return redirect(url_for('member'))
        else:
            return 'Invalid credentials', 401
    return render_template('login.html')

@app.route('/member')
@login_required
def member():
    return f'Welcome to your member page, {current_user.id}!'

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))
