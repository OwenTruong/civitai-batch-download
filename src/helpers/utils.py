from dataclasses import InitVar, dataclass, field
from datetime import datetime
import json
import os
import sys
import time
import pkg_resources
from typing import Callable, Dict, Iterable, List, Union, Optional
import importlib.util
import concurrent.futures
import requests
from tqdm import tqdm

from helpers.sorter.utils import import_sort_model
from helpers.sorter import basic, tags
from helpers.styler import Styler
from helpers.exceptions import CustomException, InputException, UnexpectedException
from helpers.validation import Validation

# Level 0

_verbose = False


def get_verbose():
    return _verbose


def set_verbose(verbose: bool):
    global _verbose
    _verbose = verbose
    return _verbose


def getDate():
    now = datetime.now()
    return now.strftime("%Y-%m-%d--%H:%M:%S-%f")


def get_version():
    return pkg_resources.get_distribution('civitdl').version


# Level 1 - Currently or in the future might depends on level 0


def run_verbose(fn, *args, **kwargs):
    if get_verbose():
        fn(*args, **kwargs)


def print_verbose(*args, **kwargs):
    if get_verbose():
        args = [Styler.stylize(str(arg), bg_color='info') for arg in args]
        print(*args, **kwargs)


def print_exc(exc: Exception, *args, **kwargs):
    if isinstance(exc, CustomException):
        print(exc, file=sys.stderr, *args, **kwargs)
    else:
        print(Styler.stylize(str(exc), color='exception'), *args,
              file=sys.stderr, **kwargs)


def safe_run(callback: Callable[..., any], *values: any) -> dict:
    try:
        return {"success": True, "data": callback(*values)}
    except Exception as e:
        return {"success": False, "error": e}


def concurrent_request(req_fn, urls, max_workers=16):
    res_list = None

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(req_fn, url) for url in urls]
        res_list = [future.result() for future in futures]

    return res_list


def get_progress_bar(total: float, desc: str):
    return tqdm(total=total, desc=desc,
                unit='iB', unit_scale=True)


def find_in_list(li, cond_fn: Callable[[any, int], bool], default=None):
    """Given a list and a condition function, where the first argument is the index of the item and the second argument is the value of the item, it returns the first value in the list when the condition is true"""
    return next((item for i, item in enumerate(li) if cond_fn(item, int)), default)


def createDirsIfNotExist(dirpaths):
    for dirpath in dirpaths:
        os.makedirs(dirpath, exist_ok=True)


# Level 2 - Currently or in the future might depends on level 0 and 1


def write_to_file(filepath: str, content_chunks: Iterable, mode: str = None, limit_rate: Union[int, None] = 0, use_pb: bool = False, total: float = 0, desc: str = None):
    """Uses content_chunks to write to filepath bit by bit. If use_pb is enabled, it is recommended to set total kwarg to the length of the file to be written."""
    progress_bar = get_progress_bar(total, desc) if use_pb else None
    with open(filepath, mode if mode != None else 'w') as file:
        last_chunk_time = time.perf_counter()
        for content in content_chunks:
            file.write(content)
            bytes_downloaded = len(content)

            download_time = time.perf_counter() - last_chunk_time
            speed = bytes_downloaded / download_time
            if limit_rate is not None and limit_rate is not 0 and speed > limit_rate:
                time_to_sleep = (bytes_downloaded / limit_rate) - download_time
                if time_to_sleep > 0:
                    time.sleep(time_to_sleep)

            if (progress_bar):
                progress_bar.update(bytes_downloaded)

            last_chunk_time = time.perf_counter()

    if (progress_bar):
        progress_bar.close()


def write_to_files(dirpath: str, basenames: Iterable, contents: Iterable, mode: str = None, use_pb: bool = False, total: float = 0, desc: str = None):
    """Write content to multiple files in dirpath. If use_pb is enabled, it is recommended to set total kwarg to the number of files being written."""
    progress_bar = get_progress_bar(total, desc) if use_pb else None
    for basename, content in zip(basenames, contents):
        filepath = os.path.join(dirpath, basename)
        with open(filepath, mode if mode != None else 'w') as file:
            file.write(content)
            if (progress_bar):
                progress_bar.update(1)
    if (progress_bar):
        progress_bar.close()


def parse_bytes(size: Union[str, int, float], name: str):
    units = {"k": 10**3, "m": 10**6, "g": 10**9, "t": 10**12}

    res = safe_run(float, size)
    if res["success"] == True:
        number = round(res["data"])
        Validation.validate_integer(number, name)
        return number
    else:
        number, unit = (size[0:-1], size[-1:].lower())

        num_res = safe_run(float, number)
        if num_res["success"] == False:
            raise InputException(
                f'Invalid byte value for {name}: {size}')
        else:
            number = round(num_res["data"])
            Validation.validate_integer(number, name)

        if unit not in units:
            raise InputException(
                f'Invalid byte value for {name}: {unit}')
        else:
            return number * units[unit]


# Level 3 - Currently or in the future might depends on level 0, 1 and 2

class BatchOptions:
    sorter: Callable[[Dict, Dict, str, str],
                     List[str]] = basic.sort_model
    max_images: int = 3
    api_key: Optional[str] = None

    with_prompt: bool = True
    limit_rate: int = 0
    retry_count: int = 3
    pause_time: int = 3

    verbose: Optional[bool] = None

    def __get_sorter(self, sorter: str):
        if not isinstance(sorter, property) and not isinstance(sorter, str):
            raise InputException(
                'Sorter provided is not a string in BatchOptions.')

        sorter_str = 'basic' if isinstance(sorter, property) else sorter
        if sorter_str == 'basic' or sorter_str == 'tags':
            self._sorter = tags.sort_model if sorter_str == 'tags' else basic.sort_model
        else:
            self._sorter = import_sort_model(sorter_str)

        print_verbose("Chosen Sorter Description: ", self._sorter.__doc__)
        return self._sorter

    def __init__(self, retry_count, pause_time, max_images, with_prompt, api_key, verbose, sorter, limit_rate):
        self.session = requests.Session()

        if verbose is not None:
            Validation.validate_bool(verbose, 'verbose')
            self.verbose = verbose
            set_verbose(self.verbose)

        if sorter is not None:
            Validation.validate_string(sorter, 'sorter')
            self.sorter = self.__get_sorter(sorter)

        if max_images is not None:
            Validation.validate_integer(max_images, 'max_images', min_value=0)
            self.max_images = max_images

        if api_key is not None and api_key is not '':
            Validation.validate_string(api_key, 'api_key')
            self.api_key = api_key

        if with_prompt is not None:
            Validation.validate_bool(with_prompt, 'with_prompt')
            self.with_prompt = with_prompt

        if limit_rate is not None:
            Validation.validate_types(
                limit_rate, [str, int, float], 'limit_rate')
            self.limit_rate = parse_bytes(limit_rate, "limit_rate")

        if retry_count is not None:
            Validation.validate_integer(
                retry_count, 'retry_count', min_value=0)
            self.retry_count = retry_count

        if pause_time is not None:
            Validation.validate_float(pause_time, 'pause_time', min_value=0)
            self.pause_time = pause_time

 # TODO: Where are we planning on using DefaultOptions and BatchOptions?... I think I should consider argparse and __main__ to be in the same context...


class DefaultOptions:
    sorter: Optional[str] = None
    max_images: Optional[int] = None
    api_key: Optional[str] = None

    with_prompt: Optional[bool] = None
    limit_rate: Optional[str] = None
    retry_count: Optional[int] = None
    pause_time: Optional[int] = None

    def __init__(self, sorter=None, max_images=None, api_key=None, with_prompt=None, limit_rate=None, retry_count=None, pause_time=None):
        if sorter is not None:
            Validation.validate_string(
                sorter, 'sorter')

            self.sorter = sorter

        if max_images is not None:
            Validation.validate_integer(
                max_images, 'max_images', min_value=0
            )
            self.max_images = max_images

        if api_key is not None:
            Validation.validate_string(api_key, 'api_key')
            self.api_key = api_key

        if with_prompt is not None:
            Validation.validate_bool(with_prompt, 'with_prompt')
            self.with_prompt = with_prompt

        if limit_rate is not None:
            Validation.validate_string(limit_rate, 'limit_rate')
            parse_bytes(limit_rate, 'limit_rate')
            self.limit_rate = limit_rate

        if retry_count is not None:
            Validation.validate_integer(
                retry_count, 'retry_count', min_value=0
            )
            self.retry_count = retry_count

        if pause_time is not None:
            Validation.validate_float(
                pause_time, 'pause_time', min_value=0
            )
            self.pause_time = pause_time
