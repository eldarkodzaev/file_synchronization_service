# Python 3.10.12

# Python 3.10.12

import os
import threading
from urllib.parse import urlencode

import requests

from dotenv import dotenv_values
from loguru import logger

from abstract_disc import AbstractDisc
from utils import FilesAnalizer
from exceptions import GettingURLForUploadException, PatchResourceException


logger.add("logs.log", format="{time} {level} {message}", level="DEBUG")


class YandexDiskDir(AbstractDisc):
    """
    Класс для работы с папкой на Яндекс Диске
    """
    upload_url = 'https://cloud-api.yandex.net/v1/disk/resources/upload'
    resources_url = 'https://cloud-api.yandex.net/v1/disk/resources'
    timeout = 10  # таймаут запроса в секундах

    def __init__(self, token: str, cloud_dir_path: str, local_dir_path: str) -> None:
        """
        Аргументы:

        token - Токен для доступа к удаленному хранилищу
        cloud_dir_path - Путь к папке на Яндекс Диске
        local_dir_path - Путь к синхронизируемой локальной папке
        """
        self.token = token
        self.cloud_dir_path = cloud_dir_path
        self.local_dir_path = local_dir_path
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json', 
            'Authorization': f'OAuth {token}'
        }

    def load(self, local_path: str, cloud_path: str, overwrite: bool=False) -> None:
        try:
            url_for_upload = self._get_url_for_upload(cloud_path, overwrite=overwrite)
        except GettingURLForUploadException:
            logger.error("Ошибка при получении URL для загрузки файла на Яндекс Диск")

        self._load_file(
            local_file_path=f'{local_path}',
            cloud_file_path=f'{cloud_path}',
            url_for_upload=url_for_upload,
        )

    def delete(self, filename: str):
        url_params = urlencode({'path': f'{self.cloud_dir_path}/{filename}'})
        response = requests.delete(
            f'{self.resources_url}?{url_params}',
            headers=self.headers,
            timeout=self.timeout
        )
        if response.status_code == requests.codes.no_content:
            logger.info(f'Файл {filename} удален из Яндекс Диска')

    def get_info(self) -> list[dict]:
        url_params = urlencode({'path': self.cloud_dir_path, 'fields': '_embedded.items'})
        response = requests.get(
            f'{self.resources_url}?{url_params}',
            headers=self.headers,
            timeout=self.timeout
        )

        items = response.json()['_embedded']['items']
        cloud_files_list: list[dict] = []

        if items:
            for item in items:
                cloud_files_list.append({
                    'name': item['name'],
                    'size': item['size'],
                    'created': item['custom_properties']['created_local'],
                    'modified': item['custom_properties']['modified_local'],
                })
        return cloud_files_list
    
    def _get_url_for_upload(self, path: str, overwrite: bool) -> None:
        """
        Возвращает ссылку для загрузки файла на Яндекс Диск
        """
        url = urlencode({'path': path, 'overwrite': overwrite})
        response = requests.get(
            f'{self.upload_url}?{url}',
            headers=self.headers,
            timeout=self.timeout
        )
        if response.status_code == 200:
            return response.json()['href']
        raise GettingURLForUploadException('Не удалось получить URL для загрузки файла')
    
    def _add_custom_properties(self, local_file_path: str, cloud_file_path: str) -> None:
        """
        Добавляет ресурсу параметры size, created_local, modified_local
        """
        size = os.stat(local_file_path).st_size
        created_local = os.path.getctime(local_file_path)
        modified_local = os.path.getmtime(local_file_path)
        custom_properties = {
            "custom_properties": {
                "size": size,
                "created_local": created_local,
                "modified_local": modified_local,
            }
        }
        url_params = urlencode({'path': cloud_file_path})
        response = requests.patch(
            f'{self.resources_url}?{url_params}',
            headers=self.headers,
            data=str(custom_properties),
            timeout=self.timeout
        )
        if response.status_code != requests.codes.ok:
            raise PatchResourceException("Не удалось обновить пользовательские данные ресурса")

    def _load_file(self, local_file_path: str, cloud_file_path: str, url_for_upload: str) -> None:
        """
        Загружает файл на Яндекс Диск по полученной ссылке

        Аргументы:
        - local_file_path: путь к локальному файлу
        - cloud_file_path: путь к файлу на Яндекс Диске
        - url_for_upload: URL для загрузки файла, полученный методом _get_url_for_upload
        """
        with open(local_file_path, 'rb') as file:
            url_params = urlencode({'path': cloud_file_path})
            response = requests.put(
                f'{url_for_upload}?{url_params}',
                files={'file': file},
                timeout=self.timeout
            )
        self._add_custom_properties(local_file_path, cloud_file_path)

        if response.status_code == requests.codes.created:
            logger.info(f'Файл "{local_file_path}" успешно загружен на Яндекс Диск')


class LocalDiscDir:
    """
    Класс для работы с папкой на локальном диске
    """

    def __init__(self, local_dir_path: str) -> None:
        self.local_dir_path = local_dir_path

    def get_info(self) -> list[dict]:
        local_files_list: list[dict] = []

        for address, _, files in os.walk(self.local_dir_path):
            for file in files:
                file_path = os.path.join(address, file)
                if not self._file_is_hidden(file_path):  # скрытые файлы не будут сканироваться
                    local_files_list.append({
                        'name': file,
                        'size': os.path.getsize(file_path),
                        'created': os.path.getctime(file_path),
                        'modified': os.path.getmtime(file_path)
                    })
        return local_files_list
    
    def _file_is_hidden(self, file_path: str) -> bool:
        """
        Проверяет является ли файл скрытым

        Аргументы:
        - file_path - абсолютный путь к файлу
        """
        if os.name == 'nt':
            import win32con, win32api
            attribute = win32api.GetFileAttributes(file_path)
            return attribute and (win32con.FILE_ATTRIBUTE_HIDDEN | win32con.FILE_ATTRIBUTE_SYSTEM)
        return file_path.startswith('.')  # linux/osx


def run():
    """
    Запуск скрипта
    """
    config = dotenv_values('.env')

    threading.Timer(int(config['SYNCHRONIZATION_PERIOD']), run).start()

    local_disc_dir = LocalDiscDir(config['LOCAL_DIR_PATH'])
    local_disc_dir_info = local_disc_dir.get_info()

    yandex_disc_dir = YandexDiskDir(
        token=config['TOKEN'],
        cloud_dir_path=config['CLOUD_DIR_PATH'],
        local_dir_path=config['LOCAL_DIR_PATH']
    )
    yandex_disc_dir_info = yandex_disc_dir.get_info()

    fa = FilesAnalizer(local_disc_dir_info, yandex_disc_dir_info)
    if (for_delete := fa.files_for_delete()):
        for file in for_delete:
            yandex_disc_dir.delete(file)

    if (for_load := fa.files_for_load()):
        for file in for_load:
            yandex_disc_dir.load(
                local_path=f"{config['LOCAL_DIR_PATH']}/{file}",
                cloud_path=f"{config['CLOUD_DIR_PATH']}/{file}"
            )
    
    if (for_reload := fa.files_for_reload()):
        for file in for_reload:
            yandex_disc_dir.load(
                local_path=f"{config['LOCAL_DIR_PATH']}/{file['name']}",
                cloud_path=f"{config['CLOUD_DIR_PATH']}/{file['name']}",
                overwrite=True              
            )


if __name__ == '__main__':
    config = dotenv_values(".env")
    logger.info(f"Программа синхронизации файлов начинает работу с директорией {config['LOCAL_DIR_PATH']}")
    run()
