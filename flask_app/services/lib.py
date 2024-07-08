from datetime import timedelta, datetime
from hashlib import md5
from typing import TypeVar
from urllib.parse import urlparse

import pandas as pd
import plotly.graph_objects as go

IntervalWindow = TypeVar('IntervalWindow', str, int)


def url_to_hash(url: str) -> str:
    return md5(url.encode("utf-8")).hexdigest()


def hash_to_meta_file(video_hash: str) -> str:
    return f"data/{video_hash}_meta.json"


def hash_to_chat_file(video_hash: str) -> str:
    return f"data/{video_hash}_chat.jsonl"


def hash_to_timestamps_file(video_hash: str) -> str:
    return f"data/{video_hash}_timestamps.json"


# https://stackoverflow.com/questions/7160737/how-to-validate-a-url-in-python-malformed-or-not
def is_http_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc]) and (result.scheme == "http" or result.scheme == "https")
    except ValueError:
        return False


def build_dataframe_by_timestamp(data):
    df = pd.DataFrame(data, columns=["timestamp"])

    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, unit="us")
    # Assign a message count of 1 for each timestamp
    df["messages"] = 1

    df.set_index("timestamp", inplace=True)
    df.sort_index(inplace=True)

    return df


def normalize_timeline(df: pd.DataFrame, time_step: int) -> pd.DataFrame:
    # Resample the data into 5 second bins, filling in any missing seconds with 0
    return df.resample(f"{time_step}s").sum()


def make_buckets(df: pd.DataFrame, windows: list[IntervalWindow]) -> dict[IntervalWindow, pd.DataFrame]:
    result = {}
    for interval in windows:
        df_resampled = df.rolling(interval).sum()
        result[interval] = df_resampled

    return result


def build_scatter_fig(rolling_dataframes: dict[str, pd.DataFrame], time_step: int, figure_title: str, xaxis_title: str):
    fig = go.Figure()

    if not len(rolling_dataframes):
        return fig

    any_key = next(iter(rolling_dataframes))
    points_count = len(rolling_dataframes[any_key])
    start_timestamp: datetime = rolling_dataframes[any_key].index[0].to_pydatetime()

    for line_name, df in rolling_dataframes.items():
        df["timestamp"] = df.index
        df["timedelta"] = (df["timestamp"] - df["timestamp"].iloc[0]) // pd.Timedelta("1s")
        df.set_index("timedelta", inplace=True)

        fig.add_trace(go.Scatter(
            x=df.index.map(humanize_timedelta),
            y=df["messages"],
            mode="lines",
            name=line_name,
        ))

    xaxis_captions, xaxis_captions_detailed = build_timedelta_axis_captions(start_timestamp, points_count, time_step)

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

    return fig


def build_timedelta_axis_captions(start_timestamp: datetime, points_count: int, time_step: int):
    vals = []
    text = []

    for x in range(0, points_count, 3600 // time_step):
        short_caption = humanize_timedelta(x * time_step)
        vals.append(short_caption)

        point_timestamp = start_timestamp + timedelta(seconds=x * time_step)
        text.append(
            f"{short_caption}<br>" +
            f"{point_timestamp.strftime('%Y-%m-%d')}<br>" +
            f"{point_timestamp.strftime('%H:%M:%S')}"
        )

    return vals, text


def humanize_timedelta(total_seconds: int | timedelta) -> str:
    if isinstance(total_seconds, timedelta):
        total_seconds = total_seconds.total_seconds()

    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    return f'{int(hours):02}:{int(minutes):02}:{int(seconds):02}'
