import json
import socket
from contextlib import closing
from datetime import timedelta, datetime
from hashlib import md5
from itertools import islice
from typing import TypeVar
from urllib.parse import urlparse

import pandas as pd
import plotly.graph_objects as go
from plotly.graph_objs import Figure
from plotly.subplots import make_subplots

IntervalWindow = TypeVar('IntervalWindow', str, int)

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


def find_free_port() -> int:
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(("", 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]


# https://stackoverflow.com/questions/7160737/how-to-validate-a-url-in-python-malformed-or-not
def is_http_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc]) and (result.scheme == "http" or result.scheme == "https")
    except ValueError:
        return False


def read_json_file(file_path):
    try:
        with open(file_path, "r") as fp:
            return json.load(fp)
    except FileNotFoundError:
        return None


def build_dataframe_by_timestamp(data: list[int]) -> pd.DataFrame:
    df = pd.DataFrame(data, columns=["timestamp"])

    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, unit="us")
    # Assign a message count of 1 for each timestamp
    df["messages"] = 1

    df.set_index("timestamp", inplace=True)
    df.sort_index(inplace=True)

    return df


def normalize_timeline(df: pd.DataFrame, time_step: int) -> pd.DataFrame:
    # Resample the data into N second bins, filling in any missing seconds with 0
    return df.resample(f"{time_step}s").sum()


def make_buckets(df: pd.DataFrame, windows: list[IntervalWindow]) -> dict[IntervalWindow, pd.DataFrame]:
    result = {}
    for interval in windows:
        df_resampled = df.rolling(interval).sum()
        result[interval] = df_resampled

    return result


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


def build_emoticons_dataframes(
        emoticons_timestamps: dict[str, list[int]],
        time_step: int,
        top_size: int = 5,
        min_occurrences: int = 5,
) -> dict[str, pd.DataFrame]:
    if not len(emoticons_timestamps):
        return {}

    buffer = {k: v for k, v in emoticons_timestamps.items()}

    # Count all emotes
    buffer[ANY_EMOTE] = [ts for emote_times in buffer.values() for ts in emote_times]
    buffer[ANY_EMOTE] = sorted(buffer[ANY_EMOTE])

    # Discard rare emotes
    buffer = {k: v for k, v in buffer.items() if len(v) >= min_occurrences}
    # Sort by frequency
    buffer = dict(reversed(sorted(buffer.items(), key=lambda x: len(x[1]))))

    result = {}
    for emote, timestamps in buffer.items():
        emote_df = build_dataframe_by_timestamp(timestamps)
        emote_df = normalize_timeline(emote_df, time_step)
        emote_df = emote_df[emote_df["messages"] >= min_occurrences]

        if len(emote_df) > 0:
            result[emote] = emote_df

    # Get N-top emotes
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

    row_heights = [.6, .4] if emoticons_row > 0 else None

    fig = make_subplots(
        rows=max(messages_row, emoticons_row),
        cols=1,
        shared_xaxes=True,
        row_heights=row_heights,
        vertical_spacing=.02,
    )

    append_messages_traces(fig, messages_dfs, row=messages_row, col=1)
    fig.update_yaxes(row=messages_row, title="Messages")
    fig.update_xaxes(rangeslider=dict(visible=True, thickness=.1))

    if emoticons_row > 0:
        append_emoticons_traces(fig, emoticons_dfs, emoticons_time_step, row=emoticons_row, col=1)
        fig.update_yaxes(row=emoticons_row, title="Emoticons")
        fig.update_xaxes(row=emoticons_row, title=xaxis_title)
    else:
        fig.update_xaxes(row=messages_row, title=xaxis_title)

    any_df_key = next(iter(messages_dfs))
    any_df = messages_dfs[any_df_key]
    start_timestamp: datetime = any_df["timestamp"][0].to_pydatetime()
    points_count = len(any_df)
    min_time_step = min(messages_time_step, emoticons_time_step)

    _multiplot_figure_layout(fig, start_timestamp, points_count, min_time_step)

    return fig


def append_messages_traces(
        fig: Figure,
        messages_dfs: dict[IntervalWindow, pd.DataFrame],
        row=None,
        col=None,
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
        )

        fig.add_trace(trace, row=row, col=col)


def append_emoticons_traces(
        fig: Figure,
        emoticons_dfs: dict[str, pd.DataFrame],
        time_step: int,
        row=None,
        col=None,
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
        )

        if len(emoticons_dfs) > 1 and line_name == ANY_EMOTE:
            trace.update(dict(visible="legendonly"))

        fig.add_trace(trace, row=row, col=col)


def _multiplot_figure_layout(
        fig: Figure,
        start_timestamp: datetime,
        points_count: int,
        time_step: int,
) -> None:
    # Link all traces to one single X axis.
    total_yaxes = len(list(fig.select_yaxes()))
    fig.update_traces(xaxis=f"x{total_yaxes}")

    fig.update_layout(
        autosize=True,
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

    # Uncluster legends of traces of each shape.
    # https://community.plotly.com/t/plotly-subplots-with-individual-legends/1754/25
    for l, yaxis in enumerate(fig.select_yaxes(), 1):
        legend_name = f"legend{l}"
        fig.update_layout({legend_name: dict(y=yaxis.domain[1], yanchor="top")}, showlegend=True)
        fig.update_traces(row=l, legend=legend_name)


def _build_time_axis_aliases(
        start_timestamp: datetime,
        points_count: int,
        time_step: int,
) -> dict[int, str]:
    result = {}
    for seconds in range(0, points_count * time_step, time_step):
        text = short_caption = _humanize_timedelta(seconds)

        if seconds % 3600 == 0:
            point_timestamp = start_timestamp + timedelta(seconds=seconds)
            text = (
                f"{short_caption}<br>" +
                f"{point_timestamp.strftime('%Y-%m-%d')}<br>" +
                f"{point_timestamp.strftime('%H:%M:%S')}"
            )

        result[seconds] = text

    return result


def _humanize_timedelta(total_seconds: int | timedelta) -> str:
    if isinstance(total_seconds, timedelta):
        total_seconds = total_seconds.total_seconds()

    sign = '-' if total_seconds < 0 else ''
    hours, remainder = divmod(abs(total_seconds), 3600)
    minutes, seconds = divmod(remainder, 60)

    return f'{sign}{int(hours):02}:{int(minutes):02}:{int(seconds):02}'
