from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import hashlib
import datetime
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)
app.secret_key = 'your_secret_key'

def create_tables():
    conn = sqlite3.connect("mental_check.db")  
    # ユーザーテーブルの作成
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
    ''')
    # mental_checks テーブルの作成
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

# アプリ開始時にテーブルを作成
create_tables()


# データベース接続
def get_db_connection():
    conn = sqlite3.connect('mental_check.db')  # DB名を統一
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, hashed_password)).fetchone()
        conn.close()
        
        if user:
            session['user_id'] = user['id']
            return redirect(url_for('dashboard'))
        else:
            error = 'ユーザーID、またはパスワードが間違っています。'
            return render_template('login.html', error=error)
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        conn = get_db_connection()
        
        # ユーザー名が既に存在するか確認
        existing_user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        
        if existing_user:
            error = 'ユーザーIDは既に使用されています。'
            return render_template('register.html', error=error)

        # 新しいユーザーを登録
        conn.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_password))
        conn.commit()
        conn.close()
        
        return redirect(url_for('login'))
    
    return render_template('register.html')


@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    if request.method == 'POST':
        stress_level = request.form['stress_level']
        mood_description = request.form['mood_description']
        date = datetime.datetime.now().strftime('%Y-%m-%d')
        
        conn = get_db_connection()
        conn.execute('INSERT INTO mental_checks (user_id, date, stress_level, mood_description) VALUES (?, ?, ?, ?)',
                     (user_id, date, stress_level, mood_description))
        conn.commit()
        conn.close()
    
    conn = get_db_connection()
    checks = conn.execute('SELECT * FROM mental_checks WHERE user_id = ?', (user_id,)).fetchall()
    conn.close()
    
    return render_template('dashboard.html', checks=checks)

@app.route('/analysis')
def analysis():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    conn = get_db_connection()
    checks = conn.execute('SELECT * FROM mental_checks WHERE user_id = ?', (user_id,)).fetchall()
    conn.close()
    
    # 日付とストレスレベルのリストを作成
    dates = [check['date'] for check in checks]
    stress_levels = [check['stress_level'] for check in checks]

    # ストレスレベルのデータが存在する場合
    if stress_levels:
        # 30分単位でデータを調整する
        # 日時のリストをdatetimeに変換
        datetime_objects = [datetime.datetime.strptime(date, '%Y-%m-%d') for date in dates]

        # x軸の目盛りを30分刻みにする
        time_ticks = [datetime_objects[0] + datetime.timedelta(minutes=30 * i) for i in range(len(datetime_objects))]
        
        plt.figure(figsize=(10, 5))
        plt.plot(time_ticks, stress_levels, marker='o')

        plt.title('Stress Level Over Time')
        plt.xlabel('Date')
        plt.ylabel('Stress Level')

        # x軸の目盛りを30分ごとに設定
        plt.xticks(time_ticks, [t.strftime('%Y-%m-%d %H:%M') for t in time_ticks], rotation=45)

        # 画像として保存
        img = io.BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        plot_url = base64.b64encode(img.getvalue()).decode('utf8')
        
        return render_template('analysis.html', plot_url=plot_url)

    return render_template('analysis.html', plot_url=None)


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
