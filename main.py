#!/usr/bin/env python3

import os
import re
import sys
from typing import Callable, Dict
import importlib.util
import time

from lib.get_model import download_model
from lib.get_model_id import get_model_ids_from_comma_file, get_model_ids_from_comma_str, get_model_ids_from_dir_path
from lib.dirpaths import create_basic_path, create_path_by_tags
from lib.utils.utils import parse_args
# from custom.tags import create_dir_path_by_tag


def choose_filter_helper(kwargs: Dict[str, str]):
    filter_model = None
    if 'custom-filter' in kwargs:
        if not os.path.exists(kwargs['custom-filter']):
            return print('Error: Custom filter python file does not exist')
        spec = importlib.util.spec_from_file_location(
            'plugin', kwargs['custom-filter'])
        plugin = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(plugin)
        filter_model = plugin.filter_model
    elif 'filter' in kwargs:
        if kwargs['filter'] == 'tags':
            filter_model = create_path_by_tags
        elif kwargs['filter'] == 'basic':
            filter_model = create_basic_path
        else:
            return print(f'Error: Unknown filter specified. The available built-in filters are {["tags", "basic"]} (basic is the default filter)')
    else:
        filter_model = create_basic_path
    return filter_model


def batch_download_by_dir(argv: list[str]):
    args_format = '<Source Path> <Destination Path> --custom-filter=<Path to a python file (optional)> --filter=<Choose between the two implemented filters (optional)> --max-images=<Default is 3 per model (optional)>'
    example = '~/unorganized_loras ~/organized_loras --filter=tags'

    kwargs, args = parse_args(argv)

    if len(args) < 2:
        return print(
            f'Error: Missing arguments. Arguments are the following: {args_format}.\nExample: {example}')
    elif not os.path.exists(args[0]):
        return print('Error: Source directory does not exist.')

    ids = get_model_ids_from_dir_path(args[0])
    filter_model = choose_filter_helper(kwargs)
    if filter_model == None:
        return

    for id in ids:
        download_model(model_id=id, create_dir_path=filter_model,
                       dst_root_path=args[1], max_img_count=(kwargs['max-images'] if 'max-images' in kwargs else 3))
        time.sleep(5)

# TODO: Write a README.md guide that 1) talks about how to use the commands, 2) talks about how to write a custom script


def batch_download_by_file(argv: list[str]):
    args_format = '<Comma Separated File> <Destination Path> --custom-filter=<Path to a python file (optional)> --filter=<Choose between the two implemented filters (optional)> --max-images=<Default is 3 per model (optional)>'
    example = '~/lora-to-download.txt ~/organized_loras --custom-filter=example.py'

    kwargs, args = parse_args(argv)

    if len(args) < 2:
        return print(
            f'Error: Missing arguments. Arguments are the following: {args_format}.\nExample: {example}')
    elif not os.path.exists(args[0]):
        return print('Error: Source file does not exist.')

    ids = get_model_ids_from_comma_file(args[0])

    filter_model = choose_filter_helper(kwargs)
    if filter_model == None:
        return

    for id in ids:
        model_id = id[0]
        version_id = id[1] if len(id) == 2 else None
        download_model(model_id=model_id, create_dir_path=filter_model,
                       dst_root_path=args[1], max_img_count=(kwargs['max-images'] if 'max-images' in kwargs else 3), version_id=version_id)
        time.sleep(2)


def batch_download_by_str(argv: list[str]):
    args_format = '<String with IDs/URL separated by comma> <Destination Path> --custom-filter=<Path to a python file (optional)> --filter=<Choose between the two implemented filters (optional)> --max-images=<Default is 3 per model (optional)>'
    example = '"123456,78901,23456" ~/organized_loras --custom-filter=example.py'

    kwargs, args = parse_args(argv)

    if len(args) < 2:
        return print(
            f'Error: Missing arguments. Arguments are the following: {args_format}.\nExample: {example}')
    ids = get_model_ids_from_comma_str(args[0])

    filter_model = choose_filter_helper(kwargs)
    if filter_model == None:
        return

    for id in ids:
        model_id = id[0]
        version_id = id[1] if len(id) == 2 else None
        download_model(model_id=model_id, create_dir_path=filter_model,
                       dst_root_path=args[1], max_img_count=(kwargs['max-images'] if 'max-images' in kwargs else 3), version_id=version_id)
        time.sleep(5)


def main():
    available_actions = ['batchdir', 'batchfile', 'batchstr']
    argv = sys.argv[1:]
    if len(argv) == 0:
        return print(f'Error: Need to provide arguments -> <action> *<action\'s arguments>.\nAvailable actions: {available_actions}')

    match argv[0]:
        case 'batchdir':
            batch_download_by_dir(argv[1:])
        case 'batchfile':
            batch_download_by_file(argv[1:])
        case 'batchstr':
            batch_download_by_str(argv[1:])
        case _:
            return print(f'Error: Unknown action.\nAvailable actions: {available_actions}')


main()