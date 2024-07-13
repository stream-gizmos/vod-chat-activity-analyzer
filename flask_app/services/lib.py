import json
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


def mine_emoticons(message: str, platform_emotes: list[dict], custom_emoticons: set[str]) -> set:
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


def build_messages_figure(df: pd.DataFrame, rolling_windows: list[IntervalWindow], time_step: int) -> Figure:
    df = normalize_timeline(df, time_step)
    rolling_dataframes = make_buckets(df, rolling_windows)

    fig = build_scatter_figure(rolling_dataframes, time_step, "Number of messages", "Video time (in minutes)")

    return fig


def build_emoticons_figure(
        emoticons_timestamps: dict[str, list[int]],
        time_step: int,
        time_multiplier: int,
) -> Figure:
    emoticons_df = build_emoticons_dataframes(emoticons_timestamps, time_step * time_multiplier, top_size=8)
    emoticons_df = {k: normalize_timeline(v, time_step) for k, v in emoticons_df.items()}

    fig = build_bar_figure(
        emoticons_df,
        time_step * time_multiplier,
        "Number of emoticons",
        "Video time (in minutes)",
    )

    if len(emoticons_df) > 1:
        fig.update_traces(dict(visible="legendonly"), dict(name=ANY_EMOTE))

    return fig


def build_scatter_figure(
        dfs: dict[str, pd.DataFrame],
        time_step: int,
        figure_title: str,
        xaxis_title: str,
) -> Figure:
    fig = go.Figure()

    for line_name, df in dfs.items():
        df["timestamp"] = df.index
        df["timedelta"] = (df["timestamp"] - df["timestamp"].iloc[0]) // pd.Timedelta("1s")
        df.set_index("timedelta", inplace=True)

        fig.add_trace(go.Scatter(
            name=line_name,
            x=df.index.map(_humanize_timedelta),
            y=df["messages"],
            mode="lines",
        ))

    _standard_figure_layout(fig, dfs, time_step, figure_title, xaxis_title)

    return fig


def build_bar_figure(
        dfs: dict[str, pd.DataFrame],
        time_step: int,
        figure_title: str,
        xaxis_title: str,
) -> Figure:
    fig = go.Figure()

    for line_name, df in dfs.items():
        df["timestamp"] = df.index
        df["timedelta"] = (df["timestamp"] - df["timestamp"].iloc[0]) // pd.Timedelta("1s")
        df.set_index("timedelta", inplace=True)

        fig.add_trace(go.Bar(
            name=line_name,
            x=df.index.map(_humanize_timedelta),
            y=df["messages"],
        ))

    _standard_figure_layout(fig, dfs, time_step, figure_title, xaxis_title)
    fig.update_layout(barmode="stack")

    return fig


def build_multiplot_figure(
        messages_dfs: dict[IntervalWindow, pd.DataFrame],
        emoticons_dfs: dict[str, pd.DataFrame],
        time_step: int,
        emoticons_time_multiplier: int,
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
        vertical_spacing=.2,
    )

    append_messages_traces(fig, messages_dfs, row=messages_row, col=1)
    fig.update_yaxes(row=messages_row, title="Messages")
    fig.update_xaxes(row=messages_row, rangeslider=dict(visible=True, thickness=.1))

    if emoticons_row > 0:
        append_emoticons_traces(fig, emoticons_dfs, emoticons_time_multiplier, row=emoticons_row, col=1)
        fig.update_yaxes(row=emoticons_row, title="Emoticons")
        fig.update_xaxes(row=emoticons_row, title=xaxis_title)
    else:
        fig.update_xaxes(row=messages_row, title=xaxis_title)

    _multiplot_figure_layout(fig, messages_dfs, time_step)

    return fig


def append_messages_traces(
        fig: Figure,
        messages_dfs: dict[IntervalWindow, pd.DataFrame],
        row=None,
        col=None,
):
    for line_name, df in messages_dfs.items():
        df["timestamp"] = df.index
        df["timedelta"] = (df["timestamp"] - df["timestamp"].iloc[0]) // pd.Timedelta("1s")
        df.set_index("timedelta", inplace=True)

        trace = go.Scatter(
            name=line_name,
            x=df.index.map(_humanize_timedelta),
            y=df["messages"],
            mode="lines",
        )

        fig.add_trace(trace, row=row, col=col)


def append_emoticons_traces(
        fig: Figure,
        emoticons_dfs: dict[str, pd.DataFrame],
        time_multiplier: int,
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
            x=df.index.map(_humanize_timedelta),
            y=df["messages"],
            width=time_multiplier,
            offset=0,
        )

        if len(emoticons_dfs) > 1 and line_name == ANY_EMOTE:
            trace.update(dict(visible="legendonly"))

        fig.add_trace(trace, row=row, col=col)


def _standard_figure_layout(
        fig: Figure,
        rolling_dataframes: dict[str, pd.DataFrame],
        time_step: int,
        figure_title: str,
        xaxis_title: str,
) -> None:
    any_key = next(iter(rolling_dataframes))
    points_count = len(rolling_dataframes[any_key])
    start_timestamp: datetime = rolling_dataframes[any_key]["timestamp"][0].to_pydatetime()

    xaxis_captions, xaxis_captions_detailed = _build_timedelta_axis_captions(start_timestamp, points_count, time_step)

    fig.update_layout(
        title=figure_title,
        autosize=True,
        height=330,
        margin=dict(t=30, b=0, l=0, r=0, pad=5),
        hovermode="x unified",
        xaxis_title=xaxis_title,
        xaxis=dict(
            type='category',

            tickmode='array',
            tickvals=xaxis_captions,
            ticktext=xaxis_captions_detailed,
            tickfont_size=11,
            ticklabelposition="outside right",
            autotickangles=[0, 60, 90],

            range=[0, min((3600 // time_step) * 3, points_count)],
            rangeslider_visible=True,
        ),
        yaxis=dict(
            fixedrange=True,
        ),
    )


def _multiplot_figure_layout(
        fig: Figure,
        rolling_dataframes: dict[str, pd.DataFrame],
        time_step: int,
) -> None:
    any_key = next(iter(rolling_dataframes))
    points_count = len(rolling_dataframes[any_key])
    start_timestamp: datetime = rolling_dataframes[any_key]["timestamp"][0].to_pydatetime()

    xaxis_captions, xaxis_captions_detailed = _build_timedelta_axis_captions(start_timestamp, points_count, time_step)

    fig.update_layout(
        autosize=True,
        modebar=dict(orientation="v"),
        margin=dict(t=0, b=0, l=0, r=130),
        hovermode="x unified",
        barmode="stack",
    )

    fig.update_yaxes(fixedrange=True)

    fig.update_xaxes(
        type='category',

        tickmode='array',
        tickvals=xaxis_captions,
        ticktext=xaxis_captions_detailed,
        tickfont_size=11,
        ticklabelposition="outside right",
        autotickangles=[0, 60, 90],

        range=[0, min((3600 // time_step) * 3, points_count)],
    )

    # Uncluster legends of traces of each shape.
    # https://community.plotly.com/t/plotly-subplots-with-individual-legends/1754/25
    for l, yaxis in enumerate(fig.select_yaxes(), 1):
        legend_name = f"legend{l}"
        fig.update_layout({legend_name: dict(y=yaxis.domain[1], yanchor="top")}, showlegend=True)
        fig.update_traces(row=l, legend=legend_name)


def _build_timedelta_axis_captions(start_timestamp: datetime, points_count: int, time_step: int):
    vals = []
    text = []

    for x in range(0, points_count, 3600 // time_step):
        short_caption = _humanize_timedelta(x * time_step)
        vals.append(short_caption)

        point_timestamp = start_timestamp + timedelta(seconds=x * time_step)
        text.append(
            f"{short_caption}<br>" +
            f"{point_timestamp.strftime('%Y-%m-%d')}<br>" +
            f"{point_timestamp.strftime('%H:%M:%S')}"
        )

    return vals, text


def _humanize_timedelta(total_seconds: int | timedelta) -> str:
    if isinstance(total_seconds, timedelta):
        total_seconds = total_seconds.total_seconds()

    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    return f'{int(hours):02}:{int(minutes):02}:{int(seconds):02}'
