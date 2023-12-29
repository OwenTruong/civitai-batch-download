from dataclasses import dataclass
from datetime import datetime
import json
import os
import re
import sys
from typing import Callable, Dict, Iterable, List, Union
import importlib.util
import concurrent.futures
import requests
from tqdm import tqdm

from helpers.styler import Styler
from helpers.exceptions import CustomException, InputException, UnexpectedException


class Id:
    def __init__(self, type, data: List[str], original: str):
        if type != 'id' and type != 'site' and type != 'api':
            raise UnexpectedException(
                f'Unknown type provided for Id class: {type}')

        for el in data:
            if not isinstance(el, str):
                raise UnexpectedException(
                    f'Wrong data type for {el} in {data}')

        if not isinstance(original, str):
            raise UnexpectedException(f'Wrong data type for {original}')

        self.type = type
        self.data = data
        self.original = original


class SourceManager:
    def __init__(self) -> None:
        pass

    def __get_comma_list(self, string: str) -> List[str]:
        return [input_str for input_str in string.replace(
            '\n', '').split(',') if input_str.strip() != '']

    def __use_parent_dir_if_exist(self, src: str, parent: Union[str, None]) -> str:
        return os.path.normpath(os.path.join(os.path.dirname(parent), src)) if parent else src

    def parse_src(self, str_li: List[str], parent: Union[str, None] = None) -> List[Id]:
        res: List[Id] = []
        for string in str_li:
            string = string.strip()

            if string.isdigit() and abs(int(string)) == int(string):
                res.append(Id('id', [string], string))
            elif len(self.__get_comma_list(string)) > 1:
                arg_str_li = self.__get_comma_list(string)
                res.extend(self.parse_src(arg_str_li))
            elif 'civitai.com/api' in string:
                version_id_regex = r'(?<=models\/)\d+'
                version_id = re.search(version_id_regex, string)
                if version_id == None:
                    err = 'Incorrect format for the url provided' + \
                        (f' in {parent}: ' if parent else ': ') + string
                    raise InputException(err)
                version_id = version_id.group(0)
                res.append(Id('api', [version_id], string))
            elif 'civitai.com/models' in string:
                model_id = re.search(r'(?<=models\/)\d+', string)
                version_id = re.search(r'(?<=modelVersionId=)\d+', string)

                if model_id == None:
                    err = 'Incorrect format for the url/id provided' + \
                        (f' in {parent}: ' if parent else ': ') + string
                    raise InputException(err)
                model_id = model_id.group(0)

                if version_id:
                    version_id = version_id.group(0)
                    res.append(
                        Id('site', [model_id, version_id], string))
                else:
                    res.append(Id('site', [model_id], string))
            elif os.path.exists(self.__use_parent_dir_if_exist(string, parent)):
                string = self.__use_parent_dir_if_exist(string, parent)
                print(f'after: {string}')
                file_str = None

                with open(string, 'r') as file:
                    file_str = file.read().strip()
                if file_str == None:
                    raise UnexpectedException(
                        'Unknown exception while reading batchfile path.')
                str_li_res = self.__get_comma_list(file_str)
                res.extend(self.parse_src(str_li_res, parent=string))
            else:
                raise InputException(
                    f'Bad source provided: {string}', f'   Batchfile Path: {parent}' if parent else None)

        return res
