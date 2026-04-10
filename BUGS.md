# BUGS.md - Дефекты, найденные в API

**Service:** `https://qa-internship.avito.com`

**Актуальный status полного прогона на 10 апреля 2026:** `61 passed, 6 failed`

Этим падениям соответствуют следующие Bugs:
- `BUG-01` принимается отрицательная statistics
- `BUG-02` принимается отрицательный price
- `BUG-03` format response у `POST /api/1/item` не соответствует документации
- `BUG-04` `GET /api/1/item/:id` возвращает массив вместо объекта
- `BUG-05` `GET /api/1/statistic/:id` возвращает массив вместо объекта
- `BUG-08` валидный create request с нулевой statistics отклоняется с `400`

---

## BUG-01: POST /api/1/item принимает отрицательные значения statistics

**Priority:** P1 - High

**Краткое описание:**
API принимает отрицательные значения в полях `likes`, `viewCount` и `contacts` и возвращает `200 OK`.

**Шаги воспроизведения:**
1. Отправить `POST https://qa-internship.avito.com/api/1/item` с body:
```json
{
  "sellerID": 224947,
  "name": "Test Item",
  "price": 100,
  "statistics": {
    "contacts": -1,
    "likes": -5,
    "viewCount": -10
  }
}
```
2. Проверить `status code` и body ответа.

**Фактический результат:**
`200 OK` - item создаётся с отрицательной statistics.

**Ожидаемый результат:**
`400 Bad Request` - отрицательные значения statistics должны отклоняться валидацией.

**Severity:** High

**Окружение:**
- Host: `https://qa-internship.avito.com`
- Endpoint: `POST /api/1/item`
- Client: `pytest` + `requests`
- Дата прогона: `2026-04-10`

**Тест, фиксирующий дефект:**
`test_create_item.py::TestCreateItemNegative::test_create_item_negative_statistics`

---

## BUG-02: POST /api/1/item принимает отрицательный price

**Priority:** P1 - High

**Краткое описание:**
API принимает `price < 0` и возвращает `200 OK`.

**Шаги воспроизведения:**
1. Отправить `POST /api/1/item` с `"price": -500`.

**Фактический результат:**
`200 OK` - item создаётся с `price = -500`.

**Ожидаемый результат:**
`400 Bad Request` - отрицательный `price` недопустим.

**Severity:** High

**Окружение:**
- Host: `https://qa-internship.avito.com`
- Endpoint: `POST /api/1/item`
- Client: `pytest` + `requests`
- Дата прогона: `2026-04-10`

**Тест, фиксирующий дефект:**
`test_create_item.py::TestCreateItemNegative::test_create_item_negative_price`

---

## BUG-03: Формат response у POST /api/1/item не соответствует документации

**Priority:** P2 - Medium

**Краткое описание:**
Согласно контракту, успешный create response должен возвращать полный объект item с полями `id`, `sellerId`, `name`, `price`, `statistics`, `createdAt`.
Фактически API возвращает только строку в поле `status`.

**Шаги воспроизведения:**
1. Отправить валидный `POST /api/1/item`.
2. Сравнить body ответа с документацией.

**Фактический результат:**
```json
{ "status": "Сохранили объявление - <uuid>" }
```

**Ожидаемый результат:**
```json
{
  "id": "<uuid>",
  "sellerId": 123456,
  "name": "...",
  "price": 1000,
  "statistics": { "likes": 0, "viewCount": 0, "contacts": 0 },
  "createdAt": "..."
}
```

**Влияние:**
Клиентский код не может получить `id` напрямую и вынужден извлекать его из строки `status`, что нарушает API contract.

**Severity:** Medium

**Окружение:**
- Host: `https://qa-internship.avito.com`
- Endpoint: `POST /api/1/item`
- Client: `pytest` + `requests`
- Дата прогона: `2026-04-10`

**Тест, фиксирующий дефект:**
`test_create_item.py::TestCreateItemPositive::test_create_item_response_format`

---

## BUG-04: GET /api/1/item/:id возвращает массив вместо одного объекта

**Priority:** P2 - Medium

**Краткое описание:**
`GET /api/1/item/:id` должен возвращать один item по `id`, но фактически возвращает массив из одного элемента.

**Шаги воспроизведения:**
1. Создать item и получить его `id`.
2. Отправить `GET /api/1/item/{id}`.
3. Проверить тип response.

**Фактический результат:**
```json
[{ "id": "...", "name": "...", "price": 1000 }]
```

**Ожидаемый результат:**
```json
{ "id": "...", "name": "...", "price": 1000 }
```

**Severity:** Medium

**Окружение:**
- Host: `https://qa-internship.avito.com`
- Endpoint: `GET /api/1/item/:id`
- Client: `pytest` + `requests`
- Дата прогона: `2026-04-10`

**Тест, фиксирующий дефект:**
`test_get_item.py::TestGetItemPositive::test_get_item_response_is_object`

---

## BUG-05: GET /api/1/statistic/:id возвращает массив вместо одного объекта

**Priority:** P2 - Medium

**Краткое описание:**
`GET /api/1/statistic/:id` возвращает `[{...}]` вместо `{...}`.

**Шаги воспроизведения:**
1. Создать item и получить его `id`.
2. Отправить `GET /api/1/statistic/{id}`.
3. Проверить тип response.

**Фактический результат:**
```json
[{ "likes": 5, "viewCount": 10, "contacts": 2 }]
```

**Ожидаемый результат:**
```json
{ "likes": 5, "viewCount": 10, "contacts": 2 }
```

**Severity:** Medium

**Окружение:**
- Host: `https://qa-internship.avito.com`
- Endpoint: `GET /api/1/statistic/:id`
- Client: `pytest` + `requests`
- Дата прогона: `2026-04-10`

**Тест, фиксирующий дефект:**
`test_get_statistic.py::TestGetStatisticV1Positive::test_get_statistic_v1_response_is_object`

---

## BUG-06: GET /api/1/:sellerID/item возвращает 404 для продавца без объявлений

**Priority:** P2 - Medium

**Краткое описание:**
Для продавца без объявлений API возвращает `404 Not Found` вместо пустого списка.

**Шаги воспроизведения:**
1. Использовать новый уникальный `sellerID`.
2. Отправить `GET /api/1/{sellerID}/item`.

**Фактический результат:**
`404 Not Found`

**Ожидаемый результат:**
`200 OK` с `[]`

**Severity:** Medium

**Окружение:**
- Host: `https://qa-internship.avito.com`
- Endpoint: `GET /api/1/:sellerID/item`
- Client: `pytest` + `requests`
- Дата прогона: `2026-04-10`

**Тест, фиксирующий дефект:**
`test_get_seller_items.py::TestGetSellerItemsPositive::test_get_seller_items_empty_for_new_seller`

---

## BUG-07: GET /api/2/statistic/:id может возвращать 100 Continue

**Priority:** P1 - High

**Краткое описание:**
`/api/2/statistic/:id` может возвращать HTTP `100 Continue` вместо финального `200 OK`.

**Шаги воспроизведения:**
1. Создать item и получить его `id`.
2. Отправить `GET /api/2/statistic/{id}`.
3. Проверить `status code`.

**Фактический результат:**
`100 Continue`

**Ожидаемый результат:**
`200 OK`

**Severity:** High

**Окружение:**
- Host: `https://qa-internship.avito.com`
- Endpoint: `GET /api/2/statistic/:id`
- Client: `pytest` + `requests`
- Дата прогона: `2026-04-10`

**Тест, фиксирующий дефект:**
`test_get_statistic.py::TestGetStatisticV2Positive::test_get_statistic_v2_returns_200`

---

## BUG-08: POST /api/1/item отклоняет валидный payload с нулевой statistics

**Priority:** P2 - Medium

**Краткое описание:**
Валидный create request с `statistics.contacts = 0`, `statistics.likes = 0` и `statistics.viewCount = 0` отклоняется с `400 Bad Request`.
Нулевые значения для счётчиков валидны и должны приниматься.

**Шаги воспроизведения:**
1. Отправить `POST /api/1/item` с body:
```json
{
  "sellerID": 320968,
  "name": "Котёнок",
  "price": 1000,
  "statistics": {
    "contacts": 0,
    "likes": 0,
    "viewCount": 0
  }
}
```
2. Проверить `status code`.

**Фактический результат:**
`400 Bad Request`

**Ожидаемый результат:**
`200 OK` - item должен успешно создаться.

**Влияние:**
API отклоняет распространённый валидный edge case и ломает сценарии, где начальная statistics должна быть пустой.

**Severity:** Medium

**Окружение:**
- Host: `https://qa-internship.avito.com`
- Endpoint: `POST /api/1/item`
- Client: `pytest` + `requests`
- Дата прогона: `2026-04-10`

**Тесты, фиксирующие дефект:**
`test_create_item.py::TestCreateItemPositive::test_create_item_response_format`
`test_create_item.py::TestCreateItemPositive::test_create_item_zero_statistics`
