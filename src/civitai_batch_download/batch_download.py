import os
import time

from .get_model import download_model
from .get_model_id import get_model_ids_from_comma_file, get_model_ids_from_comma_str, get_model_ids_from_dir_path
from .filters import choose_filter_helper
from .utils import parse_args


def batch_download_by_dir(argv: list[str]):
    args_format = '<Source Path> <Destination Path> --custom-filter=<Path to filter file (optional)> --filter=<tags (optional)> --max-images=<default=3 (optional)>'
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


def batch_download_by_file(argv: list[str]):
    args_format = '<Comma Separated File> <Destination Path> --custom-filter=<Path to filter file (optional)> --filter=<tags (optional)> --max-images=<default=3 (optional)'
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
    args_format = '<String with IDs/URL separated by comma> <Destination Path> --custom-filter=<Path to filter file (optional)> --filter=<tags (optional)> --max-images=<default=3 (optional)'
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
