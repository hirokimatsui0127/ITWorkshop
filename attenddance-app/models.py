from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='user')  # user or admin
    attendance = db.relationship('Attendance', backref='user', lazy=True)
    stress_checks = db.relationship('StressCheck', backref='user', lazy=True)

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    clock_in_time = db.Column(db.DateTime, nullable=False)
    clock_out_time = db.Column(db.DateTime)

class StressCheck(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    stress_level = db.Column(db.String(50))
    mood = db.Column(db.String(100))
    fatigue = db.Column(db.String(100))
