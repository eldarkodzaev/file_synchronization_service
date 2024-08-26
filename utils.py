import os
import urllib
import urllib.parse
import urllib.request

import requests
from dotenv import dotenv_values


class FilesAnalizer:
    """
    Анализирует файлы, помечая их как к загрузке/обновлению/удалению
    """

    def __init__(self, local_files: list[dict], cloud_files: list[dict]) -> None:
        self.local_files = local_files
        self.cloud_files = cloud_files

    def files_for_load(self):
        local_files_names = [file['name'] for file in self.local_files]
        cloud_files_names = [file['name'] for file in self.cloud_files]

        for_load = []
        for filename in local_files_names:
            if not (filename in cloud_files_names):
                for_load.append(filename)

        return for_load

    def files_for_delete(self):
        local_files_names = [file['name'] for file in self.local_files]
        cloud_files_names = [file['name'] for file in self.cloud_files]

        for_delete = []
        for filename in cloud_files_names:
            if not (filename in local_files_names):
                for_delete.append(filename)

        return for_delete

    def files_for_reload(self):
        cloud_files_names = [file['name'] for file in self.cloud_files]
        for_reload = []
        for file in self.local_files:
            if file['name'] in cloud_files_names:
                cloud_file = self.find_dict_in_list(self.cloud_files, file)
                if cloud_file != file:
                    for_reload.append(file)
        return for_reload

    def find_dict_in_list(self, lst: list[dict], dct: dict) -> dict | None:
        for item in lst:
            if item['name'] == dct['name']:
                return item
        return None


class EnvFileChecker:
    """
    Проверяет файл ".env" на наличие ошибок
    """

    resource_url = "https://cloud-api.yandex.net/v1/disk/resources"

    def __init__(self) -> None:
        if self._env_file_exists():
            self.env = dotenv_values(".env")

    def _env_file_exists(self) -> bool:
        return os.path.exists('.env')

    def _check_token(self) -> bool:
        token = self.env.get('TOKEN')
        if not token:
            print('Не найден ключ "TOKEN" в файле ".env"')
            return False
        return True

    def _check_local_dir_path(self) -> bool:
        local_dir_path = self.env.get('LOCAL_DIR_PATH')

        if not local_dir_path:
            print('Не найден ключ "LOCAL_DIR_PATH" в файле ".env"')
            return False

        if not os.path.isdir(local_dir_path):
            print(f'Неправильный путь "{local_dir_path}" у параметра "LOCAL_DIR_PATH"')
            return False

        return True

    def _check_cloud_dir_path(self) -> bool:
        cloud_dir_path = self.env.get('CLOUD_DIR_PATH')

        if not cloud_dir_path:
            print('Не найден ключ "CLOUD_DIR_PATH" в файле ".env"')
            return False

        url_params = urllib.parse.urlencode({'path': cloud_dir_path})
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': f"OAuth {self.env['TOKEN']}"
        }
        response = requests.get(
            f"{self.resource_url}?{url_params}",
            headers=headers
        )
        
        if response.status_code == requests.codes.not_found:
            print(f'Папка "{cloud_dir_path}" не найдена на Яндекс Диске')
            return False
        if response.status_code == requests.codes.unauthorized:
            print(f'Неверный токен для доступа к Яндекс Диску')
            return False

        return True

    def _check_log_file_path(self) -> bool:
        log_file_path = self.env.get('LOG_FILE_PATH')

        if not log_file_path:
            print('Не найден ключ "LOG_FILE_PATH" в файле ".env"')
            return False

        if not os.path.isfile(log_file_path):
            print(f'Неправильный путь "{log_file_path}" у параметра "LOG_FILE_PATH"')
            return False

        return True

    def _check_synchronization_period(self) -> bool:
        sync_period = self.env.get('SYNCHRONIZATION_PERIOD')

        if not sync_period:
            print('Не найден ключ "SYNCHRONIZATION_PERIOD" в файле ".env"')
            return False

        try:
            int(sync_period)
        except ValueError:
            print(f'Параметр "SYNCHRONIZATION_PERIOD" должен быть целым числом')
            return False

        return True

    def check(self) -> bool:
        if not self._env_file_exists():
            print('Файл ".env" не найден. Создайте его в корне проекта и перезапустите программу')
            return False

        return all([
            self._check_token(),
            self._check_local_dir_path(),
            self._check_cloud_dir_path(),
            self._check_log_file_path(),
            self._check_synchronization_period()
        ])


def check_internet_connection() -> bool:
    """
    Проверяет наличие интернет-соединения
    """
    try:
        urllib.request.urlopen("http://google.com")
    except IOError:
        return False
    return True
