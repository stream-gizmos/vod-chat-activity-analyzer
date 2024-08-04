from abc import ABC
from datetime import datetime
from importlib.metadata import entry_points

import pandas as pd
from plotly.graph_objs import Figure


class VodChatFigureUpdater(ABC):
    def __init__(
            self,
            messages_dfs: dict[str, pd.DataFrame],
            messages_time_step: int,
            emoticons_dfs: dict[str, pd.DataFrame],
            emoticons_time_step: int,
            vod_data: dict | None = None,
    ):
        self._messages_dfs: dict[str, pd.DataFrame] = messages_dfs
        self._messages_time_step: int = messages_time_step
        self._emoticons_dfs: dict[str, pd.DataFrame] = emoticons_dfs
        self._emoticons_time_step: int = emoticons_time_step
        self._vod_data: dict | None = vod_data

        self._is_appropriate: bool = True
        self._figure_rows: list[int] = []

        self._figure_total_rows: int = 0
        self._figure_subplot_heights: list[int] = None

        self._xaxis_start_timestamp: datetime | None = None
        self._xaxis_points_count: int | None = None
        self._xaxis_min_step: int | None = None

    @property
    def is_appropriate(self) -> bool:
        return self._is_appropriate

    @property
    def figure_total_rows(self) -> int:
        return self._figure_total_rows

    @property
    def figure_subplot_heights(self) -> list[int]:
        return self._figure_subplot_heights

    @property
    def xaxis_start_timestamp(self) -> datetime | None:
        return self._xaxis_start_timestamp

    @property
    def xaxis_points_count(self) -> int | None:
        return self._xaxis_points_count

    @property
    def xaxis_min_step(self) -> int | None:
        return self._xaxis_min_step

    def assign_figure_rows(self, row_numbers: list[int]) -> None:
        self._figure_rows = row_numbers

    def add_traces(self, fig: Figure, xaxis_title: str):
        if not self._is_appropriate:
            return

        return self._add_traces_impl(fig, xaxis_title)

    def post_traces(
            self,
            start_timestamp: datetime,
            points_count: int,
            min_time_step: int,
    ) -> tuple[datetime, int, int]:
        if not self._is_appropriate:
            return start_timestamp, points_count, min_time_step

        return self._post_traces_impl(start_timestamp, points_count, min_time_step)

    def _add_traces_impl(self, fig: Figure, xaxis_title: str):
        raise NotImplementedError

    def _post_traces_impl(
            self,
            start_timestamp: datetime,
            points_count: int,
            min_time_step: int,
    ) -> tuple[datetime, int, int]:
        return start_timestamp, points_count, min_time_step


def load_vod_chat_figure_extensions(
        messages_dfs: dict[str, pd.DataFrame],
        messages_time_step: int,
        emoticons_dfs: dict[str, pd.DataFrame],
        emoticons_time_step: int,
        vod_data: dict | None = None,
) -> list[VodChatFigureUpdater]:
    discovered_extensions = entry_points(group="chat_analyzer.v1.vod_chat.subplots", name="figure_updater")

    result: list[VodChatFigureUpdater] = []
    for extension in sorted(discovered_extensions):
        try:
            figure_updater_cls = extension.load()
            figure_updater: VodChatFigureUpdater = figure_updater_cls(
                messages_dfs,
                messages_time_step,
                emoticons_dfs,
                emoticons_time_step,
                vod_data,
            )

            if figure_updater:
                print(
                    f"Successfully loaded VOD-chat figure updater '{figure_updater.__name__}' from '{extension.module}' extension",
                    flush=True,
                )
        except Exception:
            print(f"Failed to load a VOD-chat figure updater from '{extension.module}' extension", flush=True)
            raise

    return result
