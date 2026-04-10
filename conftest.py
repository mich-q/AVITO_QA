"""Общие фикстуры для всех тестов."""

import json
import random
import re
import time
import uuid

import allure
import pytest
import requests

BASE_URL = "https://qa-internship.avito.com"
ACCEPT_HEADERS = {"Accept": "application/json"}
JSON_HEADERS = {"Content-Type": "application/json", "Accept": "application/json"}
UUID_PATTERN = (
    r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}"
    r"-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
)


def extract_item_id(response_json):
    """Извлекает UUID объявления из документированного или фактического POST response."""
    if not isinstance(response_json, dict):
        return None

    direct_id = response_json.get("id")
    if isinstance(direct_id, str):
        return direct_id

    status = response_json.get("status")
    if isinstance(status, str):
        match = re.search(UUID_PATTERN, status)
        if match:
            return match.group(0)

    return None


def attach_json(name, payload):
    """Прикладывает JSON-структуру к Allure-отчёту."""
    allure.attach(
        json.dumps(payload, ensure_ascii=False, indent=2),
        name=name,
        attachment_type=allure.attachment_type.JSON,
    )


def attach_response(response, name="response"):
    """Прикладывает response к Allure-отчёту."""
    allure.attach(
        f"status_code={response.status_code}\ncontent_type={response.headers.get('Content-Type', '')}\n\n{response.text}",
        name=name,
        attachment_type=allure.attachment_type.TEXT,
    )


def request_with_retries(
    method, url, *, attempts=3, timeout=10, retryable_statuses=(502, 503, 504), **kwargs
):
    """Выполняет HTTP-запрос с короткими повторами при сетевых сбоях."""
    last_response = None

    for attempt in range(attempts):
        try:
            response = requests.request(method, url, timeout=timeout, **kwargs)
        except requests.RequestException:
            if attempt == attempts - 1:
                raise
            time.sleep(0.5 * (attempt + 1))
            continue

        last_response = response
        if response.status_code not in retryable_statuses:
            return response

        if attempt < attempts - 1:
            time.sleep(0.5 * (attempt + 1))

    return last_response


@pytest.fixture(scope="session")
def base_url():
    """Базовый URL сервиса."""
    return BASE_URL


@pytest.fixture()
def seller_id():
    """Случайный sellerID в допустимом диапазоне."""
    return random.randint(111111, 999999)


@pytest.fixture()
def item_payload(seller_id):
    """Валидный payload для создания объявления."""
    return {
        "name": f"Test Item {uuid.uuid4().hex[:8]}",
        "price": random.randint(100, 50000),
        "sellerID": seller_id,
        "statistics": {
            "contacts": random.randint(1, 20),
            "likes": random.randint(1, 30),
            "viewCount": random.randint(1, 100),
        },
    }


@pytest.fixture()
def created_item(base_url, item_payload):
    """Создаёт объявление и возвращает его ID, payload и sellerID."""
    response = request_with_retries(
        "post",
        f"{base_url}/api/1/item",
        json=item_payload,
        headers=JSON_HEADERS,
    )
    assert response.status_code == 200, (
        f"Фикстура не смогла создать объявление: {response.status_code} {response.text}"
    )

    data = response.json()
    item_id = extract_item_id(data)
    assert item_id is not None, (
        f"Фикстура не смогла извлечь ID из response: {data}\n"
        f"(BUG-03: POST response не соответствует documented contract)"
    )

    return {
        "item_id": item_id,
        "payload": item_payload,
        "seller_id": item_payload["sellerID"],
    }


@pytest.fixture()
def create_item_func(base_url):
    """Фабрика для создания объявления с произвольным payload."""

    def _create(payload):
        return request_with_retries(
            "post",
            f"{base_url}/api/1/item",
            json=payload,
            headers=JSON_HEADERS,
        )

    return _create


@pytest.fixture()
def unused_seller_id(base_url):
    """Подбирает sellerID, для которого сервис ещё не возвращает список объявлений."""

    checked_ids = set()

    for _ in range(200):
        sid = random.randint(950_000, 999_999)
        if sid in checked_ids:
            continue
        checked_ids.add(sid)

        response = requests.get(
            f"{base_url}/api/1/{sid}/item",
            headers=ACCEPT_HEADERS,
        )

        if response.status_code == 404:
            return sid

        if response.status_code == 200 and response.json() == []:
            return sid

    pytest.skip(
        "Не удалось подобрать sellerID без объявлений для проверки пустого списка"
    )
