import json

import pandas as pd
import plotly
import plotly.graph_objects as go
from chat_downloader import ChatDownloader
from flask import Flask, render_template, request, redirect, url_for

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

    # List to hold time_text of each message
    list_of_times = []

    for message in chat:
        # Append the time_text of each message to the list
        list_of_times.append(message['time_in_seconds'])

    # Save the list of times to a JSON file named after the VOD number
    with open(f'{vod_number}_times.json', 'w') as f:
        json.dump(list_of_times, f)

    return redirect(url_for('display_graph', vod_number=vod_number))

@app.route('/display_graph/<vod_number>', methods=['GET'])
def display_graph(vod_number):
    # Load the JSON data from a file
    with open(f'{vod_number}_times.json', 'r') as f:
        data = json.load(f)

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
    app.run(host="0.0.0.0", port=8080, debug=False)
