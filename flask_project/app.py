from flask import Flask, render_template, redirect, url_for, request
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # セッション管理のために必要

login_manager = LoginManager()
login_manager.init_app(app)

# ユーザーデータベース（ここではサンプルデータ）
users = {"user1": {"password": "password1"}, "user2": {"password": "password2"}}

class User(UserMixin):
    def __init__(self, username):
        self.id = username

@login_manager.user_loader
def load_user(username):
    return User(username) if username in users else None

# ルートURL（/）にアクセスしたときのビュー
@app.route('/')
def home():
    return render_template('home.html')  # home.htmlテンプレートを表示

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

if __name__ == '__main__':
    app.run(debug=True)
