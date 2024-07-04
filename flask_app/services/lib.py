from hashlib import md5
from urllib.parse import urlparse

import pandas as pd
import plotly.graph_objects as go


def url_to_hash(url: str) -> str:
    return md5(url.encode("utf-8")).hexdigest()


def hash_to_meta_file(video_hash: str) -> str:
    return f"data/{video_hash}_meta.json"


def hash_to_chat_file(video_hash: str) -> str:
    return f"data/{video_hash}_chat.jsonl"


def hash_to_times_file(video_hash: str) -> str:
    return f"data/{video_hash}_times.json"


# https://stackoverflow.com/questions/7160737/how-to-validate-a-url-in-python-malformed-or-not
def is_http_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc]) and (result.scheme == "http" or result.scheme == "https")
    except ValueError:
        return False


def times_data_to_rolling_sums(data, intervals):
    df = pd.DataFrame(data, columns=["timestamp"])

    # Convert timestamp to timedelta
    df["timestamp"] = pd.to_timedelta(df["timestamp"], unit="s")
    # Assign a message count of 1 for each timestamp
    df["messages"] = 1

    # Resample the data into 5 second bins, filling in any missing seconds with 0
    df.set_index("timestamp", inplace=True)
    df = df.resample("5S").sum()

    for interval in intervals:
        df_resampled = df.rolling(interval).sum()

        yield interval, df_resampled


def build_scatter_fig(interval_dataframes: dict, figure_title):
    fig = go.Figure()

    for interval, interval_df in interval_dataframes.items():
        fig.add_trace(go.Scatter(
            x=interval_df.index.total_seconds() / 60,  # convert seconds to minutes
            y=interval_df["messages"],
            mode="lines",
            name=interval,
        ))

    fig.update_layout(
        title=figure_title,
        autosize=True,
        height=300,
        margin=dict(t=30, b=0, l=0, r=0, pad=5),
        hovermode="x",
        xaxis_title="Time (in minutes)",
        xaxis=dict(
            tickmode="linear",
            tick0=0,
            dtick=30,  # change interval to 30 minutes
        ),
    )

    return fig
