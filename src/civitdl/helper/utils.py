import json
from typing import Callable

from tqdm import tqdm
import pygit2

from .exceptions import UnexpectedException


def write_to_file(path, content, mode: str = None):
    f = open(path, mode) if mode != None else open(path, 'w')
    f.write(content)
    f.close()


def write_to_file_with_progress_bar(path, res, mode: str = None):
    """Stream must have been enabled -> request.get(url, stream=True)"""

    total_size_in_bytes = int(res.headers.get('content-length', 0))
    block_size = 1024
    progress_bar = tqdm(total=total_size_in_bytes, unit='iB', unit_scale=True)
    with open(path, mode if mode != None else 'w') as file:
        for data in res.iter_content(block_size):
            progress_bar.update(len(data))
            file.write(data)
    progress_bar.close()
    if total_size_in_bytes != 0 and progress_bar.n != total_size_in_bytes:
        raise UnexpectedException(
            'Unexpected error while writing file with progress bar.')


def find_in_list(li, cond_fn: Callable[[any, int], bool], default=None):
    """Given a list and a condition function, where the first argument is the index of the item and the second argument is the value of the item, it returns the first value in the list when the condition is true"""
    return next((item for i, item in enumerate(li) if cond_fn(item, int)), default)


def run_in_dev(fn, *args):
    if pygit2.Repository('.').head.shorthand != 'master':
        fn(*args)
