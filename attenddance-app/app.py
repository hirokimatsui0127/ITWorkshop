from flask import Flask, render_template, redirect, url_for, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, LoginManager, login_user, login_required, current_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config
from models import db, User, Attendance, StressCheck
from datetime import datetime

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('admin_dashboard') if user.role == 'admin' else url_for('user_dashboard'))
    return render_template('login.html')

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        return redirect(url_for('index'))

    users = User.query.all()
    return render_template('admin_dashboard.html', users=users)

@app.route('/admin/user/<int:user_id>')
@login_required
def user_details(user_id):
    if current_user.role != 'admin':
        return redirect(url_for('index'))

    user = User.query.get(user_id)
    attendance_records = Attendance.query.filter_by(user_id=user.id).all()
    stress_check_records = StressCheck.query.filter_by(user_id=user.id).all()
    return render_template('user_details.html', user=user, attendance_records=attendance_records, stress_check_records=stress_check_records)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/user/dashboard')
@login_required
def user_dashboard():
    # ユーザー専用ダッシュボード
    attendance_records = Attendance.query.filter_by(user_id=current_user.id).all()
    stress_check_records = StressCheck.query.filter_by(user_id=current_user.id).all()
    return render_template('user_dashboard.html', attendance_records=attendance_records, stress_check_records=stress_check_records)

@app.route('/clock_in')
@login_required
def clock_in():
    new_attendance = Attendance(user_id=current_user.id, clock_in_time=datetime.now())
    db.session.add(new_attendance)
    db.session.commit()
    return redirect(url_for('user_dashboard'))

@app.route('/clock_out')
@login_required
def clock_out():
    attendance = Attendance.query.filter_by(user_id=current_user.id).order_by(Attendance.clock_in_time.desc()).first()
    attendance.clock_out_time = datetime.now()
    db.session.commit()
    return redirect(url_for('user_dashboard'))

@app.route('/stress_check', methods=['GET', 'POST'])
@login_required
def stress_check():
    if request.method == 'POST':
        stress_level = request.form['stress_level']
        mood = request.form['mood']
        fatigue = request.form['fatigue']
        new_stress_check = StressCheck(
            user_id=current_user.id,
            date=datetime.now(),
            stress_level=stress_level,
            mood=mood,
            fatigue=fatigue
        )
        db.session.add(new_stress_check)
        db.session.commit()
        return redirect(url_for('user_dashboard'))

    return render_template('stress_check.html')

if __name__ == '__main__':
    app.run(debug=True)
