"""Тесты для GET /api/1/item/:id."""

import uuid

import allure
import pytest
import requests

HEADERS = {"Accept": "application/json"}


def parse_item_response(data):
    """Нормализует response: объект или массив из одного элемента."""
    return data[0] if isinstance(data, list) else data


class TestGetItemPositive:
    """Позитивные сценарии."""

    @pytest.mark.positive
    def test_get_existing_item(self, base_url, created_item):
        item_id = created_item["item_id"]

        response = requests.get(f"{base_url}/api/1/item/{item_id}", headers=HEADERS)

        assert response.status_code == 200, (
            f"Ожидался 200, получен {response.status_code}: {response.text}"
        )

        item = parse_item_response(response.json())

        for field in ("id", "name", "price", "sellerId", "createdAt"):
            assert field in item, f"Поле '{field}' отсутствует в ответе: {item}"

    @pytest.mark.positive
    @allure.title("GET /api/1/item/{id}: сервис должен возвращать объект объявления")
    def test_get_item_response_is_object(self, base_url, created_item):
        item_id = created_item["item_id"]

        with allure.step("Запросить объявление по идентификатору"):
            response = requests.get(f"{base_url}/api/1/item/{item_id}", headers=HEADERS)
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, dict), (
            f"BUG-04: Ожидался объект dict, получен {type(data).__name__}.\n"
            f"API возвращает массив вместо одного объявления. Подробнее в BUGS.md"
        )

    @pytest.mark.positive
    def test_get_item_data_matches_created(self, base_url, created_item):
        item_id = created_item["item_id"]
        payload = created_item["payload"]

        response = requests.get(f"{base_url}/api/1/item/{item_id}", headers=HEADERS)
        assert response.status_code == 200

        item = parse_item_response(response.json())

        assert item["name"] == payload["name"], (
            f"name: ожидалось '{payload['name']}', получено '{item['name']}'"
        )
        assert item["price"] == payload["price"], (
            f"price: ожидалось {payload['price']}, получено {item['price']}"
        )
        assert item["sellerId"] == payload["sellerID"], (
            f"sellerId: ожидалось {payload['sellerID']}, получено {item['sellerId']}"
        )

    @pytest.mark.positive
    def test_get_item_has_statistics(self, base_url, created_item):
        item_id = created_item["item_id"]

        response = requests.get(f"{base_url}/api/1/item/{item_id}", headers=HEADERS)
        assert response.status_code == 200

        item = parse_item_response(response.json())

        assert "statistics" in item, f"Поле 'statistics' отсутствует: {item}"

        stats = item["statistics"]
        for field in ("likes", "viewCount", "contacts"):
            assert field in stats, f"Поле '{field}' отсутствует в statistics: {stats}"


class TestGetItemNegative:
    """Негативные сценарии."""

    @pytest.mark.negative
    def test_get_nonexistent_item(self, base_url):
        fake_id = str(uuid.uuid4())

        response = requests.get(f"{base_url}/api/1/item/{fake_id}", headers=HEADERS)

        assert response.status_code == 404, (
            f"Ожидался 404, получен {response.status_code}: {response.text}"
        )

    @pytest.mark.negative
    def test_get_item_invalid_id_format(self, base_url):
        response = requests.get(f"{base_url}/api/1/item/not-a-uuid", headers=HEADERS)

        assert response.status_code in (400, 404), (
            f"Ожидался 400/404, получен {response.status_code}"
        )

    @pytest.mark.negative
    def test_get_item_numeric_id(self, base_url):
        response = requests.get(f"{base_url}/api/1/item/12345", headers=HEADERS)

        assert response.status_code in (400, 404), (
            f"Ожидался 400/404, получен {response.status_code}"
        )

    @pytest.mark.negative
    def test_get_item_empty_id(self, base_url):
        response = requests.get(f"{base_url}/api/1/item/", headers=HEADERS)

        assert response.status_code in (400, 404, 405), (
            f"Неожиданный статус: {response.status_code}"
        )


class TestGetItemCornerCases:
    """Граничные и нестандартные сценарии."""

    @pytest.mark.corner_case
    def test_get_item_idempotent(self, base_url, created_item):
        item_id = created_item["item_id"]

        results = []
        for _ in range(3):
            resp = requests.get(f"{base_url}/api/1/item/{item_id}", headers=HEADERS)
            assert resp.status_code == 200
            results.append(resp.json())

        assert results[0] == results[1] == results[2], "GET должен быть идемпотентным"

    @pytest.mark.corner_case
    def test_get_item_sql_injection(self, base_url):
        response = requests.get(
            f"{base_url}/api/1/item/' OR 1=1 --",
            headers=HEADERS,
        )

        assert response.status_code != 500, (
            f"Сервер вернул 500 на SQL injection: {response.text}"
        )
        assert response.status_code in (400, 404)
