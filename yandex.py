# Python 3.10.12

import os
import datetime
from datetime import datetime as dt
import threading
from urllib.parse import urlencode

import requests

from dotenv import dotenv_values

from abstract_disc import AbstractDisc
from utils import FilesAnalizer


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
        cloud_dir_path - Путь к синхронизируемой папке на Яндекс Диске
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

    def load(self, local_path: str, cloud_path: str) -> None:
        # Получаем URL для загрузки файла
        try:
            url_for_upload = self._get_url_for_upload(cloud_path, overwrite=False)
        except ConnectionError as e:
            print(e)
            return None

        # Загружаем файл по полученному URL
        self._load_file(
            local_file_path=f'{local_path}',
            cloud_file_path=f'{cloud_path}',
            url_for_upload=url_for_upload,
        )

    def reload(self, local_path: str, cloud_path: str):
        # Получаем URL для загрузки файла
        try:
            url_for_upload = self._get_url_for_upload(cloud_path, overwrite=True)
        except ConnectionError as e:
            print(e)
            return None
        
        # Загружаем файл по полученному URL
        self._load_file(
            local_file_path=f'{local_path}',
            cloud_file_path=f'{cloud_path}',
            url_for_upload=url_for_upload,
        )

    def delete(self, filename: str):
        response = requests.delete(
            f'{self.resources_url}?path={self.cloud_dir_path}/{filename}',
            headers=self.headers,
            timeout=self.timeout
        )
        if response.status_code == 204:
            print(f'Файл {filename} удален')
        else:
            print('Файл не найден')

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
                    'created': item['created'],
                    'modified': item['modified'],
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
        raise ConnectionError('Не удалось получить URL для загрузки файла')

    def _load_file(self, local_file_path: str, cloud_file_path: str, url_for_upload: str) -> None:
        """
        Загружает файл на Яндекс Диск по полученной ссылке
        """
        with open(local_file_path, 'rb') as file:
            url_params = urlencode({'path': cloud_file_path})
            response = requests.put(
                f'{url_for_upload}?{url_params}',
                files={'file': file},
                timeout=10
            )

        if response.status_code == 201:
            print(f'Файл "{local_file_path}" успешно загружен на Яндекс Диск')
        else:
            print(response)



class LocalDiscDir:
    """
    Класс для работы с папкой на локальном диске
    """
    tz = datetime.timezone(offset=datetime.timedelta(0))

    def __init__(self, local_dir_path: str) -> None:
        self.local_dir_path = local_dir_path

    def get_info(self) -> list[dict]:
        local_files_list: list[dict] = []

        for address, _, files in os.walk(self.local_dir_path):
            for file in files:
                file_path = os.path.join(address, file)
                local_files_list.append({
                    'name': file,
                    'size': os.path.getsize(file_path),
                    'created': dt.fromtimestamp(int(os.path.getctime(file_path)), self.tz).isoformat(),
                    'modified': dt.fromtimestamp(int(os.path.getmtime(file_path)), self.tz).isoformat(),
                })
        return local_files_list


def run():
    """
    Запуск скрипта
    """
    config = dotenv_values('.env')

    # threading.Timer(config['SYNCHRONIZATION_PERIOD'], run).start()

    local_disc_dir = LocalDiscDir(config['LOCAL_DIR_PATH'])
    local_disc_dir_info = local_disc_dir.get_info()

    yandex_disc_dir = YandexDiskDir(
        token=config['TOKEN'],
        cloud_dir_path=config['CLOUD_DIR_PATH'],
        local_dir_path=config['LOCAL_DIR_PATH']
    )
    yandex_disc_dir_info = yandex_disc_dir.get_info()

    fa = FilesAnalizer(local_disc_dir_info, yandex_disc_dir_info)
    files = fa.get_files_for_upload()

    for file in files:
        if file['status'] == 'load':
            yandex_disc_dir.load(
                local_path=f"{config['LOCAL_DIR_PATH']}/{file['name']}",
                cloud_path=f"{config['CLOUD_DIR_PATH']}/{file['name']}"
            )
        elif file['status'] == 'reload':
            yandex_disc_dir.reload(
                local_path=f"{config['LOCAL_DIR_PATH']}/{file['name']}",
                cloud_path=f"{config['CLOUD_DIR_PATH']}/{file['name']}"
            )


if __name__ == '__main__':
    run()
