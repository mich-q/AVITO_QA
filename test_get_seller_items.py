"""Тесты для GET /api/1/:sellerID/item."""

import random

import allure
import pytest
import requests

from conftest import ACCEPT_HEADERS, extract_item_id


class TestGetSellerItemsPositive:
    """Позитивные сценарии."""

    @pytest.mark.positive
    def test_get_seller_items_returns_list(self, base_url, created_item):
        sid = created_item["seller_id"]

        response = requests.get(f"{base_url}/api/1/{sid}/item", headers=ACCEPT_HEADERS)

        assert response.status_code == 200, (
            f"Ожидался 200, получен {response.status_code}: {response.text}"
        )
        data = response.json()
        assert isinstance(data, list), f"Ожидался массив, получен {type(data)}: {data}"

    @pytest.mark.positive
    def test_get_seller_items_contains_created(self, base_url, created_item):
        sid = created_item["seller_id"]
        item_id = created_item["item_id"]

        response = requests.get(f"{base_url}/api/1/{sid}/item", headers=ACCEPT_HEADERS)
        assert response.status_code == 200

        ids_in_list = [item["id"] for item in response.json()]
        assert item_id in ids_in_list, (
            f"Объявление {item_id} не найдено в списке продавца {sid}"
        )

    @pytest.mark.positive
    def test_get_seller_items_all_belong_to_seller(self, base_url, created_item):
        sid = created_item["seller_id"]

        response = requests.get(f"{base_url}/api/1/{sid}/item", headers=ACCEPT_HEADERS)
        assert response.status_code == 200

        for item in response.json():
            assert item["sellerId"] == sid, (
                f"Объявление {item['id']} имеет sellerId={item['sellerId']}, ожидался {sid}"
            )

    @pytest.mark.positive
    def test_get_seller_multiple_items(self, base_url, create_item_func):
        sid = random.randint(111111, 999999)
        created_ids = []

        for i in range(3):
            payload = {
                "name": f"Котёнок {i + 1}",
                "price": 1000 * (i + 1),
                "sellerID": sid,
                "statistics": {"contacts": 1, "likes": 1, "viewCount": 1},
            }
            resp = create_item_func(payload)
            assert resp.status_code == 200, (
                f"Создание #{i + 1}: {resp.status_code} {resp.text}"
            )
            item_id = extract_item_id(resp.json())
            assert item_id is not None
            created_ids.append(item_id)

        response = requests.get(f"{base_url}/api/1/{sid}/item", headers=ACCEPT_HEADERS)
        assert response.status_code == 200

        ids_in_list = [item["id"] for item in response.json()]
        for item_id in created_ids:
            assert item_id in ids_in_list, (
                f"Созданное объявление {item_id} не найдено в списке продавца"
            )

    @pytest.mark.positive
    @allure.title(
        "GET /api/1/{sellerID}/item: новый продавец должен возвращать пустой список"
    )
    def test_get_seller_items_empty_for_new_seller(self, base_url, unused_seller_id):
        with allure.step("Запросить список объявлений для sellerID без объявлений"):
            response = requests.get(
                f"{base_url}/api/1/{unused_seller_id}/item",
                headers=ACCEPT_HEADERS,
            )

        assert response.status_code == 200, (
            f"BUG-06: Ожидался 200 с пустым массивом, получен {response.status_code}. "
            f"Подробнее в BUGS.md"
        )
        assert response.json() == [], (
            f"BUG-06: Ожидался пустой массив [], получен: {response.json()}"
        )


class TestGetSellerItemsNegative:
    """Негативные сценарии."""

    @pytest.mark.negative
    def test_get_seller_items_string_id(self, base_url):
        response = requests.get(
            f"{base_url}/api/1/not_a_number/item", headers=ACCEPT_HEADERS
        )

        assert response.status_code == 400, (
            f"Ожидался 400 для строкового sellerID, получен {response.status_code}"
        )

    @pytest.mark.negative
    def test_get_seller_items_float_id(self, base_url):
        response = requests.get(
            f"{base_url}/api/1/123.456/item", headers=ACCEPT_HEADERS
        )

        assert response.status_code == 400, (
            f"Ожидался 400 для дробного sellerID, получен {response.status_code}"
        )

    @pytest.mark.negative
    def test_get_seller_items_negative_id(self, base_url):
        response = requests.get(f"{base_url}/api/1/-1/item", headers=ACCEPT_HEADERS)

        assert response.status_code in (200, 400), (
            f"Неожиданный статус: {response.status_code}"
        )


class TestGetSellerItemsCornerCases:
    """Граничные и нестандартные сценарии."""

    @pytest.mark.corner_case
    def test_get_seller_items_idempotent(self, base_url, created_item):
        sid = created_item["seller_id"]

        resp1 = requests.get(f"{base_url}/api/1/{sid}/item", headers=ACCEPT_HEADERS)
        resp2 = requests.get(f"{base_url}/api/1/{sid}/item", headers=ACCEPT_HEADERS)

        assert resp1.status_code == 200
        assert resp2.status_code == 200
        assert resp1.json() == resp2.json(), "GET должен быть идемпотентным"

    @pytest.mark.corner_case
    def test_get_seller_items_zero_id(self, base_url):
        response = requests.get(f"{base_url}/api/1/0/item", headers=ACCEPT_HEADERS)

        assert response.status_code in (200, 400), (
            f"Неожиданный статус: {response.status_code}"
        )

    @pytest.mark.corner_case
    def test_get_seller_items_huge_id(self, base_url):
        response = requests.get(
            f"{base_url}/api/1/99999999999999999999/item",
            headers=ACCEPT_HEADERS,
        )

        assert response.status_code != 500, (
            f"Сервер вернул 500 на очень большой sellerID: {response.text}"
        )
