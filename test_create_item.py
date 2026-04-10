"""Тесты для POST /api/1/item."""

import uuid

import allure
import pytest
import requests

from conftest import JSON_HEADERS, attach_json, attach_response, extract_item_id


def has_documented_item_shape(data):
    """Проверяет, что response содержит все поля из документации."""
    required_fields = ("id", "sellerId", "name", "price", "statistics", "createdAt")
    return isinstance(data, dict) and all(field in data for field in required_fields)


class TestCreateItemPositive:
    """Позитивные сценарии."""

    @pytest.mark.positive
    @allure.title("POST /api/1/item: успешное создание объявления")
    @allure.description(
        "Проверяет, что валидный payload создаёт объявление и возвращает идентификатор."
    )
    def test_create_item_success(self, base_url, seller_id):
        payload = {
            "name": "Персидский котёнок",
            "price": 25000,
            "sellerID": seller_id,
            "statistics": {"contacts": 2, "likes": 5, "viewCount": 20},
        }

        with allure.step("Отправить валидный POST /api/1/item"):
            attach_json("create_item_payload", payload)
            response = requests.post(
                f"{base_url}/api/1/item", json=payload, headers=JSON_HEADERS
            )
            attach_response(response, "create_item_response")

        assert response.status_code == 200
        item_id = extract_item_id(response.json())
        assert item_id is not None, (
            f"Не удалось извлечь ID из ответа: {response.json()}\n"
            f"(BUG-03: ответ не соответствует документации)"
        )

    @pytest.mark.positive
    @allure.title("POST /api/1/item: формат ответа соответствует документации")
    @allure.description(
        "Фиксирует BUG-03, когда сервис возвращает status-строку вместо полного объекта объявления."
    )
    def test_create_item_response_format(self, base_url, seller_id):
        """Проверка формата response при создании объявления."""
        payload = {
            "name": "Котёнок",
            "price": 1000,
            "sellerID": seller_id,
            "statistics": {"contacts": 1, "likes": 1, "viewCount": 1},
        }

        with allure.step("Создать объявление валидным запросом"):
            attach_json("create_item_payload", payload)
            response = requests.post(
                f"{base_url}/api/1/item", json=payload, headers=JSON_HEADERS
            )
            attach_response(response, "create_item_response")

        assert response.status_code == 200
        data = response.json()

        expected_fields = ("id", "sellerId", "name", "price", "statistics", "createdAt")
        has_all_fields = has_documented_item_shape(data)

        assert has_all_fields, (
            f"BUG-03: Ответ не соответствует документации.\n"
            f"Ожидались поля: {expected_fields}\n"
            f"Фактический ответ: {data}"
        )

    @pytest.mark.positive
    def test_create_item_unique_ids(self, base_url, seller_id):
        """Два одинаковых запроса создают объявления с разными ID."""
        payload = {
            "name": "Одинаковое объявление",
            "price": 1000,
            "sellerID": seller_id,
            "statistics": {"contacts": 1, "likes": 1, "viewCount": 1},
        }
        resp1 = requests.post(
            f"{base_url}/api/1/item", json=payload, headers=JSON_HEADERS
        )
        resp2 = requests.post(
            f"{base_url}/api/1/item", json=payload, headers=JSON_HEADERS
        )

        assert resp1.status_code == 200
        assert resp2.status_code == 200

        id1 = extract_item_id(resp1.json())
        id2 = extract_item_id(resp2.json())
        assert id1 != id2, "Два одинаковых POST должны возвращать разные ID"

    @pytest.mark.positive
    def test_create_item_zero_price(self, base_url, seller_id):
        """Проверка граничного значения price = 0."""
        payload = {
            "name": "Бесплатно",
            "price": 0,
            "sellerID": seller_id,
            "statistics": {"contacts": 1, "likes": 1, "viewCount": 1},
        }
        response = requests.post(
            f"{base_url}/api/1/item", json=payload, headers=JSON_HEADERS
        )

        assert response.status_code in (200, 400), (
            f"Неожиданный статус для price=0: {response.status_code}"
        )

    @pytest.mark.positive
    @allure.title("POST /api/1/item: нулевая statistics должна приниматься")
    @allure.description(
        "Фиксирует BUG-08, когда валидный payload с нулевыми счётчиками отклоняется."
    )
    def test_create_item_zero_statistics(self, base_url, seller_id):
        """Проверка нулевых значений в statistics."""
        payload = {
            "name": "Новое объявление",
            "price": 5000,
            "sellerID": seller_id,
            "statistics": {"contacts": 0, "likes": 0, "viewCount": 0},
        }

        with allure.step("Отправить запрос с нулевыми значениями statistics"):
            attach_json("zero_statistics_payload", payload)
            response = requests.post(
                f"{base_url}/api/1/item", json=payload, headers=JSON_HEADERS
            )
            attach_response(response, "zero_statistics_response")

        assert response.status_code == 200, (
            f"BUG-08: Ожидался 200 для нулевой statistics, "
            f"получен {response.status_code}. Подробнее в BUGS.md"
        )


class TestCreateItemNegative:
    """Негативные сценарии."""

    @pytest.mark.negative
    def test_create_item_without_name(self, base_url, seller_id):
        payload = {
            "price": 1000,
            "sellerID": seller_id,
            "statistics": {"contacts": 1, "likes": 1, "viewCount": 1},
        }
        response = requests.post(
            f"{base_url}/api/1/item", json=payload, headers=JSON_HEADERS
        )

        assert response.status_code == 400

    @pytest.mark.negative
    def test_create_item_without_price(self, base_url, seller_id):
        payload = {
            "name": "Котёнок",
            "sellerID": seller_id,
            "statistics": {"contacts": 1, "likes": 1, "viewCount": 1},
        }
        response = requests.post(
            f"{base_url}/api/1/item", json=payload, headers=JSON_HEADERS
        )

        assert response.status_code == 400

    @pytest.mark.negative
    def test_create_item_without_seller_id(self, base_url):
        payload = {
            "name": "Котёнок",
            "price": 1000,
            "statistics": {"contacts": 1, "likes": 1, "viewCount": 1},
        }
        response = requests.post(
            f"{base_url}/api/1/item", json=payload, headers=JSON_HEADERS
        )

        assert response.status_code == 400

    @pytest.mark.negative
    def test_create_item_empty_body(self, base_url):
        response = requests.post(
            f"{base_url}/api/1/item", json={}, headers=JSON_HEADERS
        )

        assert response.status_code == 400

    @pytest.mark.negative
    @allure.title("POST /api/1/item: отрицательная цена должна отклоняться")
    def test_create_item_negative_price(self, base_url, seller_id):
        """BUG-02: сервер принимает отрицательный price."""
        payload = {
            "name": "Котёнок",
            "price": -500,
            "sellerID": seller_id,
            "statistics": {"contacts": 1, "likes": 1, "viewCount": 1},
        }

        with allure.step("Отправить запрос с отрицательной ценой"):
            attach_json("negative_price_payload", payload)
            response = requests.post(
                f"{base_url}/api/1/item", json=payload, headers=JSON_HEADERS
            )
            attach_response(response, "negative_price_response")

        assert response.status_code == 400, (
            f"BUG-02: Ожидался 400 для отрицательной цены, "
            f"получен {response.status_code}. Подробнее в BUGS.md"
        )

    @pytest.mark.negative
    def test_create_item_price_as_string(self, base_url, seller_id):
        payload = {
            "name": "Котёнок",
            "price": "дорого",
            "sellerID": seller_id,
        }
        response = requests.post(
            f"{base_url}/api/1/item", json=payload, headers=JSON_HEADERS
        )

        assert response.status_code == 400

    @pytest.mark.negative
    def test_create_item_seller_id_as_string(self, base_url):
        payload = {
            "name": "Котёнок",
            "price": 1000,
            "sellerID": "abc",
        }
        response = requests.post(
            f"{base_url}/api/1/item", json=payload, headers=JSON_HEADERS
        )

        assert response.status_code == 400

    @pytest.mark.negative
    @allure.title("POST /api/1/item: отрицательная statistics должна отклоняться")
    def test_create_item_negative_statistics(self, base_url, seller_id):
        """BUG-01: сервер принимает отрицательную statistics."""
        payload = {
            "name": "Neg Stats",
            "price": 100,
            "sellerID": seller_id,
            "statistics": {"contacts": -1, "likes": -5, "viewCount": -10},
        }

        with allure.step("Отправить запрос с отрицательными счётчиками"):
            attach_json("negative_statistics_payload", payload)
            response = requests.post(
                f"{base_url}/api/1/item", json=payload, headers=JSON_HEADERS
            )
            attach_response(response, "negative_statistics_response")

        assert response.status_code == 400, (
            f"BUG-01: Ожидался 400 для отрицательной statistics, "
            f"получен {response.status_code}. Подробнее в BUGS.md"
        )

    @pytest.mark.negative
    def test_create_item_negative_seller_id(self, base_url):
        payload = {
            "name": "Котёнок",
            "price": 1000,
            "sellerID": -123456,
        }
        response = requests.post(
            f"{base_url}/api/1/item", json=payload, headers=JSON_HEADERS
        )

        assert response.status_code == 400


class TestCreateItemCornerCases:
    """Граничные и нестандартные сценарии."""

    @pytest.mark.corner_case
    def test_create_item_not_idempotent(self, base_url, seller_id):
        """POST не должен быть идемпотентным."""
        payload = {
            "name": f"Идемпотентность {uuid.uuid4().hex[:4]}",
            "price": 500,
            "sellerID": seller_id,
            "statistics": {"contacts": 1, "likes": 1, "viewCount": 1},
        }
        resp1 = requests.post(
            f"{base_url}/api/1/item", json=payload, headers=JSON_HEADERS
        )
        resp2 = requests.post(
            f"{base_url}/api/1/item", json=payload, headers=JSON_HEADERS
        )

        assert resp1.status_code == 200
        assert resp2.status_code == 200
        assert extract_item_id(resp1.json()) != extract_item_id(resp2.json())

    @pytest.mark.corner_case
    def test_create_item_long_name(self, base_url, seller_id):
        payload = {
            "name": "А" * 5000,
            "price": 100,
            "sellerID": seller_id,
        }
        response = requests.post(
            f"{base_url}/api/1/item", json=payload, headers=JSON_HEADERS
        )

        assert response.status_code in (200, 400), (
            f"Неожиданный статус: {response.status_code}"
        )

    @pytest.mark.corner_case
    def test_create_item_xss_in_name(self, base_url, seller_id):
        payload = {
            "name": "<script>alert('xss')</script>",
            "price": 100,
            "sellerID": seller_id,
        }
        response = requests.post(
            f"{base_url}/api/1/item", json=payload, headers=JSON_HEADERS
        )

        assert response.status_code != 500

    @pytest.mark.corner_case
    def test_create_item_seller_id_zero(self, base_url):
        payload = {
            "name": "Котёнок",
            "price": 1000,
            "sellerID": 0,
        }
        response = requests.post(
            f"{base_url}/api/1/item", json=payload, headers=JSON_HEADERS
        )

        assert response.status_code == 400

    @pytest.mark.corner_case
    @pytest.mark.parametrize("price", [0, 1, 100000, 999999999])
    def test_create_item_price_boundary(self, base_url, seller_id, price):
        payload = {
            "name": f"Цена {price}",
            "price": price,
            "sellerID": seller_id,
            "statistics": {"contacts": 1, "likes": 1, "viewCount": 1},
        }
        response = requests.post(
            f"{base_url}/api/1/item", json=payload, headers=JSON_HEADERS
        )

        assert response.status_code in (200, 400), (
            f"Неожиданный статус для price={price}: {response.status_code}"
        )
