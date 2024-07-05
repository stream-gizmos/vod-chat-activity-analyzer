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


def hash_to_times_file(video_hash: str) -> str:
    return f"data/{video_hash}_times.json"


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

    # Convert timestamp to time
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, unit="us")
    # Assign a message count of 1 for each timestamp
    df["messages"] = 1

    df.set_index("timestamp", inplace=True)
    df.sort_index(inplace=True)

    return df


def make_buckets(df: pd.DataFrame, intervals: list[IntervalWindow]) -> dict[IntervalWindow, pd.DataFrame]:
    # Resample the data into 5 second bins, filling in any missing seconds with 0
    df = df.resample("5S").sum()

    # Convert absolute time to duration from the video start
    df["time_in_seconds"] = df.index.to_series().sub(df.index[0])
    df.set_index("time_in_seconds", inplace=True)

    result = {}
    for interval in intervals:
        df_resampled = df.rolling(interval).sum()
        result[interval] = df_resampled

    return result


def build_scatter_fig(scatter_dataframes: dict, figure_title: str, xaxis_title: str):
    fig = go.Figure()

    for line_name, df in scatter_dataframes.items():
        fig.add_trace(go.Scatter(
            x=df.index.total_seconds() / 60,  # convert seconds to minutes
            y=df["messages"],
            mode="lines",
            name=line_name,
        ))

    fig.update_layout(
        title=figure_title,
        autosize=True,
        height=300,
        margin=dict(t=30, b=0, l=0, r=0, pad=5),
        hovermode="x",
        xaxis_title=xaxis_title,
        xaxis=dict(
            tickmode="linear",
            tick0=0,
            dtick=30,  # change interval to 30 minutes
        ),
    )

    return fig
