from abc import ABC, abstractmethod


class AbstractDisc(ABC):

    @abstractmethod
    def load(self, path: str):
        """
        Загрузка файла в хранилище
        """
        pass

    @abstractmethod
    def delete(self, filename: str):
        """
        Удаление файла из хранилища
        """
        pass

    @abstractmethod
    def get_info(self) -> None:
        """
        Получение информации о хранящихся в удалённом хранилище файлах
        """
        pass
