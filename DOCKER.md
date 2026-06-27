# Docker guide

Этот проект можно запускать в Docker-контейнере. Это удобно для практики: зависимости ставятся внутрь образа, а на основной машине не нужно вручную создавать `venv`.

## Как это работает

`Dockerfile` описывает образ:

1. Берётся базовый образ `python:3.11-slim`.
2. Внутри контейнера создаётся рабочая папка `/app`.
3. Копируется `requirements.txt`.
4. Устанавливаются зависимости: `pytest`, `requests`, `allure-pytest`, `ruff`.
5. Копируется код проекта.
6. По умолчанию запускается команда `pytest -v`.

`.dockerignore` нужен, чтобы в Docker image не попадали лишние локальные файлы: `.git`, кеши, виртуальное окружение, отчёты, настройки IDE.

## Сборка образа

Из корня проекта:

```bash
docker build -t qa-avito-tests .
```

Что происходит:

- Docker читает `Dockerfile`;
- скачивает Python-образ;
- устанавливает зависимости;
- копирует проект;
- создаёт локальный образ с именем `qa-avito-tests`.

## Запуск всех тестов

```bash
docker run --rm qa-avito-tests
```

`--rm` означает: удалить контейнер после завершения. Сам image при этом остаётся.

Так как в `Dockerfile` указан:

```dockerfile
CMD ["pytest", "-v"]
```

контейнер по умолчанию запускает весь pytest-набор.

## Запуск отдельных команд

Можно переопределить команду после имени образа:

```bash
docker run --rm qa-avito-tests pytest -v -m positive
docker run --rm qa-avito-tests pytest -v -m negative
docker run --rm qa-avito-tests pytest -v -m e2e
docker run --rm qa-avito-tests pytest -v test_create_item.py
```

Ruff внутри контейнера:

```bash
docker run --rm qa-avito-tests python -m ruff check .
docker run --rm qa-avito-tests python -m ruff format --check .
```

## Allure results

Если просто запустить `pytest --alluredir=allure-results` внутри контейнера, результаты останутся внутри контейнера и исчезнут после `--rm`.

Чтобы сохранить их на хост-машину, нужно примонтировать папку:

```bash
docker run --rm -v "${PWD}/allure-results:/app/allure-results" qa-avito-tests pytest -v --alluredir=allure-results
```

После этого папка `allure-results` появится в проекте на твоей машине.

## Важные нюансы

- Контейнеру нужен доступ в интернет, потому что тесты ходят в `https://qa-internship.avito.com`.
- Если внешний API недоступен, тесты могут упасть не из-за Docker, а из-за сети или сервиса.
- Известные API-баги помечены как `xfail`, поэтому при текущем известном поведении API полный прогон должен быть зелёным.
- Docker не заменяет GitHub Actions. Docker нужен для локальной практики, а GitHub Actions запускает проверки в облаке при push или pull request.

## Частые команды

Посмотреть локальные images:

```bash
docker images
```

Посмотреть контейнеры:

```bash
docker ps -a
```

Удалить image:

```bash
docker rmi qa-avito-tests
```

Пересобрать image без кеша:

```bash
docker build --no-cache -t qa-avito-tests .
```
