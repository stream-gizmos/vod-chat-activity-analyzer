import json

import pandas as pd
import plotly
from chat_downloader import ChatDownloader
from flask import Blueprint, render_template, request, redirect, url_for

from flask_app.services.lib import build_dataframe_by_timestamp, build_scatter_fig, get_custom_emoticons, \
    hash_to_chat_file, hash_to_emoticons_file, hash_to_meta_file, hash_to_timestamps_file, is_http_url, make_buckets, \
    mine_emoticons, normalize_timeline, url_to_hash, build_emoticons_dataframe, build_bar_fig, read_emoticons_timestamps

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
        return redirect(url_for(".index", error="Wrong URLs provided"))

    custom_emoticons = get_custom_emoticons()

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

        messages_timestamps = []
        emoticons_timestamps: dict[str, list[int]] = {}
        for message in chat:
            if message["time_in_seconds"] < 0:
                continue

            messages_timestamps.append(message["timestamp"])

            message_emotes = mine_emoticons(message["message"], message.get("emotes", []), custom_emoticons)
            for emoticon in message_emotes:
                if emoticon not in emoticons_timestamps:
                    emoticons_timestamps[emoticon] = []

                emoticons_timestamps[emoticon].append(message["timestamp"])

        with open(hash_to_timestamps_file(video_hash), "w") as fp:
            json.dump(messages_timestamps, fp)

        if len(emoticons_timestamps):
            with open(hash_to_emoticons_file(video_hash), "w") as fp:
                json.dump(emoticons_timestamps, fp)

    hashes_string = ",".join(hashes)

    return redirect(url_for(".display_graph", video_hashes=hashes_string))


@front_bp.route("/display_graph/<video_hashes>", methods=["GET"])
def display_graph(video_hashes):
    video_hashes = video_hashes.split(",")

    time_step = 5
    rolling_windows = [f"{3 * time_step}s", f"{12 * time_step}s", f"{60 * time_step}s"]

    combined_df: pd.DataFrame | None = None

    graphs = {}
    for i, video_hash in enumerate(video_hashes, start=1):
        with open(hash_to_meta_file(video_hash), "r") as fp:
            meta = json.load(fp)
        with open(hash_to_timestamps_file(video_hash), "r") as fp:
            data = json.load(fp)

        df = build_dataframe_by_timestamp(data)
        combined_df = df.copy() if combined_df is None else combined_df.add(df, fill_value=0)

        df = normalize_timeline(df, time_step)
        rolling_dataframes = make_buckets(df, rolling_windows)

        fig = build_scatter_fig(rolling_dataframes, time_step, "Number of messages", "Video time (in minutes)")
        graph_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
        graphs[f"graph{i:02d}_1"] = dict(url=meta["url"], json=graph_json)

        emoticons: dict[str, list[int]] = read_emoticons_timestamps(hash_to_emoticons_file(video_hash))
        emoticons_df = build_emoticons_dataframe(emoticons, time_step * 12, top_size=8)

        if len(emoticons_df) > 0:
            fig = build_bar_fig(emoticons_df, time_step * 12, "Number of emoticons", "Video time (in minutes)")
            graph_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
            graphs[f"graph{i:02d}_2"] = dict(url=meta["url"], json=graph_json)

    if len(video_hashes) > 1 and combined_df is not None:
        combined_df = normalize_timeline(combined_df, time_step)
        rolling_dataframes = make_buckets(combined_df, rolling_windows)

        fig = build_scatter_fig(rolling_dataframes, time_step, "Number of messages", "Stream time (in minutes)")
        graph_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
        graphs[f"graph{0:02d}"] = dict(caption='Combined stream stats', json=graph_json)

    return render_template("graph.html", graphs=graphs)
