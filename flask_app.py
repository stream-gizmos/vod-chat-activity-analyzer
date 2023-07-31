from flask import Flask, render_template, request, redirect, url_for
from chat_downloader import ChatDownloader
import json
import pandas as pd
import plotly
import plotly.graph_objects as go
from datetime import timedelta

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/start_download', methods=['POST'])
def start_download():
    url = request.form.get('url')  # Assume you're getting the URL from a form on your homepage

    # Get the VOD number from the URL
    vod_number = url.split('/')[-1]

    chat = ChatDownloader().get_chat(url)  # create a generator

    list_of_times = []

    for message in chat:
        list_of_times.append(message['time_in_seconds'])

    with open(f'{vod_number}_times.json', 'w') as f:
        json.dump(list_of_times, f)

    return redirect(url_for('display_graph', vod_number=vod_number))

@app.route('/display_graph/<vod_number>', methods=['GET'])
def display_graph(vod_number):
    with open(f'{vod_number}_times.json', 'r') as f:
        data = json.load(f)

    df = pd.DataFrame(data, columns=['timestamp'])

    df['timestamp'] = pd.to_timedelta(df['timestamp'], unit='s')

    df['message'] = 1

    df.set_index('timestamp', inplace=True)
    df = df.resample('5S').sum()

    intervals = ['15S', '60S', '300S']

    fig = go.Figure()

    # For each interval
    for interval in intervals:
        df_resampled = df.rolling(interval).sum()
        fig.add_trace(go.Scatter(
            x=df_resampled.index.total_seconds() / 60,  # convert seconds to minutes
            y=df_resampled['message'],
            mode='lines',
            name=interval
        ))

    fig.update_layout(
        autosize=True,
        hovermode='x',
        title='Twitch Chat Activity Tracker',
        xaxis_title='Time (in minutes)',  # change x-axis label to minutes
        yaxis_title='Number of messages',
        xaxis=dict(
            tickmode='linear',
            tick0=0,
            dtick=30  # change interval to 30 minutes
        )
    )

    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    return render_template('graph.html', graphJSON=graphJSON)

if __name__ == "__main__":
    app.run(debug=False)

