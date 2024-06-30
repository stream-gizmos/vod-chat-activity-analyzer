from hashlib import md5


def url_to_hash(url: str) -> str:
    return md5(url.encode("utf-8")).hexdigest()


def hash_to_meta_file(video_hash: str) -> str:
    return f'data/{video_hash}_meta.json'


def hash_to_chat_file(video_hash: str) -> str:
    return f'data/{video_hash}_chat.json'


def hash_to_times_file(video_hash: str) -> str:
    return f'data/{video_hash}_times.json'
