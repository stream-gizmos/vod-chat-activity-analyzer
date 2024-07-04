import json

import pandas as pd
import plotly
import plotly.graph_objects as go
from chat_downloader import ChatDownloader
from flask import Blueprint, render_template, request, redirect, url_for

from lib import hash_to_chat_file, hash_to_meta_file, hash_to_times_file, is_http_url, url_to_hash

front_bp = Blueprint('front', __name__)


@front_bp.route("/")
def index():
    return render_template(
        "index.html",
        error=request.args.get("error"),
    )


@front_bp.route("/start_download", methods=["POST"])
def start_download():
    urls = request.form.getlist("url[]")
    urls = map(str.strip, urls)
    urls = filter(None, urls)
    urls = filter(is_http_url, urls)
    urls = set(urls)

    if not len(urls):
        return redirect(url_for("front.index", error="Wrong URLs provided"))

    hashes = []
    for url in sorted(urls):
        video_hash = url_to_hash(url)
        hashes.append(video_hash)

        with open(hash_to_meta_file(video_hash), "w") as fp:
            data = {
                "url": url,
            }
            json.dump(data, fp, indent=2)

        chat = ChatDownloader().get_chat(url, output=hash_to_chat_file(video_hash))

        list_of_times = []
        for message in chat:
            list_of_times.append(message["time_in_seconds"])

        with open(hash_to_times_file(video_hash), "w") as fp:
            json.dump(list_of_times, fp)

    hashes_string = ",".join(hashes)

    return redirect(url_for("front.display_graph", video_hashes=hashes_string))


@front_bp.route("/display_graph/<video_hashes>", methods=["GET"])
def display_graph(video_hashes):
    video_hashes = video_hashes.split(",")

    graphs = {}
    for i, video_hash in enumerate(video_hashes, start=1):
        with open(hash_to_meta_file(video_hash), "r") as fp:
            meta = json.load(fp)

        with open(hash_to_times_file(video_hash), "r") as fp:
            data = json.load(fp)

        df = pd.DataFrame(data, columns=["timestamp"])

        # Convert timestamp to timedelta
        df["timestamp"] = pd.to_timedelta(df["timestamp"], unit="s")
        # Assign a message count of 1 for each timestamp
        df["message"] = 1

        # Resample the data into 5 second bins, filling in any missing seconds with 0
        df.set_index("timestamp", inplace=True)
        df = df.resample("5S").sum()

        # Define your time intervals in seconds
        intervals = ["15S", "60S", "300S"]

        # Create a new figure
        fig = go.Figure()

        # For each interval
        for interval in intervals:
            df_resampled = df.rolling(interval).sum()
            fig.add_trace(go.Scatter(
                x=df_resampled.index.total_seconds() / 60,  # convert seconds to minutes
                y=df_resampled["message"],
                mode="lines",
                name=interval,
            ))

        fig.update_layout(
            title="Number of messages",
            autosize=True,
            height=300,
            margin=dict(t=30, b=0, l=0, r=0, pad=5),
            hovermode="x",
            xaxis_title="Time (in minutes)",
            xaxis=dict(
                tickmode="linear",
                tick0=0,
                dtick=30,  # change interval to 30 minutes
            ),
        )

        graph_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

        graphs[f"graph{i}"] = dict(url=meta["url"], json=graph_json)

    return render_template("graph.html", graphs=graphs)
