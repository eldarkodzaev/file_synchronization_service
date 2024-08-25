import os
import urllib
import urllib.request


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
            if not(filename in cloud_files_names):
                for_load.append(filename)

        return for_load
    
    def files_for_delete(self):
        local_files_names = [file['name'] for file in self.local_files]
        cloud_files_names = [file['name'] for file in self.cloud_files]

        for_delete = []
        for filename in cloud_files_names:
            if not(filename in local_files_names):
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


def check_internet_connection():
    try:
        urllib.request.urlopen("http://google.com")
    except IOError:
        return False
    return True


def check_config(config: dict):
    if not os.path.exists('.env'):
        print('Файл ".env" не найден. Создайте его в корне проекта и перезапустите программу')
        return False
    
    settings = {
        'TOKEN': str, 
        'LOCAL_DIR_PATH': str,
        'CLOUD_DIR_PATH': str,
        'LOG_FILE_PATH': str,
        'SYNCHRONIZATION_PERIOD': int
    }
    for key, value in settings.items():
        if not config.get(key):
            print(f'Неверный файл ".env". В файле должны присутствовать следующие ключи: {list(settings.keys())}. См. файл ".env.dist".')
            return False
        else:
            try:
                value(config[key])
            except ValueError:
                print(f'Параметр "{key}" должен быть типа {value.__name__}. Проверьте файл ".env" и перезапустите программу.')
                return False
            
    return True
