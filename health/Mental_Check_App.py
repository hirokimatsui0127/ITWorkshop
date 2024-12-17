import datetime
import hashlib
import io
import base64
import matplotlib
matplotlib.use('Agg')  # GUIバックエンドを使用せず画像として生成
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# スレッドプール設定
executor = ThreadPoolExecutor(max_workers=4)

# データベース接続
def get_db_connection():
    conn = sqlite3.connect('mental_check.db')
    conn.row_factory = sqlite3.Row
    return conn

# 初期テーブル作成
def create_tables():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS mental_checks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            stress_level INTEGER NOT NULL,
            mood_description TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    conn.commit()
    conn.close()

# アプリ起動時のテーブル作成
create_tables()

# ユーザーログイン
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = hashlib.sha256(request.form['password'].encode()).hexdigest()
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password)).fetchone()
        conn.close()

        if user:
            session['user_id'] = user['id']
            return redirect(url_for('dashboard'))
        else:
            error = 'ユーザーIDまたはパスワードが間違っています。'
    return render_template('login.html', error=error)

# ユーザー登録
@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = hashlib.sha256(request.form['password'].encode()).hexdigest()

        conn = get_db_connection()
        existing_user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()

        if existing_user:
            error = 'ユーザーIDは既に使用されています。'
        else:
            conn.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
            conn.commit()
            conn.close()
            return redirect(url_for('login'))
        conn.close()
    return render_template('register.html', error=error)

# ダッシュボード
@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    page = request.args.get('page', 1, type=int)
    per_page = 5
    error = None

    if request.method == 'POST':
        stress_level = request.form['stress_level']
        mood_description = request.form['mood_description']

        if len(mood_description) > 500:
            error = 'コメントは500文字以内で入力してください。'
        else:
            date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            conn = get_db_connection()
            conn.execute(
                'INSERT INTO mental_checks (user_id, date, stress_level, mood_description) VALUES (?, ?, ?, ?)',
                (user_id, date, stress_level, mood_description)
            )
            conn.commit()
            conn.close()
            return redirect(url_for('dashboard'))

    conn = get_db_connection()
    checks = conn.execute(
        'SELECT * FROM mental_checks WHERE user_id = ? ORDER BY date DESC LIMIT ? OFFSET ?',
        (user_id, per_page, (page - 1) * per_page)
    ).fetchall()
    total_checks = conn.execute('SELECT COUNT(*) FROM mental_checks WHERE user_id = ?', (user_id,)).fetchone()[0]
    conn.close()

    total_pages = (total_checks + per_page - 1) // per_page
    return render_template('dashboard.html', checks=checks, page=page, total_pages=total_pages, error=error)


@app.route('/analysis')
def analysis():
    return redirect(url_for('plot'))

# データ取得
def fetch_data(user_id):
    conn = get_db_connection()
    checks = conn.execute('SELECT * FROM mental_checks WHERE user_id = ? ORDER BY date DESC LIMIT 30', (user_id,)).fetchall()
    conn.close()
    return checks

# グラフ表示
@app.route('/plot')
def plot():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    checks = fetch_data(user_id)

    if not checks:
        return render_template('analysis.html', plot_url=None)

    dates = [datetime.datetime.strptime(check['date'], '%Y-%m-%d %H:%M:%S') for check in checks]
    stress_levels = [check['stress_level'] for check in checks]

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(dates, stress_levels, marker='o', linestyle='-', color='b', label='Stress Level')
    ax.set_title('Stress Level Over Time')
    ax.set_xlabel('Date and Time')
    ax.set_ylabel('Stress Level (0-100)')
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M:%S'))
    ax.xaxis.set_major_locator(mdates.HourLocator(interval=1))
    plt.xticks(rotation=45)
    plt.tight_layout()

    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode('utf8')
    plt.close(fig)

    return render_template('analysis.html', plot_url=plot_url)

# ログアウト
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('home'))

# ホームページ
@app.route('/')
def home():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True, threaded=True)
