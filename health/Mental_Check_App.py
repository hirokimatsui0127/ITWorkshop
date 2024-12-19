import datetime
import hashlib
import io
import base64
import matplotlib
matplotlib.use('Agg')
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
DATABASE = 'mental_check.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# 初期テーブル作成
def create_tables():
    with get_db_connection() as conn:
        conn.executescript('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS mental_checks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                stress_level INTEGER NOT NULL,
                mood_description TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            );
        ''')

# グラフ生成関数
def generate_plot(dates, stress_levels, title):
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(dates, stress_levels, marker='o', linestyle='-', color='b', label='Stress Level')
    ax.set_title(title)
    ax.set_xlabel('Date and Time')
    ax.set_ylabel('Stress Level (0-100)')
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M:%S'))
    ax.xaxis.set_major_locator(mdates.HourLocator(interval=1))
    plt.xticks(rotation=45)
    plt.tight_layout()

    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plt.close(fig)
    return base64.b64encode(img.getvalue()).decode('utf8')

# アプリ起動時のテーブル作成
create_tables()

# ユーザーログイン
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = hashlib.sha256(request.form['password'].encode()).hexdigest()
        with get_db_connection() as conn:
            user = conn.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password)).fetchone()

        if user:
            session['user_id'] = user['id']
            return redirect(url_for('dashboard'))
        else:
            error = 'ユーザーIDまたはパスワードが間違っています。'
    return render_template('login.html', error=error)

# 新規登録
@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = hashlib.sha256(request.form['password'].encode()).hexdigest()
        with get_db_connection() as conn:
            try:
                conn.execute(
                    'INSERT INTO users (username, password) VALUES (?, ?)',
                    (username, password)
                )
                return redirect(url_for('login'))
            except sqlite3.IntegrityError:
                error = 'このユーザーIDは既に使用されています。'
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
            with get_db_connection() as conn:
                conn.execute(
                    'INSERT INTO mental_checks (user_id, date, stress_level, mood_description) VALUES (?, ?, ?, ?)',
                    (user_id, date, stress_level, mood_description)
                )

            return redirect(url_for('dashboard'))

    with get_db_connection() as conn:
        checks = conn.execute(
            'SELECT * FROM mental_checks WHERE user_id = ? ORDER BY date DESC LIMIT ? OFFSET ?',
            (user_id, per_page, (page - 1) * per_page)
        ).fetchall()
        total_checks = conn.execute('SELECT COUNT(*) FROM mental_checks WHERE user_id = ?', (user_id,)).fetchone()[0]

    total_pages = (total_checks + per_page - 1) // per_page
    return render_template('dashboard.html', checks=checks, page=page, total_pages=total_pages, error=error)

# グラフ表示
@app.route('/plot')
def plot():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    with get_db_connection() as conn:
        checks = conn.execute(
            'SELECT * FROM mental_checks WHERE user_id = ? ORDER BY date DESC LIMIT 30',
            (user_id,)
        ).fetchall()

    if not checks:
        return render_template('analysis.html', plot_url=None)

    dates = [datetime.datetime.strptime(check['date'], '%Y-%m-%d %H:%M:%S') for check in checks]
    stress_levels = [check['stress_level'] for check in checks]

    plot_url = generate_plot(dates, stress_levels, 'Stress Level Over Time')
    return render_template('analysis.html', plot_url=plot_url)

# 日付ごとのデータを取得してグラフ化
@app.route('/analysis', methods=['GET'])
def analysis():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    selected_date = request.args.get('date', datetime.date.today().strftime('%Y-%m-%d'))

    with get_db_connection() as conn:
        data = conn.execute(
            'SELECT * FROM mental_checks WHERE user_id = ? AND date LIKE ? ORDER BY date DESC',
            (session['user_id'], f'{selected_date}%')
        ).fetchall()

    if data:
        dates = [datetime.datetime.strptime(record['date'], '%Y-%m-%d %H:%M:%S') for record in data]
        stress_levels = [record['stress_level'] for record in data]
        plot_url = generate_plot(dates, stress_levels, f'Stress Level for {selected_date}')
    else:
        plot_url = None

    return render_template('analysis.html', plot_url=plot_url, selected_date=selected_date)

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
