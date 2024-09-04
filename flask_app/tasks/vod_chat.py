import json

import luigi
from chat_downloader import ChatDownloader
from luigi.format import UTF8

from flask_app.services.lib import (
    get_custom_emoticons,
    hash_to_chat_file,
    hash_to_emoticons_file,
    hash_to_meta_file,
    hash_to_timestamps_file,
    mine_emoticons,
    truncate_last_second_messages,
    url_to_hash,
)


class DumpVodChatMeta(luigi.Task):
    url = luigi.Parameter()

    def output(self) -> luigi.LocalTarget:
        url = str(self.url)
        video_hash = url_to_hash(url)

        return luigi.LocalTarget(hash_to_meta_file(video_hash), UTF8)

    def run(self):
        url = str(self.url)

        with self.output().open("w") as fp:
            data = {
                "url": url,
            }
            json.dump(data, fp, indent=2)


class DownloadVodChat(luigi.Task):
    url = luigi.Parameter()

    old_output = luigi.LocalTarget(format=UTF8, is_tmp=True)

    def move_output_for_update(self):
        if self.output().exists():
            self.output().move(self.old_output.path, True)

    def requires(self):
        return DumpVodChatMeta(self.url)

    def output(self) -> luigi.LocalTarget:
        url = str(self.url)
        video_hash = url_to_hash(url)

        return luigi.LocalTarget(hash_to_chat_file(video_hash), UTF8)

    def run(self):
        if self.old_output.exists():
            truncated_seconds = truncate_last_second_messages(self.old_output.path)
        else:
            truncated_seconds = None

        chat = ChatDownloader().get_chat(
            str(self.url),
            output=self.old_output.path,
            output_format="jsonl",
            overwrite=False,
            start_time=truncated_seconds,
        )
        for _ in chat: pass

        if self.old_output.exists():
            self.old_output.move(self.output().path, True)


class CollectVodChatTimestamps(luigi.Task):
    url = luigi.Parameter()

    def requires(self):
        return DownloadVodChat(self.url)

    def output(self) -> luigi.LocalTarget:
        url = str(self.url)
        video_hash = url_to_hash(url)

        return luigi.LocalTarget(hash_to_timestamps_file(video_hash), UTF8)

    def run(self):
        messages_timestamps = []
        with self.input().open("r") as fp:
            for line in fp:
                message = json.loads(line)

                if message["time_in_seconds"] < 0:
                    continue

                messages_timestamps.append(message["timestamp"])

        with self.output().open("w") as fp:
            json.dump(messages_timestamps, fp)


class CollectVodChatEmoticons(luigi.Task):
    url = luigi.Parameter()

    def requires(self):
        return DownloadVodChat(self.url)

    def output(self) -> luigi.LocalTarget:
        url = str(self.url)
        video_hash = url_to_hash(url)

        return luigi.LocalTarget(hash_to_emoticons_file(video_hash), UTF8)

    def run(self):
        custom_emoticons = get_custom_emoticons()

        emoticons_timestamps: dict[str, list[int]] = {}
        with self.input().open("r") as fp:
            for line in fp:
                message = json.loads(line)

                if message["time_in_seconds"] < 0:
                    continue

                message_emotes = mine_emoticons(message["message"], message.get("emotes", []), custom_emoticons)
                for emoticon in message_emotes:
                    if emoticon not in emoticons_timestamps:
                        emoticons_timestamps[emoticon] = []

                    emoticons_timestamps[emoticon].append(message["timestamp"])

        if len(emoticons_timestamps):
            with self.output().open("w") as fp:
                json.dump(emoticons_timestamps, fp)
