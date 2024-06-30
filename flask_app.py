import json

import pandas as pd
import plotly
import plotly.graph_objects as go
from chat_downloader import ChatDownloader
from flask import Flask, render_template, request, redirect, url_for

from lib import hash_to_chat_file, hash_to_meta_file, hash_to_times_file, url_to_hash

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/start_download', methods=['POST'])
def start_download():
    url = request.form.get('url')  # Assume you're getting the URL from a form on your homepage
    video_hash = url_to_hash(url)

    with open(hash_to_meta_file(video_hash), 'w') as fp:
        data = {
            'url': url,
        }
        json.dump(data, fp, indent=2)

    chat = ChatDownloader().get_chat(url, output=hash_to_chat_file(video_hash), indent=0)

    list_of_times = []
    for message in chat:
        list_of_times.append(message['time_in_seconds'])

    with open(hash_to_times_file(video_hash), 'w') as fp:
        json.dump(list_of_times, fp)

    return redirect(url_for('display_graph', video_hash=video_hash))

@app.route('/display_graph/<video_hash>', methods=['GET'])
def display_graph(video_hash):
    with open(hash_to_meta_file(video_hash), 'r') as fp:
        meta = json.load(fp)

    with open(hash_to_times_file(video_hash), 'r') as fp:
        data = json.load(fp)

    df = pd.DataFrame(data, columns=['timestamp'])

    # Convert timestamp to timedelta
    df['timestamp'] = pd.to_timedelta(df['timestamp'], unit='s')
    # Assign a message count of 1 for each timestamp
    df['message'] = 1

    # Resample the data into 5 second bins, filling in any missing seconds with 0
    df.set_index('timestamp', inplace=True)
    df = df.resample('5S').sum()

    # Define your time intervals in seconds
    intervals = ['15S', '60S', '300S']

    # Create a new figure
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
        xaxis_title='Time (in minutes)',  # change x-axis label to minutes
        yaxis_title='Number of messages',
        xaxis=dict(
            tickmode='linear',
            tick0=0,
            dtick=30  # change interval to 30 minutes
        )
    )

    graph_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    return render_template('graph.html', url=meta['url'], graph_json=graph_json)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
