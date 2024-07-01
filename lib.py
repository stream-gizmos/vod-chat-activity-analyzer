from hashlib import md5
from urllib.parse import urlparse


def url_to_hash(url: str) -> str:
    return md5(url.encode("utf-8")).hexdigest()


def hash_to_meta_file(video_hash: str) -> str:
    return f'data/{video_hash}_meta.json'


def hash_to_chat_file(video_hash: str) -> str:
    return f'data/{video_hash}_chat.json'


def hash_to_times_file(video_hash: str) -> str:
    return f'data/{video_hash}_times.json'


# https://stackoverflow.com/questions/7160737/how-to-validate-a-url-in-python-malformed-or-not
def is_http_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc]) and (result.scheme == 'http' or result.scheme == 'https')
    except ValueError:
        return False
