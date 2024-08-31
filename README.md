<h1>Сервис синхронизации файлов</h1>
Синхронизирует файлы в локальной папке с папкой на Яндекс.Диске.
<h2>Установка</h2>

```
git clone https://github.com/eldarkodzaev/file_synchronization_service.git
cd file_synchronization_service/
python3 -m pip install -r requirements.txt
```

> [!NOTE]
> При установке в Windows использовать `python` вместо `python3`

<h2>Настройка</h2>

Создайте файл `.env` в корне проекта и заполните его. Пример заполнения указан в файле `.env.dist`.

<u>Параметры</u>:
- `TOKEN` - токен доступа к API Яндекс.Диска.
- `LOCAL_DIR_PATH` - абсолютный путь к папке на локальном диске.
- `CLOUD_DIR_PATH` - абсолютный путь к папке в Яндекс.Диске.
- `LOG_FILE_PATH` - абсолютный путь к папке в которой будет храниться лог-файл.
- `SYNCHRONIZATION_PERIOD` - период синхронизации папки в секундах.

<h2>Запуск</h2>

Linux/MacOS:

```
python3 yandex.py
```

Windows:

```
python yandex.py
```
