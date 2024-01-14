from typing import Callable, Dict, List
import importlib.util
import re
from dataclasses import dataclass

from helpers.validation import Validation
from helpers.constants import BLACKLISTED_DIR_CHARS


def import_sort_model(path: str) -> Callable[[Dict, Dict, str, str], List[str]]:
    spec = importlib.util.spec_from_file_location('sorter', path)
    sorter = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sorter)
    return sorter.sort_model

# TODO: I don't need parent_dir_name so get rid of that
# TODO: Check Windows for behavior of / and \.... I think Windows uses \ so I might be interested in splitting by that for validate_dir_path.


@dataclass
class SorterData:
    parent_dir_path: str
    metadata_dir_path: str
    image_dir_path: str
    prompt_dir_path: str

    def __post_init__(self):

        self.parent_dir_path = Validation.validate_dir_path(
            self.parent_dir_path, 'sorter')

        self.metadata_dir_path = Validation.validate_dir_path(
            self.metadata_dir_path, 'sorter')

        self.image_dir_path = Validation.validate_dir_path(
            self.image_dir_path, 'sorter')

        self.prompt_dir_path = Validation.validate_dir_path(
            self.prompt_dir_path, 'sorter')


class DirName:
    @staticmethod
    def replace(string, char_dict):
        return ''.join([char_dict[char] if char in char_dict else char for char in string])

    @staticmethod
    def remove_extra_space(string: str):
        return ' '.join([part for part in string.split(' ') if part != ''])

    @staticmethod
    def remove_pun_before_specials(string: str, special_chars):
        return re.sub(fr"[\.?!,;:]+(?= *[{special_chars}])", "", string)

    # Replacements
    @classmethod
    def replace_with_rule_1(cls, string):
        dic = {}
        dic['<'] = '('
        dic['>'] = ')'
        dic[':'] = ','
        dic['"'] = '-'
        dic['/'] = '&'
        dic['\\'] = '&'
        dic['|'] = '&'
        dic['?'] = '.'
        dic['*'] = '&'
        return cls.remove_extra_space(cls.remove_pun_before_specials(cls.replace(string, dic), '\&\(\)\[\]\{\}\-'))

    @classmethod
    def replace_all_with_space(cls, string):
        dic = {char: ' ' for char in BLACKLISTED_DIR_CHARS}
        return cls.remove_extra_space(cls.replace(string, dic))

    @classmethod
    def replace_all_with_empty(cls, string):
        dic = {char: '' for char in BLACKLISTED_DIR_CHARS}
        return cls.remove_extra_space(cls.replace(string, dic))

    @classmethod
    def replace_all_with_dash(cls, string):
        dic = {char: '-' for char in BLACKLISTED_DIR_CHARS}
        return cls.remove_extra_space(cls.replace(string, dic))
