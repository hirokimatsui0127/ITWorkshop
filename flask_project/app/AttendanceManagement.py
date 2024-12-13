from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from zoneinfo import ZoneInfo

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///attendance.db'
app.config['SECRET_KEY'] = 'your_secret_key'
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

def get_japan_time():
    return datetime.now(ZoneInfo("Asia/Tokyo"))

# User model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    attendance_records = db.relationship('Attendance', backref='user', lazy=True)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

# Attendance model
class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, default=lambda: datetime.now(ZoneInfo("Asia/Tokyo")).date())  # 日本時間の日付
    check_in = db.Column(db.Time, nullable=True)
    check_out = db.Column(db.Time, nullable=True)
    mood = db.Column(db.String(50), nullable=True)
    stress_level = db.Column(db.Integer, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('register'))
        new_user = User(username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    if request.method == 'POST':
        mood = request.form.get('mood', '不明')
        stress_level = int(request.form.get('stress_level', 0))  # 数値型に変換
        action = request.form.get('action')
        now_japan = get_japan_time()

        # 今日の日付の出勤記録を取得
        attendance = Attendance.query.filter_by(user_id=current_user.id, date=now_japan.date()).first()

        if action == 'check_in' and not attendance:
            attendance = Attendance(user_id=current_user.id, check_in=now_japan.time(), mood=mood, stress_level=stress_level)
            db.session.add(attendance)
            db.session.commit()
        elif action == 'check_out' and attendance:
            attendance.check_out = now_japan.time()
            db.session.commit()

    records = Attendance.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', records=records)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # データベースを作成
    app.run(debug=True)
