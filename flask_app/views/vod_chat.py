import json

import luigi
import pandas as pd
from flask import Blueprint, flash, render_template, redirect, request, url_for
from luigi.task import flatten, flatten_output

from flask_app.services.extension import load_vod_chat_figure_extensions
from flask_app.services.lib import (
    build_dataframe_by_timestamp,
    build_emoticons_dataframes,
    build_multiplot_figure,
    calc_spikes,
    count_emoticons_top,
    find_minimal_start_timestamp,
    hash_to_emoticons_file,
    hash_to_meta_file,
    hash_to_timestamps_file,
    normalize_timeline,
    parse_vod_url,
    url_to_hash,
)
from flask_app.services.utils import is_http_url, make_buckets, read_json_file
from flask_app.tasks.vod_chat import (
    CollectVodChatEmoticons,
    CollectVodChatTimestamps,
    DownloadVodChat,
    DumpVodChatMeta,
)

vod_chat_bp = Blueprint("vod_chat", __name__)


@vod_chat_bp.route("/")
def index():
    return render_template("vod_chat/index.html")


@vod_chat_bp.route("/start_download", methods=["POST"])
def start_download():
    urls = request.form.getlist("url[]")
    urls = map(str.strip, urls)
    urls = filter(None, urls)
    urls = filter(is_http_url, urls)
    urls = set(urls)

    if not len(urls):
        flash("Wrong URLs provided", "error")
        return redirect(url_for(".index"))

    tasks = []
    hashes = []
    for url in sorted(urls):
        video_hash = url_to_hash(url)
        hashes.append(video_hash)

        tasks.append(DumpVodChatMeta(url))

    luigi.build(tasks, workers=1)

    hashes_string = ",".join(hashes)

    return redirect(url_for(".display_graph", video_hashes=hashes_string))


@vod_chat_bp.route("/update_vod_chat/<video_hash>", methods=["POST"])
def update_vod_chat(video_hash):
    meta = read_json_file(hash_to_meta_file(video_hash)) or {}

    download_task = DownloadVodChat(url=meta["url"])
    download_task.move_output_for_update()

    tasks_to_cleanup = [
        CollectVodChatTimestamps(url=meta["url"]),
        CollectVodChatEmoticons(url=meta["url"]),
    ]
    outputs_to_cleanup = [flatten_output(task) for task in tasks_to_cleanup]
    outputs_to_cleanup = flatten(outputs_to_cleanup)

    for output in outputs_to_cleanup:
        if output.exists():
            output.remove()

    tasks = [
        download_task,
        CollectVodChatTimestamps(url=meta["url"]),
        CollectVodChatEmoticons(url=meta["url"]),
    ]

    luigi.build(tasks, workers=1)

    return json.dumps({'success': True}), 202, {"Content-Type": "application/json"}


@vod_chat_bp.route("/display_graph/<video_hashes>", methods=["GET"])
def display_graph(video_hashes):
    video_hashes = video_hashes.split(",")

    vods = {}
    for i, video_hash in enumerate(video_hashes, start=1):
        meta = read_json_file(hash_to_meta_file(video_hash)) or {}
        vod_data = parse_vod_url(meta["url"])

        vods[f"vod{i:02d}"] = dict(
            hash=video_hash,
            data_url=url_for(".calc_vod_graph", video_hash=video_hash),
            update_url=url_for(".update_vod_chat", video_hash=video_hash),
            **vod_data,
        )

    if len(video_hashes) > 1:
        vods[f"vod{0:02d}"] = dict(
            hash="combined",
            data_url=url_for(".calc_combined_vod_graph", video_hashes=",".join(video_hashes)),
            caption="Combined stats",
        )

    return render_template("vod_chat/graph.html", vods=vods)


@vod_chat_bp.route("/calc_vod_graph/<video_hash>", methods=["GET"])
def calc_vod_graph(video_hash):
    meta = read_json_file(hash_to_meta_file(video_hash)) or {}

    tasks = [
        CollectVodChatTimestamps(url=meta["url"]),
        CollectVodChatEmoticons(url=meta["url"]),
    ]

    if any(filter(lambda x: not x.complete(), tasks)):
        luigi.build(tasks, workers=1)
        return json.dumps({'success': True}), 202, {"Content-Type": "application/json"}

    messages_time_step = 15  # In seconds
    rolling_windows = [f"{1 * messages_time_step}s", f"{4 * messages_time_step}s", f"{20 * messages_time_step}s"]
    emoticons_time_step = messages_time_step * 4
    emoticons_min_occurrences = 10
    emoticons_top_size = 6

    emoticons_filter = request.args.getlist(f"emoticons[]")

    vod_data = parse_vod_url(meta["url"])

    messages: list[int] = read_json_file(hash_to_timestamps_file(video_hash)) or []
    emoticons: dict[str, list[int]] = read_json_file(hash_to_emoticons_file(video_hash)) or {}

    extensions = load_vod_chat_figure_extensions(messages, emoticons, vod_data)
    common_start_timestamp = find_minimal_start_timestamp(messages, extensions)

    messages_df = build_dataframe_by_timestamp(messages, [common_start_timestamp])
    messages_df = normalize_timeline(messages_df, messages_time_step)
    rolling_messages_dfs = make_buckets(messages_df, rolling_windows)
    rolling_messages_dfs["spikes"] = calc_spikes(messages_df, min_messages=5, min_spike_power=.4)

    emoticons_top = count_emoticons_top(emoticons, top_size=None, min_occurrences=emoticons_min_occurrences)
    emoticons_dfs = build_emoticons_dataframes(
        emoticons,
        emoticons_time_step,
        forced_start_timestamp=common_start_timestamp,
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
        extensions,
    )

    if _is_dark_theme_request():
        fig.update_layout(template="plotly_dark")

    return dict(
        plotly=json.loads(fig.to_json()),
        emoticons_top=list(emoticons_top.items()),
        selected_emoticons=list(emoticons_dfs.keys()),
        **vod_data,
    )


@vod_chat_bp.route("/calc_combined_vod_graph/<video_hashes>", methods=["GET"])
def calc_combined_vod_graph(video_hashes):
    video_hashes = video_hashes.split(",")

    if len(video_hashes) == 1:
        return {}

    tasks = []
    for video_hash in video_hashes:
        meta = read_json_file(hash_to_meta_file(video_hash)) or {}
        tasks.extend([
            CollectVodChatTimestamps(url=meta["url"]),
            CollectVodChatEmoticons(url=meta["url"]),
        ])

    if any(filter(lambda x: not x.complete(), tasks)):
        luigi.build(tasks, workers=1)
        return json.dumps({'success': True}), 202, {"Content-Type": "application/json"}

    messages_time_step = 15  # In seconds
    rolling_windows = [f"{1 * messages_time_step}s", f"{4 * messages_time_step}s", f"{20 * messages_time_step}s"]
    emoticons_time_step = messages_time_step * 4
    emoticons_min_occurrences = 10
    emoticons_top_size = 6

    combined_messages_df: pd.DataFrame | None = None
    combined_emoticons: dict[str, list[int]] = {}

    min_start_timestamp = None
    for video_hash in video_hashes:
        meta = read_json_file(hash_to_meta_file(video_hash)) or {}
        vod_data = parse_vod_url(meta["url"])

        messages: list[int] = read_json_file(hash_to_timestamps_file(video_hash)) or []
        emoticons: dict[str, list[int]] = read_json_file(hash_to_emoticons_file(video_hash)) or {}

        extensions = load_vod_chat_figure_extensions(messages, emoticons, vod_data)
        common_start_timestamp = find_minimal_start_timestamp(messages, extensions)
        min_start_timestamp = common_start_timestamp if min_start_timestamp is None \
            else min(min_start_timestamp, common_start_timestamp)

        messages_df = build_dataframe_by_timestamp(messages, [common_start_timestamp])
        messages_df = normalize_timeline(messages_df, messages_time_step)

        combined_messages_df = messages_df.copy() if combined_messages_df is None \
            else combined_messages_df.add(messages_df, fill_value=0)

        for emote, timestamps in emoticons.items():
            if emote not in combined_emoticons:
                combined_emoticons[emote] = timestamps
            else:
                combined_emoticons[emote].extend(timestamps)

    emoticons_filter = request.args.getlist(f"emoticons[]")

    messages_df = normalize_timeline(combined_messages_df, messages_time_step)
    rolling_messages_dfs = make_buckets(messages_df, rolling_windows)
    rolling_messages_dfs["spikes"] = calc_spikes(messages_df, min_messages=5, min_spike_power=.4)

    emoticons_top = count_emoticons_top(
        combined_emoticons,
        top_size=None,
        min_occurrences=emoticons_min_occurrences,
    )
    emoticons_dfs = build_emoticons_dataframes(
        combined_emoticons,
        emoticons_time_step,
        forced_start_timestamp=min_start_timestamp,
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

    if _is_dark_theme_request():
        fig.update_layout(template="plotly_dark")

    return dict(
        plotly=json.loads(fig.to_json()),
        emoticons_top=list(emoticons_top.items()),
        selected_emoticons=list(emoticons_dfs.keys()),
    )


def _is_dark_theme_request():
    return request.args.get("theme", "light") == "dark"
