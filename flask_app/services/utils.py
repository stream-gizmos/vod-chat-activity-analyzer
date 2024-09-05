import contextlib
import json
import socket
from collections import defaultdict
from contextlib import closing
from datetime import timedelta
from typing import Callable, TypeVar
from urllib.parse import urlparse

import pandas as pd
from filelock import FileLock

IntervalWindow = TypeVar('IntervalWindow', str, int)
PlainType = TypeVar('PlainType', str, int, float, bool)


def read_json_file(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as fp:
            return json.load(fp)
    except FileNotFoundError:
        return None


def sort_dict_items(result: dict, **kwargs) -> dict:
    return dict(sorted(result.items(), **kwargs))


def sort_dict(
        top: dict[str, PlainType],
        *,
        keys_key: Callable[[str], any] | None = None,
        keys_reverse: bool | None = False,
        values_key: Callable[[tuple[PlainType, str]], any] | None = None,
        values_reverse: bool | None = False,
        # **kwargs,
) -> dict[str, PlainType]:
    if keys_reverse is values_reverse is None:
        raise Exception("At least one sort criteria must be specified")

    group_by_count = defaultdict(list)
    for k, v in top.items():
        group_by_count[v].append(k)

    if values_reverse is not None:
        group_by_count = sort_dict_items(group_by_count, key=values_key, reverse=values_reverse)

    if keys_reverse is not None:
        group_by_count = {k: sorted(v, key=keys_key, reverse=keys_reverse) for k, v in group_by_count.items()}

    return {
        emote: count
        for count, emotes in group_by_count.items()
        for emote in emotes
    }


# https://stackoverflow.com/questions/7160737/how-to-validate-a-url-in-python-malformed-or-not
def is_http_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc]) and (result.scheme == "http" or result.scheme == "https")
    except ValueError:
        return False


def find_free_port() -> int:
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(("", 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]


@contextlib.contextmanager
def lock_file_path(path: str):
    lock = FileLock(f"{path}.lock", timeout=1)

    with lock:
        yield lock


def humanize_timedelta(total_seconds: int | timedelta) -> str:
    if isinstance(total_seconds, timedelta):
        total_seconds = total_seconds.total_seconds()

    sign = '-' if total_seconds < 0 else ''
    hours, remainder = divmod(abs(total_seconds), 3600)
    minutes, seconds = divmod(remainder, 60)

    return f'{sign}{int(hours):02}:{int(minutes):02}:{int(seconds):02}'


def normalize_timeline(df: pd.DataFrame, time_step: int) -> pd.DataFrame:
    # Resample the data into N second bins, filling in any missing seconds with 0
    return df.resample(f"{time_step}s").sum()


def make_buckets(df: pd.DataFrame, windows: list[IntervalWindow]) -> dict[IntervalWindow, pd.DataFrame]:
    result = {}
    for interval in windows:
        df_resampled = df.rolling(interval).sum().astype(int)
        result[interval] = df_resampled

    return result
