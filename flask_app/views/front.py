import json
import os

import pandas as pd
import plotly
from chat_downloader import ChatDownloader
from flask import Blueprint, render_template, request, redirect, url_for

from flask_app.services.lib import (
    build_dataframe_by_timestamp,
    build_emoticons_dataframes,
    build_multiplot_figure,
    count_emoticons_top,
    get_custom_emoticons,
    hash_to_chat_file,
    hash_to_emoticons_file,
    hash_to_meta_file,
    hash_to_timestamps_file,
    mine_emoticons,
    normalize_timeline,
    parse_vod_url,
    url_to_hash,
    truncate_last_second_messages,
)
from flask_app.services.utils import is_http_url, make_buckets, read_json_file

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

        chat_file_path = hash_to_chat_file(video_hash)

        if os.path.isfile(chat_file_path):
            truncated_seconds = truncate_last_second_messages(chat_file_path)
        else:
            truncated_seconds = None

        chat = ChatDownloader().get_chat(url, output=chat_file_path, overwrite=False, start_time=truncated_seconds)
        for _ in chat: pass

        messages_timestamps = []
        emoticons_timestamps: dict[str, list[int]] = {}
        with open(chat_file_path, "r") as fp:
            for line in fp:
                message = json.loads(line)

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

    messages_time_step = 15  # In seconds
    rolling_windows = [f"{1 * messages_time_step}s", f"{4 * messages_time_step}s", f"{20 * messages_time_step}s"]
    emoticons_time_step = messages_time_step * 4
    emoticons_min_occurrences = 10
    emoticons_top_size = 6

    get_emoticons_filter = lambda x: request.args.getlist(f"emoticons[{x}][]")

    combined_messages_df: pd.DataFrame | None = None
    combined_emoticons: dict[str, list[int]] = {}

    graphs = {}
    for i, video_hash in enumerate(video_hashes, start=1):
        emoticons_filter = get_emoticons_filter(video_hash)

        meta = read_json_file(hash_to_meta_file(video_hash)) or {}

        messages = read_json_file(hash_to_timestamps_file(video_hash)) or []
        messages_df = build_dataframe_by_timestamp(messages)
        messages_df = normalize_timeline(messages_df, messages_time_step)
        rolling_messages_dfs = make_buckets(messages_df, rolling_windows)

        emoticons: dict[str, list[int]] = read_json_file(hash_to_emoticons_file(video_hash)) or {}
        emoticons_top = count_emoticons_top(emoticons, top_size=None, min_occurrences=emoticons_min_occurrences)
        emoticons_dfs = build_emoticons_dataframes(
            emoticons,
            emoticons_time_step,
            top_size=emoticons_top_size,
            min_occurrences=emoticons_min_occurrences,
            name_filter=emoticons_filter,
        )

        fig = build_multiplot_figure(
            rolling_messages_dfs,
            messages_time_step,
            emoticons_dfs,
            emoticons_time_step,
            "Video time (in minutes)",
        )

        vod_url_data = parse_vod_url(meta["url"])
        graph_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
        graphs[f"vod{i:02d}"] = dict(
            hash=video_hash,
            plotly=graph_json,
            emoticons_top=list(emoticons_top.items()),
            selected_emoticons=list(emoticons_dfs.keys()),
            **vod_url_data,
        )

        combined_messages_df = messages_df.copy() if combined_messages_df is None \
            else combined_messages_df.add(messages_df, fill_value=0)

        for emote, timestamps in emoticons.items():
            if emote not in combined_emoticons:
                combined_emoticons[emote] = timestamps
            else:
                combined_emoticons[emote].extend(timestamps)

    if len(video_hashes) > 1 and combined_messages_df is not None:
        video_hash = "combined"
        emoticons_filter = get_emoticons_filter(video_hash)

        messages_df = normalize_timeline(combined_messages_df, messages_time_step)
        rolling_messages_dfs = make_buckets(messages_df, rolling_windows)

        emoticons_top = count_emoticons_top(
            combined_emoticons,
            top_size=None,
            min_occurrences=emoticons_min_occurrences,
        )
        emoticons_dfs = build_emoticons_dataframes(
            combined_emoticons,
            emoticons_time_step,
            top_size=emoticons_top_size,
            min_occurrences=emoticons_min_occurrences,
            name_filter=emoticons_filter,
        )

        fig = build_multiplot_figure(
            rolling_messages_dfs,
            messages_time_step,
            emoticons_dfs,
            emoticons_time_step,
            "Stream time (in minutes)",
        )

        graph_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
        graphs[f"vod{0:02d}"] = dict(
            hash=video_hash,
            plotly=graph_json,
            emoticons_top=list(emoticons_top.items()),
            selected_emoticons=list(emoticons_dfs.keys()),
            caption="Combined stream stats",
        )

    return render_template("graph.html", graphs=graphs)
