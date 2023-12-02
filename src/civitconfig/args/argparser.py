import os
import re
from typing import Dict, List, Union

import argparse

from termcolor import colored

from helpers.exceptions import InputException, UnexpectedException

__all__ = ['get_args']


parser = argparse.ArgumentParser(
    prog='civitconfig',
    description="civitconfig is a cli program used to set configurations for the main program, civitdl.",
    formatter_class=argparse.RawTextHelpFormatter
)


subparsers = parser.add_subparsers(
    dest='subcommand',
    required=True,
    help='Choose one of the following subcommands: default, sorter, alias.')

default_parser = subparsers.add_parser(
    'default', help='Set a default value for one of the options below.\nIf no options are provided, default will print the current default.\n')
default_parser.add_argument('-m', '--max-images', type=int,
                            help='Set the default max number of images to download per model.')
default_parser.add_argument('-s', '--sorter', type=str,
                            help='Set the default sorter given name of sorter (filepath not accepted).')
default_parser.add_argument('-k', '--api-key', type=str,
                            help='Set the api key to use for model downloads that require users to log in.')


sorter_parser = subparsers.add_parser(
    'sorter', help='Sorter-related subcommand.\nCurrently supports listing, adding and deleting sorters.\nIf no options are provided, sorter will list all available sorters.\nExample usage: civitdl 123456 ./lora --sorter mysorter.'
)
sorter_group = sorter_parser.add_mutually_exclusive_group()
sorter_group.add_argument('-a', '--add', type=str, nargs=2,
                          help='Add/save a new sorter to civitdl program.\nFor the first arg, you have to create a memorable name for the sorter.\nFor the second arg, you have to give the file path to the sorter file.\nExample: civitconfig sorter --add mysorter ./custom/tags.py\n.(custom/tags.py is free to be deleted once it is added to the program)')
sorter_group.add_argument('-d', '--delete', type=str,
                          help='Delete sorter based on name of the sorter.\nExample: civitconfig sorter --delete mysorter.')


alias_parser = subparsers.add_parser(
    'alias', help='Alias-related subcommand.\nCurrently supports listing, adding and deleting aliases.\nIf no options are provided, alias will list all available aliases.\nExample usage: civitdl 123456 @lora.'
)
alias_group = alias_parser.add_mutually_exclusive_group()
alias_group.add_argument('-a', '--add', type=str, nargs=2,
                         help='Add a new alias to the civitdl program.\nFor the first arg, you have to create a memorable name for the alias.\nFor the second arg, you have to give a directory path.\nExample: civitconfig alias --add @lora ./ComfyUI/models/loras.')
alias_group.add_argument('-d', '--delete', type=str,
                         help='Delete alias based on name of the alias.\nExample: civitconfig alias --delete @lora.')


def get_args():
    parser_result = parser.parse_args()
    return {
        key: value for key, value in list(
            vars(parser_result).items()) if value != None
    }
