# Avito QA Internship - API Tests

Набор API-тестов для `https://qa-internship.avito.com`, написанный на `pytest` и `requests`.

## Покрытые endpoints

- `POST /api/1/item`
- `GET /api/1/item/:id`
- `GET /api/1/:sellerID/item`
- `GET /api/1/statistic/:id`
- `GET /api/2/statistic/:id`

## Структура проекта

```text
.
|-- .gitignore
|-- .dockerignore
|-- .github/
|   `-- workflows/
|       `-- ci.yml
|-- Dockerfile
|-- DOCKER.md
|-- README.md
|-- conftest.py
|-- pytest.ini
|-- pyproject.toml
|-- requirements.txt
|-- test_create_item.py
|-- test_get_item.py
|-- test_get_seller_items.py
|-- test_get_statistic.py
|-- test_e2e.py
|-- TESTCASES.md
|-- BUGS.md
|-- OBSERVATIONS.md
|-- PROJECT_DEFENSE.md
|-- allure-example.html
`-- task1.md
```

Локально после запусков могут появляться служебные директории `.pytest_cache/`, `.ruff_cache/`, `__pycache__/`, `allure-results/`. Они не считаются частью исходников и исключены через `.gitignore`.

## Установка

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / macOS
source venv/bin/activate

pip install -r requirements.txt
```

## Запуск тестов

```bash
# все тесты
pytest -v

# запуск по markers
pytest -v -m positive
pytest -v -m negative
pytest -v -m corner_case
pytest -v -m e2e
pytest -v -m nonfunctional

# запуск одного файла
pytest -v test_create_item.py
```

## Allure report

```bash
pytest -v --alluredir=allure-results
allure serve allure-results
```

- В проекте подключён `allure-pytest`.
- Для ключевых сценариев добавлены `title`, `description`, `step` и вложения request/response.
- Папка `allure-results` добавлена в `.gitignore`, чтобы не хранить сырые результаты в репозитории.
- В репозиторий приложен пример артефакта отчёта: [allure-example.html](allure-example.html).

## Линтинг

```bash
python -m ruff check .
python -m ruff format --check .
python -m ruff format .
```

## Текущее состояние

- В проекте задокументировано `6` подтверждённых API bugs в [BUGS.md](BUGS.md).
- Известные баги помечены через `pytest.mark.xfail`, чтобы CI/CD pipeline оставался зелёным и при этом не скрывал дефекты.
- Ожидаемый результат полного прогона при текущем поведении API: `62 passed, 6 xfailed`.
- Эти `6 xfailed` ожидаемы: они фиксируют реальные дефекты API, описанные в [BUGS.md](BUGS.md).
- Метка `xfail(strict=True)` специально сделает прогон красным, если API исправят, а тест всё ещё будет помечен как ожидаемо падающий.

## Примечания

- Набор тестов зависит от доступности внешнего Avito API.
- Проверки response выполняются прямо в тестах и фикстурах, чтобы проект было проще объяснить на собеседовании.
