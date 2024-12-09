from flask import Flask
from flask_login import LoginManager

app = Flask(__name__)
app.secret_key = 'your_secret_key'

login_manager = LoginManager()
login_manager.init_app(app)

# モデルやルートをインポート
from app import routes, models
