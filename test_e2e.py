"""E2E и нефункциональные API-тесты."""

import random
import uuid

import allure
import pytest
import requests

from conftest import (
    ACCEPT_HEADERS,
    BASE_URL,
    JSON_HEADERS,
    extract_item_id,
    request_with_retries,
)


def create_item(seller_id, name=None, price=1000, stats=None):
    """Создаёт объявление и возвращает response вместе с payload."""
    payload = {
        "name": name or f"E2E-{uuid.uuid4().hex[:6]}",
        "price": price,
        "sellerID": seller_id,
        "statistics": stats or {"contacts": 1, "likes": 1, "viewCount": 1},
    }
    resp = request_with_retries(
        "post",
        f"{BASE_URL}/api/1/item",
        json=payload,
        headers=JSON_HEADERS,
    )
    return resp, payload


def parse_item_response(data):
    """Нормализует response: объект или массив из одного элемента."""
    return data[0] if isinstance(data, list) else data


def parse_statistics_response(data):
    """Нормализует response statistics: объект или массив из одного элемента."""
    return data[0] if isinstance(data, list) else data


class TestE2E:
    """Сквозные сценарии."""

    @pytest.mark.e2e
    def test_create_then_get_by_id(self):
        sid = random.randint(111111, 999999)

        create_resp, payload = create_item(sid, name="E2E котёнок", price=7500)
        assert create_resp.status_code == 200, (
            f"Создание не удалось: {create_resp.status_code} {create_resp.text}"
        )

        item_id = extract_item_id(create_resp.json())
        assert item_id is not None, f"ID не найден в ответе: {create_resp.json()}"

        get_resp = requests.get(
            f"{BASE_URL}/api/1/item/{item_id}", headers=ACCEPT_HEADERS
        )
        assert get_resp.status_code == 200

        item = parse_item_response(get_resp.json())

        assert item["name"] == payload["name"]
        assert item["price"] == payload["price"]
        assert item["sellerId"] == sid

    @pytest.mark.e2e
    def test_create_then_find_in_seller_list(self):
        sid = random.randint(111111, 999999)

        create_resp, _ = create_item(sid, price=3000)
        assert create_resp.status_code == 200
        item_id = extract_item_id(create_resp.json())
        assert item_id is not None

        seller_resp = requests.get(
            f"{BASE_URL}/api/1/{sid}/item", headers=ACCEPT_HEADERS
        )
        assert seller_resp.status_code == 200

        ids_in_list = [it["id"] for it in seller_resp.json()]
        assert item_id in ids_in_list, (
            f"Объявление {item_id} не найдено в списке продавца {sid}"
        )

    @pytest.mark.e2e
    def test_create_then_check_statistic_v1(self):
        sid = random.randint(111111, 999999)
        expected_stats = {"contacts": 11, "likes": 22, "viewCount": 33}

        create_resp, _ = create_item(sid, price=1000, stats=expected_stats)
        assert create_resp.status_code == 200
        item_id = extract_item_id(create_resp.json())
        assert item_id is not None

        stat_resp = requests.get(
            f"{BASE_URL}/api/1/statistic/{item_id}",
            headers=ACCEPT_HEADERS,
        )
        assert stat_resp.status_code == 200

        stats = parse_statistics_response(stat_resp.json())

        assert stats["contacts"] == expected_stats["contacts"]
        assert stats["likes"] == expected_stats["likes"]
        assert stats["viewCount"] == expected_stats["viewCount"]

    @pytest.mark.e2e
    def test_create_then_check_statistic_v2(self):
        sid = random.randint(111111, 999999)
        expected_stats = {"contacts": 5, "likes": 10, "viewCount": 50}

        create_resp, _ = create_item(sid, price=2000, stats=expected_stats)
        assert create_resp.status_code == 200
        item_id = extract_item_id(create_resp.json())
        assert item_id is not None

        stat_resp = requests.get(
            f"{BASE_URL}/api/2/statistic/{item_id}",
            headers=ACCEPT_HEADERS,
        )
        assert stat_resp.status_code == 200

        stats = parse_statistics_response(stat_resp.json())

        assert stats["contacts"] == expected_stats["contacts"]
        assert stats["likes"] == expected_stats["likes"]
        assert stats["viewCount"] == expected_stats["viewCount"]

    @pytest.mark.e2e
    def test_create_multiple_then_count(self):
        sid = random.randint(111111, 999999)
        n = 5

        for i in range(n):
            resp, _ = create_item(sid, name=f"Котёнок {i + 1}", price=500 * (i + 1))
            assert resp.status_code == 200, (
                f"Создание #{i + 1}: {resp.status_code} {resp.text}"
            )

        seller_resp = requests.get(
            f"{BASE_URL}/api/1/{sid}/item", headers=ACCEPT_HEADERS
        )
        assert seller_resp.status_code == 200

        items = seller_resp.json()
        assert len(items) >= n, f"Ожидалось >= {n} объявлений, получено {len(items)}"

    @pytest.mark.e2e
    @allure.title("E2E: полный сценарий объявления")
    @allure.description(
        "Создание объявления, чтение по id, поиск у продавца и проверка статистики в двух версиях API."
    )
    def test_full_flow(self):
        sid = random.randint(111111, 999999)

        with allure.step("Создать объявление"):
            create_resp, payload = create_item(
                sid,
                name="Полный сценарий",
                price=12000,
                stats={"contacts": 3, "likes": 7, "viewCount": 25},
            )
        assert create_resp.status_code == 200
        item_id = extract_item_id(create_resp.json())
        assert item_id is not None

        with allure.step("Получить объявление по id"):
            get_resp = requests.get(
                f"{BASE_URL}/api/1/item/{item_id}", headers=ACCEPT_HEADERS
            )
        assert get_resp.status_code == 200
        item = parse_item_response(get_resp.json())
        assert item["name"] == payload["name"]

        with allure.step("Проверить объявление в списке продавца"):
            list_resp = requests.get(
                f"{BASE_URL}/api/1/{sid}/item", headers=ACCEPT_HEADERS
            )
        assert list_resp.status_code == 200
        assert item_id in [i["id"] for i in list_resp.json()]

        with allure.step("Проверить statistics в API v1"):
            stat1_resp = requests.get(
                f"{BASE_URL}/api/1/statistic/{item_id}",
                headers=ACCEPT_HEADERS,
            )
        assert stat1_resp.status_code == 200
        stat1 = parse_statistics_response(stat1_resp.json())
        assert stat1["contacts"] == payload["statistics"]["contacts"]

        with allure.step("Проверить statistics в API v2"):
            stat2_resp = requests.get(
                f"{BASE_URL}/api/2/statistic/{item_id}",
                headers=ACCEPT_HEADERS,
            )
        assert stat2_resp.status_code == 200
        stat2 = parse_statistics_response(stat2_resp.json())
        assert stat2["likes"] == payload["statistics"]["likes"]


class TestNonFunctional:
    """Нефункциональные проверки."""

    @pytest.mark.nonfunctional
    def test_create_response_time(self):
        sid = random.randint(111111, 999999)
        resp, _ = create_item(sid)

        assert resp.elapsed.total_seconds() < 3, (
            f"Слишком долгий ответ: {resp.elapsed.total_seconds():.2f}s"
        )

    @pytest.mark.nonfunctional
    def test_get_item_response_time(self):
        sid = random.randint(111111, 999999)
        create_resp, _ = create_item(sid)
        assert create_resp.status_code == 200

        item_id = extract_item_id(create_resp.json())
        assert item_id is not None

        get_resp = requests.get(
            f"{BASE_URL}/api/1/item/{item_id}", headers=ACCEPT_HEADERS
        )
        assert get_resp.elapsed.total_seconds() < 3, (
            f"Слишком долгий ответ: {get_resp.elapsed.total_seconds():.2f}s"
        )

    @pytest.mark.nonfunctional
    def test_response_content_type_is_json(self):
        sid = random.randint(111111, 999999)
        resp, _ = create_item(sid)

        content_type = resp.headers.get("Content-Type", "")
        assert "application/json" in content_type, (
            f"Ожидался Content-Type: application/json, получен: '{content_type}'"
        )
