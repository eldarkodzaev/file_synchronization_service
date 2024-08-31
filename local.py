import os
import stat
import platform


class LocalDiscDir:
    """
    Класс для работы с папкой на локальном диске
    """
    plt = platform.system()

    def __init__(self, local_dir_path: str) -> None:
        self.local_dir_path = local_dir_path

    def get_info(self) -> list[dict]:
        """
        Возвращает информацию о файлах в локальной папке
        """

        local_files_list: list[dict] = []

        for address, _, files in os.walk(self.local_dir_path):
            for file in files:
                file_path = os.path.join(address, file)
                if not self.file_is_hidden(file_path):
                    local_files_list.append({
                        'name': file,
                        'size': os.path.getsize(file_path),
                        'created': os.path.getctime(file_path),
                        'modified': os.path.getmtime(file_path)
                    })
        return local_files_list

    def file_is_hidden(self, file_path: str) -> bool:
        """
        Проверяет, является ли файл скрытым
        """
        if self.plt in ('Linux', 'Darwin',):
            return os.path.basename(file_path).startswith('.')
        
        # if Windows
        info = os.stat(file_path)
        return info.st_file_attributes & stat.FILE_ATTRIBUTE_HIDDEN
