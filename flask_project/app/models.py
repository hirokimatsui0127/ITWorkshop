from flask_login import UserMixin

# ユーザーデータベース（サンプルデータ）
users = {"user1": {"password": "password1"}, "user2": {"password": "password2"}}

class User(UserMixin):
    def __init__(self, username):
        self.id = username

# ユーザーのロード処理
from app import login_manager

@login_manager.user_loader
def load_user(username):
    return User(username) if username in users else None
