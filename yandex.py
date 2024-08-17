import os
import datetime
from datetime import datetime as dt
import threading

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

    def __init__(self, token: str, cloud_dir_path: str, local_dir_path: str) -> None:
        """
        Аргументы:

        token - Токен для доступа к удаленному хранилищу
        cloud_dir_path - Путь к синхронизируемой папке в удаленном хранилище
        local_dir_path - Путь к синхронизируемой локальной папке
        """
        self.token = token
        self.cloud_dir_path = cloud_dir_path
        self.local_dir_path = local_dir_path
        self.headers = {'Authorization': f'OAuth {token}'}

    def load(self, path: str):
        response = requests.get(
            f'{self.upload_url}?path={path}',
            headers=self.headers,
            timeout=3.05
        )
        print(response.json())
        url_for_load = response.json()['href']
        with open(path, 'rb') as file:
            response = requests.put(
                f'{self.upload_url}?path={path}&url={url_for_load}',
                headers=self.headers,
                files={'file': file},
                timeout=3.05
            )

    def reload(self, path: str):
        response = requests.get(
            f'{self.upload_url}?path={path}',
            headers=self.headers,
            timeout=3.05
        )
        url_for_load = response.json()['href']
        with open(path, 'rb') as file:
            response = requests.put(
                f'{self.upload_url}?path={path}&url={url_for_load}&overwrite=true',
                headers=self.headers,
                files={'file': file},
                timeout=3.05
            )

    def delete(self, filename: str):
        response = requests.delete(
            f'{self.resources_url}?path={self.cloud_dir_path}/{filename}',
            headers=self.headers,
            timeout=3.05
        )
        if response.status_code == 204:
            print(f'Файл {filename} удален')
        else:
            print('Файл не найден')

    def get_info(self) -> list[dict]:
        response = requests.get(
            f'{self.resources_url}?path={self.cloud_dir_path}&fields=_embedded',
            headers=self.headers,
            timeout=3.05
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
    files = fa.get()

    for file in files:
        if file['status'] == 'load':
            yandex_disc_dir.load(f"{config['CLOUD_DIR_PATH']}")
        else:
            yandex_disc_dir.reload(f"{config['CLOUD_DIR_PATH']}")


if __name__ == '__main__':
    run()
