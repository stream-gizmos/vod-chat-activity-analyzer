import json
import os
from datetime import timedelta, datetime
from hashlib import md5
from itertools import islice
from urllib.parse import parse_qs, urlparse

import pandas as pd
import plotly.graph_objects as go
from plotly.graph_objs import Figure
from plotly.subplots import make_subplots

from flask_app.services.utils import (
    IntervalWindow,
    humanize_timedelta,
    normalize_timeline,
    sort_dict,
    sort_dict_items,
)

ANY_EMOTE = 'ANY EMOTE'


def url_to_hash(url: str) -> str:
    return md5(url.encode("utf-8")).hexdigest()


def hash_to_meta_file(video_hash: str) -> str:
    return f"data/{video_hash}_meta.json"


def hash_to_chat_file(video_hash: str) -> str:
    return f"data/{video_hash}_chat.jsonl"


def hash_to_timestamps_file(video_hash: str) -> str:
    return f"data/{video_hash}_timestamps.json"


def hash_to_emoticons_file(video_hash: str) -> str:
    return f"data/{video_hash}_emoticons.json"


def parse_vod_url(url: str) -> dict:
    parts = urlparse(url)
    qs = parse_qs(parts.query)

    platform = None
    vod_id = None
    if parts.hostname == "www.twitch.tv" or parts.hostname == "twitch.tv":
        platform = "twitch"

        if parts.path.startswith("/videos/"):
            vod_id = parts.path[8:]

    if parts.hostname == "www.youtube.com" or parts.hostname == "youtube.com":
        platform = "youtube"
        vod_id = qs.get("v", [])
        vod_id = vod_id[0] if len(vod_id) else None
    if parts.hostname == "youtu.be":
        platform = "youtube"
        vod_id = parts.path

    return {
        "url": url,
        "platform": platform,
        "vod_id": vod_id,
    }


def truncate_last_second_messages(chat_file_path) -> int | None:
    """
    Remove all messages from the tail of the JSONL file whose have the same second, then return this second value.
    """
    # Inspired by https://stackoverflow.com/a/54278929/3155344
    with open(chat_file_path, "ab+") as fp:
        def seek_line_back(count: int = 1) -> int:
            while count > 0:
                fp.seek(-2, os.SEEK_CUR)
                while fp.read(1) != b'\n':
                    pos = fp.seek(-2, os.SEEK_CUR)
                    if pos == 0:
                        return pos

                count -= 1

            return fp.tell()

        def read_current_line_json_attr(attr: str):
            line = fp.readline()
            line_json = json.loads(line)
            return line_json[attr]

        try:  # catch OSError in case of a one line file
            seek_line_back(1)
        except OSError as e:
            return None

        last_line_seconds = int(read_current_line_json_attr("time_in_seconds"))

        while True:
            pos = seek_line_back(2)
            line_seconds = int(read_current_line_json_attr("time_in_seconds"))

            if line_seconds != last_line_seconds:
                # Truncate to the pos because we have moved after the readline().
                fp.truncate(fp.tell())
                return last_line_seconds

            if pos == 0:
                # Truncate to the file beginning because the first line is also at this second.
                fp.truncate(0)
                return last_line_seconds


def build_dataframe_by_timestamp(data: list[int]) -> pd.DataFrame:
    df = pd.DataFrame(data, columns=["timestamp"])

    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, unit="us")
    # Assign a message count of 1 for each timestamp
    df["messages"] = 1

    df.set_index("timestamp", inplace=True)
    df.sort_index(inplace=True)

    return df


def get_custom_emoticons() -> set[str]:
    try:
        with open("emoticons.txt", "r") as fp:
            emoticons = [line.rstrip() for line in fp]
    except FileNotFoundError:
        emoticons = []

    emoticons = filter(None, emoticons)
    emoticons = map(lambda x: x.strip(), emoticons)
    emoticons = filter(lambda x: x[:2] != "# ", emoticons)

    return set(emoticons)


def mine_emoticons(message: str, platform_emotes: list[dict], custom_emoticons: set[str]) -> set[str]:
    emoticons = list(map(lambda x: x["name"], platform_emotes)) + list(custom_emoticons)

    # TODO Use YouTube's "shortcuts" for aliases of an emote

    return {word for word in message.split(" ") if word in emoticons}


def count_emoticons_top(
        emoticons_timestamps: dict[str, list[int]],
        top_size: int | None = 5,
        min_occurrences: int | None = 5,
) -> dict[str, int]:
    result = {k: len(timestamps) for k, timestamps in emoticons_timestamps.items()}

    result = sort_dict(result, values_key=lambda x: x[0], values_reverse=True)

    if min_occurrences is not None:
        result = {k: v for k, v in result.items() if v >= min_occurrences}

    if top_size is not None:
        result = {k: v for k, v in islice(result.items(), top_size)}

    result = {ANY_EMOTE: sum(result.values()), **result}

    return result


def build_emoticons_dataframes(
        emoticons_timestamps: dict[str, list[int]],
        time_step: int,
        top_size: int | None = 5,
        min_occurrences: int | None = 5,
        name_filter: list[str] | None = None,
) -> dict[str, pd.DataFrame]:
    if not len(emoticons_timestamps):
        return {}

    if name_filter is None:
        name_filter = []

    buffer = {k: v for k, v in emoticons_timestamps.items()}

    # Count all emotes
    buffer[ANY_EMOTE] = [ts for emote_times in buffer.values() for ts in emote_times]
    buffer[ANY_EMOTE] = sorted(buffer[ANY_EMOTE])

    # Discard rare emotes
    if min_occurrences is not None:
        buffer = {k: v for k, v in buffer.items() if len(v) >= min_occurrences}
    # Filter out by emote name
    if len(name_filter):
        buffer = {k: v for k, v in buffer.items() if k in name_filter}
    # Sort by frequency
    buffer = sort_dict_items(buffer, key=lambda x: len(x[1]), reverse=True)

    result = {}
    for emote, timestamps in buffer.items():
        emote_df = build_dataframe_by_timestamp(timestamps)
        emote_df = normalize_timeline(emote_df, time_step)

        if len(emote_df) > 0:
            result[emote] = emote_df

    # Get N-top emotes
    if top_size is not None:
        result = {k: v for k, v in islice(result.items(), top_size)}

    return result


def build_multiplot_figure(
        messages_dfs: dict[IntervalWindow, pd.DataFrame],
        messages_time_step: int,
        emoticons_dfs: dict[str, pd.DataFrame],
        emoticons_time_step: int,
        xaxis_title: str,
) -> Figure:
    messages_row = 1
    emoticons_row = 2 if len(emoticons_dfs) else 0
    total_rows = max(messages_row, emoticons_row)

    total_height, row_heights = _calculate_chart_heights(emoticons_row > 0)

    fig = make_subplots(
        rows=total_rows,
        cols=1,
        shared_xaxes=True,
        row_heights=row_heights,
        vertical_spacing=.02,
    )
    fig.update_xaxes(rangeslider=dict(visible=True, thickness=.1))

    append_messages_traces(fig, messages_dfs, row=messages_row, col=1, legend="legend1")
    fig.update_yaxes(row=messages_row, title="Messages")

    if emoticons_row > 0:
        append_emoticons_traces(fig, emoticons_dfs, emoticons_time_step, row=emoticons_row, col=1, legend="legend2")
        fig.update_yaxes(row=emoticons_row, title="Emoticons")
        fig.update_xaxes(row=emoticons_row, title=xaxis_title)
    else:
        fig.update_xaxes(row=messages_row, title=xaxis_title)

    any_df_key = next(iter(messages_dfs))
    any_df = messages_dfs[any_df_key]
    start_timestamp: datetime = any_df["timestamp"][0].to_pydatetime()
    points_count = len(any_df)
    min_time_step = min(messages_time_step, emoticons_time_step)

    _multiplot_figure_layout(
        fig,
        height=total_height,
        start_timestamp=start_timestamp,
        points_count=points_count,
        time_step=min_time_step,
    )

    return fig


def _calculate_chart_heights(with_emoticons_chart: bool) -> tuple[int, list[float]]:
    subplot_heights = [450]

    if with_emoticons_chart:
        subplot_heights.append(180)
        subplot_heights[0] -= subplot_heights[1]

    total_height = sum(subplot_heights)
    height_fractions = list(map(lambda x: x / total_height, subplot_heights))

    return total_height, height_fractions


def append_messages_traces(
        fig: Figure,
        messages_dfs: dict[IntervalWindow, pd.DataFrame],
        *,
        row: str | int | None = None,
        col: str | int | None = None,
        showlegend: bool = True,
        legend: str | None = None,
) -> None:
    for line_name, df in messages_dfs.items():
        df["timestamp"] = df.index
        df["timedelta"] = (df["timestamp"] - df["timestamp"].iloc[0]) // pd.Timedelta("1s")
        df.set_index("timedelta", inplace=True)

        trace = go.Scatter(
            name=line_name,
            x=df.index,
            y=df["messages"],
            mode="lines",
            showlegend=showlegend,
            legend=legend,
        )

        fig.add_trace(trace, row=row, col=col)


def append_emoticons_traces(
        fig: Figure,
        emoticons_dfs: dict[str, pd.DataFrame],
        time_step: int,
        *,
        row: str | int | None = None,
        col: str | int | None = None,
        showlegend: bool = True,
        legend: str | None = None,
) -> None:
    if not len(emoticons_dfs):
        return

    for line_name, df in emoticons_dfs.items():
        df["timestamp"] = df.index
        df["timedelta"] = (df["timestamp"] - df["timestamp"].iloc[0]) // pd.Timedelta("1s")
        df.set_index("timedelta", inplace=True)

        trace = go.Bar(
            name=line_name,
            x=df.index,
            y=df["messages"],
            width=time_step,
            offset=0,
            showlegend=showlegend,
            legend=legend,
        )

        if len(emoticons_dfs) > 1 and line_name == ANY_EMOTE:
            trace.update(dict(visible="legendonly"))

        fig.add_trace(trace, row=row, col=col)


def _multiplot_figure_layout(
        fig: Figure,
        *,
        height: int | None = None,
        start_timestamp: datetime,
        points_count: int,
        time_step: int,
) -> None:
    # Link all traces to one single X axis.
    total_yaxes = len(list(fig.select_yaxes()))
    fig.update_traces(xaxis=f"x{total_yaxes}")

    fig.update_layout(
        autosize=True,
        height=height,
        modebar=dict(orientation="v"),
        margin=dict(t=0, b=0, l=0, r=130),
        hoversubplots="axis",
        hovermode="x unified",
        barmode="stack",
    )

    xaxis_aliases = _build_time_axis_aliases(start_timestamp, points_count, time_step)

    fig.update_xaxes(
        type="linear",
        minallowed=-time_step,
        maxallowed=points_count * time_step,

        tickmode="linear",
        tick0=0,
        dtick=3600,
        labelalias=xaxis_aliases,
        tickformat="d",
        showgrid=True,

        tickfont_size=11,
        ticklabelposition="outside right",
        autotickangles=[0, 60, 90],

        range=[0, min(3600 * 3, points_count * time_step)],
    )

    fig.update_yaxes(
        minallowed=0,
        fixedrange=True,
    )

    separate_subplot_legends(fig)


def separate_subplot_legends(fig: Figure):
    """
    Uncluster legends of traces of each shape.
    https://community.plotly.com/t/plotly-subplots-with-individual-legends/1754/25
    """
    fig.update_layout(showlegend=True)

    for l, yaxis in enumerate(fig.select_yaxes(), 1):
        fig.update_layout({
            f"legend{l}": dict(y=yaxis.domain[1], yanchor="top"),
        })


def _build_time_axis_aliases(
        start_timestamp: datetime,
        points_count: int,
        time_step: int,
) -> dict[int, str]:
    result = {}
    for seconds in range(0, points_count * time_step, time_step):
        text = short_caption = humanize_timedelta(seconds)

        if seconds % 3600 == 0:
            point_timestamp = start_timestamp + timedelta(seconds=seconds)
            text = (
                    f"{short_caption}<br>" +
                    f"{point_timestamp.strftime('%Y-%m-%d')}<br>" +
                    f"{point_timestamp.strftime('%H:%M:%S')}"
            )

        result[seconds] = text

    return result
