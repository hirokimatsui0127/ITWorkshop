from werkzeug.security import generate_password_hash
from app import db
from models import User

admin_users = [
    {'username': 'admin1', 'password': 'password123'},
    {'username': 'admin2', 'password': 'password123'},
    {'username': 'admin3', 'password': 'password123'},
    {'username': 'admin4', 'password': 'password123'},
    {'username': 'admin5', 'password': 'password123'}
]

for admin in admin_users:
    hashed_password = generate_password_hash(admin['password'], method='sha256')
    new_admin = User(username=admin['username'], password=hashed_password, role='admin')
    db.session.add(new_admin)

db.session.commit()
