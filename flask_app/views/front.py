import json

import pandas as pd
import plotly
from chat_downloader import ChatDownloader
from flask import Blueprint, render_template, request, redirect, url_for

from flask_app.services.lib import (
    build_dataframe_by_timestamp,
    build_emoticons_figure,
    build_messages_figure,
    get_custom_emoticons,
    hash_to_chat_file,
    hash_to_emoticons_file,
    hash_to_meta_file,
    hash_to_timestamps_file,
    is_http_url,
    mine_emoticons,
    read_json_file,
    url_to_hash,
)

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

    combined_messages_df: pd.DataFrame | None = None
    combined_emoticons: dict[str, list[int]] = {}

    graphs = {}
    for i, video_hash in enumerate(video_hashes, start=1):
        meta = read_json_file(hash_to_meta_file(video_hash)) or {}

        messages = read_json_file(hash_to_timestamps_file(video_hash)) or []
        messages_df = build_dataframe_by_timestamp(messages)

        emoticons: dict[str, list[int]] = read_json_file(hash_to_emoticons_file(video_hash)) or {}

        combined_messages_df = messages_df.copy() if combined_messages_df is None \
            else combined_messages_df.add(messages_df, fill_value=0)

        for emote, emoticon_times in emoticons.items():
            combined_emoticons[emote] = emoticon_times if emote not in combined_emoticons \
                else combined_emoticons[emote].extend(emoticon_times)

        messages_fig = build_messages_figure(messages_df, rolling_windows, time_step)
        graph_json = json.dumps(messages_fig, cls=plotly.utils.PlotlyJSONEncoder)
        graphs[f"graph{i:02d}_1"] = dict(url=meta["url"], json=graph_json)

        emoticons_fig = build_emoticons_figure(emoticons, time_step)
        if emoticons_fig is not None:
            graph_json = json.dumps(emoticons_fig, cls=plotly.utils.PlotlyJSONEncoder)
            graphs[f"graph{i:02d}_2"] = dict(url=meta["url"], json=graph_json)

    if len(video_hashes) > 1 and combined_messages_df is not None:
        messages_fig = build_messages_figure(combined_messages_df, rolling_windows, time_step)
        graph_json = json.dumps(messages_fig, cls=plotly.utils.PlotlyJSONEncoder)
        graphs[f"graph{0:02d}_1"] = dict(caption='Combined stream stats', json=graph_json)

    if len(video_hashes) > 1:
        emoticons_fig = build_emoticons_figure(combined_emoticons, time_step)
        if emoticons_fig is not None:
            graph_json = json.dumps(emoticons_fig, cls=plotly.utils.PlotlyJSONEncoder)
            graphs[f"graph{0:02d}_2"] = dict(caption='Combined stream stats', json=graph_json)

    return render_template("graph.html", graphs=graphs)
