import json

import pandas as pd
import plotly
from chat_downloader import ChatDownloader
from flask import Blueprint, render_template, request, redirect, url_for

from flask_app.services.lib import build_dataframe_by_timestamp, build_scatter_fig, hash_to_chat_file, \
    hash_to_meta_file, hash_to_times_file, hash_to_timestamps_file, is_http_url, make_buckets, url_to_hash

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
        list_of_timestamp = []
        for message in chat:
            if message["time_in_seconds"] < 0:
                continue

            list_of_times.append(message["time_in_seconds"])
            list_of_timestamp.append(message["timestamp"])

        with open(hash_to_times_file(video_hash), "w") as fp:
            json.dump(list_of_times, fp)
        with open(hash_to_timestamps_file(video_hash), "w") as fp:
            json.dump(list_of_timestamp, fp)

    hashes_string = ",".join(hashes)

    return redirect(url_for("front.display_graph", video_hashes=hashes_string))


@front_bp.route("/display_graph/<video_hashes>", methods=["GET"])
def display_graph(video_hashes):
    video_hashes = video_hashes.split(",")

    intervals = ["15S", "60S", "300S"]
    combined_df: pd.DataFrame | None = None

    graphs = {}
    for i, video_hash in enumerate(video_hashes, start=1):
        with open(hash_to_meta_file(video_hash), "r") as fp:
            meta = json.load(fp)
        with open(hash_to_timestamps_file(video_hash), "r") as fp:
            data = json.load(fp)

        df = build_dataframe_by_timestamp(data)
        combined_df = df.copy() if combined_df is None else combined_df.add(df, fill_value=0)

        interval_dataframes = make_buckets(df, intervals)

        fig = build_scatter_fig(interval_dataframes, "Number of messages", "Video time (in minutes)")
        graph_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
        graphs[f"graph{i:02d}"] = dict(url=meta["url"], json=graph_json)

    if len(video_hashes) > 1 and combined_df is not None:
        interval_dataframes = make_buckets(combined_df, intervals)

        fig = build_scatter_fig(interval_dataframes, "Number of messages", "Stream time (in minutes)")
        graph_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
        graphs[f"graph{0:02d}"] = dict(caption='Combined stream stats', json=graph_json)

    return render_template("graph.html", graphs=graphs)
