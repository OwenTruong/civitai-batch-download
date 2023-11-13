from json import dumps
import requests
import os
import re
from typing import Callable, Dict, List

from termcolor import colored

from .utils import err_400_if_true, err_404_if_true, err_500_if_true, err_501_if_true, err_if_true, write_to_file


class Metadata:
    __id_string = None

    model_name = None
    model_id = None
    version_id = None

    model_dict = None
    version_dict = None

    download_url = None
    images_dict_li = None
    nsfw = False

    def __init__(self, id_string: str):
        self.__id_string = id_string

        if id_string.isdigit():
            self.__id_handler()
        elif "/api/" in id_string:
            self.__api_url_handler()
        else:
            self.__url_handler()

    def __id_handler(self):
        id = [self.__id_string]
        self.__handler(id, 'id')

    def __url_handler(self):
        model_id_regex = r'(?<=models\/)\d+'
        version_id_regex = r'(?<=modelVersionId=)\d+'
        model_id = re.search(model_id_regex, self.__id_string)
        version_id = re.search(version_id_regex, self.__id_string)
        err_400_if_true(model_id == None,
                        f'Incorrect format for the url/id provided: {self.__id_string}')
        model_id = model_id.group(0)
        err_500_if_true(
            model_id == None, f'Unknown error while parsing model id for the url/id provided: {self.__id_string}')

        if version_id:
            version_id = version_id.group(0)
            err_500_if_true(
                version_id == None, f'Unknown error while parsing version id for the url/id provided: {self.__id_string}')
            self.__handler([model_id, version_id], 'url')
        else:
            self.__handler([model_id], 'url')

    def __api_url_handler(self):
        version_id_regex = r'(?<=models\/)\d+'
        version_id = re.search(version_id_regex, self.__id_string)
        err_400_if_true(version_id == None,
                        f'Incorrect format for the url provided: {self.__id_string}')
        version_id = version_id.group(0)
        err_500_if_true(
            version_id == None, f'Unknown error while parsing version id for the url provided: {self.__id_string}')

        self.__handler([version_id], 'api')

    def __handler(self, ids: List[int], type: str):
        if type == 'url' and len(ids) == 2:
            self.model_id = ids[0]
            self.version_id = ids[1]
            self.model_dict = self.__get_model_metadata()
            self.version_dict = self.__get_version_metadata()
        elif type == 'id' or (type == 'url' and len(ids) == 1):
            self.model_id = ids[0]
            self.model_dict = self.__get_model_metadata()
            err_404_if_true(len(self.model_dict['modelVersions']) == 0,
                            f'No model versions found from model id, {self.model_id}')
            self.version_dict = self.model_dict['modelVersions'][0]
            self.version_id = str(self.version_dict['id'])
        elif type == 'api':
            self.version_id = ids[0]
            self.version_dict = self.__get_version_metadata()
            self.model_id = str(self.version_dict['modelId'])
            self.model_dict = self.__get_model_metadata()
        else:
            err_400_if_true(True,
                            f'Incorrect format sent ({ids}, {type}): "{self.__id_string}"')

        self.download_url = self.version_dict['downloadUrl']
        self.images_dict_li = self.version_dict['images']
        self.nsfw = self.model_dict['nsfw']
        self.model_name = self.model_dict['name']

    def __get_model_metadata(self):
        """Returns json object if request succeeds, else print error and returns None"""
        metadata_url = 'https://civitai.com/api/v1/models/' + self.model_id
        return self.__get_metadata(metadata_url)

    def __get_version_metadata(self):
        metadata_url = 'https://civitai.com/api/v1/model-versions/' + self.version_id
        return self.__get_metadata(metadata_url)

    def __get_metadata(self, url: str):
        meta_res = requests.get(url)
        err_if_true(meta_res.status_code != 200,
                    f'Downloading metadata from CivitAI for "{self.__id_string}" failed when trying to request metadata from "{url}"', meta_res.status_code)
        return meta_res.json()


def _download_image(dirpath: str, images: list[Dict], nsfw: bool, max_img_count):
    image_urls = []

    for dict in images:
        if len(image_urls) == max_img_count:
            break
        if not nsfw and dict['nsfw'] != 'None':
            continue
        else:
            image_urls.append(dict['url'])

    for url in image_urls:
        image_res = requests.get(url)
        err_if_true(image_res.status_code != 200,
                    f'Downloading image from CivitAI failed for the url: {url}', image_res.status_code)
        write_to_file(os.path.join(
            dirpath, os.path.basename(url)), image_res.content, 'wb')


def download_model(input_str: str, create_dir_path: Callable[[Dict, Dict, str, str], str], dst_root_path: str, download_image: bool, max_img_count: int):
    """
        Downloads the model's safetensors and json metadata files.
        create_dir_path is a callback function that takes in the following: metadata dict, specific model's data as dict, filename, and root path.
    """
    err_500_if_true(input_str == None or create_dir_path == None or dst_root_path ==
                    None or download_image == None or max_img_count == None, 'download_model received a None type in one of its parameter')

    metadata = Metadata(input_str)

    print(colored(
        f"Now downloading \"{metadata.model_name}\" with model id, {metadata.model_id}, and version id, {metadata.version_id}...", 'blue'))
    model_res = requests.get(metadata.download_url, headers={
                             "Accept-Charset": "utf-16"})
    err_if_true(model_res.status_code != 200,
                f'Downloading model from CivitAI failed for model id, {metadata.model_id}, and version id, {metadata.version_id}', model_res.status_code)

    # Find filename
    content_disposition = model_res.headers.get('Content-Disposition')
    err_404_if_true(content_disposition == None,
                    f'Downloaded model from CivitAI has no content disposition header available.')
    filename = None

    try:
        filename = content_disposition.split(
            'filename=')[-1].strip('"').encode('latin-1').decode('utf-8')
    except UnicodeDecodeError:
        # Alternative solution for finding filename
        for file in metadata.version_dict['files']:
            file_version_id = re.search(
                r'(?<=models\/)\d+', file['downloadUrl'])
            if file_version_id != None and file_version_id.group(0) == metadata.version_id:
                filename = file['name']
                break

    if filename == None:
        err_500_if_true(filename == None,
                        f"Error: Unable to retrieve filename for {input_str}")

    # Create empty directory recursively
    filename_without_ext, filename_ext = os.path.splitext(filename)
    dst_dir_path = create_dir_path(
        metadata.model_dict, metadata.version_dict, filename_without_ext, dst_root_path)
    if not os.path.exists(dst_dir_path):
        os.makedirs(dst_dir_path)

    # Write model to the directory
    json_path = os.path.join(
        dst_dir_path, f'{filename_without_ext}-mid_{metadata.model_id}-vid_{metadata.version_id}.json')
    model_path = os.path.join(
        dst_dir_path, f'{filename_without_ext}-mid_{metadata.model_id}-vid_{metadata.version_id}{filename_ext}')
    write_to_file(json_path, dumps(
        metadata.model_dict, indent=2, ensure_ascii=False))
    write_to_file(model_path, model_res.content, 'wb')
    if download_image:
        _download_image(
            dst_dir_path, metadata.version_dict['images'], metadata.nsfw, max_img_count)

    print(colored(
        f"Download completed for \"{metadata.model_name}\" with model id, {metadata.model_id}, and version id, {metadata.version_id}: {model_path}", 'green'))


# def download_model(model_id: str, create_dir_path: Callable[[Dict, Dict, str, str], str], dst_root_path: str, version_id: str = None, download_image: bool = True, max_img_count: int = 3):
#     """
#         Downloads the model's safetensors and json metadata files.
#         create_dir_path is a callback function that takes in the following: metadata dict, specific model's data as dict, filename, and root path.
#     """
#     err_500_if_true(model_id == None or create_dir_path == None or dst_root_path ==
#                     None or download_image == None or max_img_count == None, 'download_model received a None type in one of its parameter')

#     def create_model_url(version):
#         return f'https://civitai.com/api/download/models/{version}'

#     # Fetch model metadata
#     meta_json = _get_metadata_json(model_id)
#     if (meta_json == None):
#         return

#     # Find the specific version of the model
#     model_dict_list: list = meta_json['modelVersions']
#     model_dict = model_dict_list[0] if version_id == None else next(
#         (obj for obj in model_dict_list if str(obj['id']) == version_id), None)
#     err_404_if_true(model_dict == None,
#                     f'The version id, {version_id} provided does not exist on CivitAI for the model with model id, {model_id}.\nAvailable version ids: {[dict["id"] for dict in model_dict_list]}')
#     version_id = model_dict['id']

#     # Fetch model data
#     print(colored(
#         f"Now downloading \"{meta_json['name']}\" with model id, {model_id}, and version id, {version_id}...", 'blue'))
#     model_res = requests.get(create_model_url(
#         model_dict['id']), headers={"Accept-Charset": "utf-16"})

#     err_if_true(model_res.status_code != 200,
#                 f'Downloading model from CivitAI failed for model id, {model_id}, and version id, {version_id}', model_res.status_code)

#     # Find filename # FIXME: Finding filename by content-disposition is not working for UTF-8 characters (i.e. chinese characters). wget is able to retrieve the filename normally.
#     content_disposition = model_res.headers.get('Content-Disposition')
#     err_404_if_true(content_disposition == None,
#                     f'Downloaded model from CivitAI has no content disposition header available.')
#     alt_filename = content_disposition.split('filename=')[-1].strip('"')

#     # Temporary solution for finding filename
#     filename = None
#     for file in model_dict['files']:
#         regex_res = re.search(r'/(\d+)$', file['downloadUrl'])
#         if regex_res != None and regex_res.group(0) == model_dict['id']:
#             filename = file['name']
#             break

#     if filename == None:
#         err_404_if_true(alt_filename == None,
#                         f"Error: Unable to retrieve filename for {meta_json['name']}")
#         filename = alt_filename

#     # Write metadata and model data to files
#     filename_without_ext = os.path.splitext(filename)[0]
#     dst_dir_path = create_dir_path(
#         meta_json, model_dict, filename_without_ext, dst_root_path)
#     if not os.path.exists(dst_dir_path):
#         os.makedirs(dst_dir_path)
#     write_to_file(
#         os.path.join(dst_dir_path, f'{filename_without_ext}-{model_id}.json'), dumps(meta_json, indent=2, ensure_ascii=False))
#     write_to_file(
#         os.path.join(dst_dir_path, f'{filename_without_ext}-{model_id}.safetensors'), model_res.content, 'wb')
#     if download_image:
#         _download_image(
#             dst_dir_path, model_dict['images'], meta_json['nsfw'], max_img_count)

#     tensor_full_path = os.path.join(
#         dst_dir_path, f'{filename_without_ext}-{model_id}.safetensors')
#     print(colored(
#         f"Download completed for \"{meta_json['name']}\" with model id, {model_id}, and version id, {version_id}: {tensor_full_path}", 'green'))
