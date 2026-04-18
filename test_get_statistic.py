"""Тесты для endpoints статистики объявления."""

import uuid

import allure
import pytest
import requests

HEADERS = {"Accept": "application/json"}


def parse_statistics_response(data):
    """Нормализует response: объект или массив из одного элемента."""
    return data[0] if isinstance(data, list) else data


class TestGetStatisticV1Positive:
    """Позитивные сценарии для /api/1/statistic/:id."""

    @pytest.mark.positive
    def test_get_statistic_v1_returns_200(self, base_url, created_item):
        item_id = created_item["item_id"]

        response = requests.get(
            f"{base_url}/api/1/statistic/{item_id}", headers=HEADERS
        )

        assert response.status_code == 200, (
            f"Ожидался 200, получен {response.status_code}: {response.text}"
        )

    @pytest.mark.positive
    @allure.title(
        "GET /api/1/statistic/{id}: сервис должен возвращать массив statistics"
    )
    def test_get_statistic_v1_response_is_list(self, base_url, created_item):
        item_id = created_item["item_id"]

        with allure.step("Запросить statistics для существующего объявления"):
            response = requests.get(
                f"{base_url}/api/1/statistic/{item_id}", headers=HEADERS
            )
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list), (
            f"Ожидался массив list, получен {type(data).__name__}: {data}"
        )
        assert len(data) >= 1, "Ожидался непустой массив statistics"

    @pytest.mark.positive
    def test_get_statistic_v1_has_required_fields(self, base_url, created_item):
        item_id = created_item["item_id"]

        response = requests.get(
            f"{base_url}/api/1/statistic/{item_id}", headers=HEADERS
        )
        assert response.status_code == 200

        stats = parse_statistics_response(response.json())

        for field in ("likes", "viewCount", "contacts"):
            assert field in stats, f"Поле '{field}' отсутствует в ответе: {stats}"

    @pytest.mark.positive
    def test_get_statistic_v1_values_match(self, base_url, created_item):
        item_id = created_item["item_id"]
        expected = created_item["payload"]["statistics"]

        response = requests.get(
            f"{base_url}/api/1/statistic/{item_id}", headers=HEADERS
        )
        assert response.status_code == 200

        stats = parse_statistics_response(response.json())

        assert stats["contacts"] == expected["contacts"], (
            f"contacts: ожидалось {expected['contacts']}, получено {stats['contacts']}"
        )
        assert stats["likes"] == expected["likes"], (
            f"likes: ожидалось {expected['likes']}, получено {stats['likes']}"
        )
        assert stats["viewCount"] == expected["viewCount"], (
            f"viewCount: ожидалось {expected['viewCount']}, получено {stats['viewCount']}"
        )

    @pytest.mark.positive
    def test_get_statistic_v1_values_are_integers(self, base_url, created_item):
        item_id = created_item["item_id"]

        response = requests.get(
            f"{base_url}/api/1/statistic/{item_id}", headers=HEADERS
        )
        assert response.status_code == 200

        stats = parse_statistics_response(response.json())

        assert isinstance(stats["likes"], int), "likes должно быть int"
        assert isinstance(stats["viewCount"], int), "viewCount должно быть int"
        assert isinstance(stats["contacts"], int), "contacts должно быть int"


class TestGetStatisticV2Positive:
    """Позитивные сценарии для /api/2/statistic/:id."""

    @pytest.mark.positive
    def test_get_statistic_v2_returns_200(self, base_url, created_item):
        item_id = created_item["item_id"]

        response = requests.get(
            f"{base_url}/api/2/statistic/{item_id}", headers=HEADERS
        )

        assert response.status_code == 200, (
            f"Ожидался 200, получен {response.status_code}: {response.text}"
        )

    @pytest.mark.positive
    def test_get_statistic_v2_has_required_fields(self, base_url, created_item):
        item_id = created_item["item_id"]

        response = requests.get(
            f"{base_url}/api/2/statistic/{item_id}", headers=HEADERS
        )
        assert response.status_code == 200

        stats = parse_statistics_response(response.json())

        for field in ("likes", "viewCount", "contacts"):
            assert field in stats, f"Поле '{field}' отсутствует в ответе v2: {stats}"

    @pytest.mark.positive
    def test_get_statistic_v1_v2_same_result(self, base_url, created_item):
        item_id = created_item["item_id"]

        resp_v1 = requests.get(f"{base_url}/api/1/statistic/{item_id}", headers=HEADERS)
        resp_v2 = requests.get(f"{base_url}/api/2/statistic/{item_id}", headers=HEADERS)

        assert resp_v1.status_code == 200
        assert resp_v2.status_code == 200

        s1 = parse_statistics_response(resp_v1.json())
        s2 = parse_statistics_response(resp_v2.json())

        assert s1["likes"] == s2["likes"], "likes расходятся между v1 и v2"
        assert s1["viewCount"] == s2["viewCount"], "viewCount расходятся между v1 и v2"
        assert s1["contacts"] == s2["contacts"], "contacts расходятся между v1 и v2"


class TestGetStatisticNegative:
    """Негативные сценарии."""

    @pytest.mark.negative
    def test_get_statistic_v1_nonexistent(self, base_url):
        response = requests.get(
            f"{base_url}/api/1/statistic/{uuid.uuid4()}",
            headers=HEADERS,
        )

        assert response.status_code == 404, (
            f"Ожидался 404, получен {response.status_code}: {response.text}"
        )

    @pytest.mark.negative
    def test_get_statistic_v2_nonexistent(self, base_url):
        response = requests.get(
            f"{base_url}/api/2/statistic/{uuid.uuid4()}",
            headers=HEADERS,
        )

        assert response.status_code == 404, (
            f"Ожидался 404, получен {response.status_code}: {response.text}"
        )

    @pytest.mark.negative
    def test_get_statistic_v1_invalid_id(self, base_url):
        response = requests.get(
            f"{base_url}/api/1/statistic/invalid-id",
            headers=HEADERS,
        )

        assert response.status_code in (400, 404)

    @pytest.mark.negative
    def test_get_statistic_v2_invalid_id(self, base_url):
        response = requests.get(
            f"{base_url}/api/2/statistic/invalid-id",
            headers=HEADERS,
        )

        assert response.status_code in (400, 404)


class TestGetStatisticCornerCases:
    """Граничные и нестандартные сценарии."""

    @pytest.mark.corner_case
    def test_get_statistic_v1_idempotent(self, base_url, created_item):
        item_id = created_item["item_id"]

        results = []
        for _ in range(3):
            resp = requests.get(
                f"{base_url}/api/1/statistic/{item_id}", headers=HEADERS
            )
            assert resp.status_code == 200
            results.append(resp.json())

        assert results[0] == results[1] == results[2], (
            "GET statistics должен быть идемпотентным"
        )

    @pytest.mark.corner_case
    def test_get_statistic_v2_idempotent(self, base_url, created_item):
        item_id = created_item["item_id"]

        results = []
        for _ in range(3):
            resp = requests.get(
                f"{base_url}/api/2/statistic/{item_id}", headers=HEADERS
            )
            assert resp.status_code == 200
            results.append(resp.json())

        assert results[0] == results[1] == results[2], (
            "GET statistics v2 должен быть идемпотентным"
        )

    @pytest.mark.corner_case
    def test_get_statistic_sql_injection(self, base_url):
        response = requests.get(
            f"{base_url}/api/1/statistic/' OR 1=1 --",
            headers=HEADERS,
        )

        assert response.status_code != 500, (
            f"Сервер вернул 500 на SQL injection: {response.text}"
        )
        assert response.status_code in (400, 404)
