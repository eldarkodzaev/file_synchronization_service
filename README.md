<h1>Сервис синхронизации файлов</h1>
Синхронизирует файлы в локальной папке с папкой на Яндекс.Диске.
<h2>Установка</h2>

```
git clone https://github.com/eldarkodzaev/file_synchronization_service.git
cd file_synchronization_service/
python3 -m pip install -r requirements.txt
```

<h2>Настройка</h2>

Создайте файл `.env` в корне проекта и заполните его. Пример заполнения указан в файле `.env.dist`.
<u>Параметры</u>:
`TOKEN` - токен доступа к API Яндекс.Диска.
`LOCAL_DIR_PATH` - абсолютный путь к папке на локальном диске.
`CLOUD_DIR_PATH` - абсолютный путь к папке в Яндекс.Диске.
`LOG_FILE_PATH` - абсолютный путь, по которому будет храниться лог-файл.
`SYNCHRONIZATION_PERIOD` - период синхронизации папки в секундах.

<h2>Запуск</h2>

```
python3 yandex.py
```
