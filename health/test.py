import datetime
import plotly.graph_objects as go
from flask import Flask, render_template

app = Flask(__name__)

# ダミーデータ
dates = [datetime.datetime.now() - datetime.timedelta(days=i) for i in range(5)]
stress_levels = [30, 45, 60, 50, 70]
mood_descriptions = ['Good', 'Stressed', 'Neutral', 'Happy', 'Sad']

# Plotlyを使用してインタラクティブなグラフを作成
def create_plot():
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=dates,
        y=stress_levels,
        mode='markers',
        text=mood_descriptions,  # 各点にマウスオーバー時に表示されるテキスト
        marker=dict(size=12, color='blue', opacity=0.7),
    ))

    fig.update_layout(
        title='Stress Level Over Time',
        xaxis_title='Date',
        yaxis_title='Stress Level',
    )

    return fig.to_html(full_html=False)  # PlotlyのグラフをHTML形式で返す

# アナリシスページ
@app.route('/analysis')
def analysis():
    plot_html = create_plot()  # Plotlyのグラフを作成
    return render_template('analysis.html', plot_html=plot_html)

if __name__ == '__main__':
    app.run(debug=True)
