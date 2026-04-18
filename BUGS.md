# BUGS.md - Дефекты, найденные в API

**Service:** `https://qa-internship.avito.com`

**Актуальный статус полного прогона на 18 апреля 2026:** `62 passed, 6 failed`

Этим падениям соответствуют следующие bugs:
- `BUG-01` принимается отрицательная `statistics`
- `BUG-02` принимается отрицательный `price`
- `BUG-03` format response у `POST /api/1/item` не соответствует документации
- `BUG-04` валидный create request с нулевой `statistics` отклоняется с `400`
- `BUG-05` API принимает недокументированные имена полей и вариации регистра в create payload
- `BUG-06` API принимает отрицательный `sellerID`

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

## BUG-04: POST /api/1/item отклоняет валидный payload с нулевой statistics

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

**Тест, фиксирующий дефект:**  
`test_create_item.py::TestCreateItemPositive::test_create_item_zero_statistics`

---

## BUG-05: POST /api/1/item принимает недокументированные имена полей и вариации регистра

**Priority:** P2 - Medium

**Краткое описание:**  
Сервис принимает payload с полем `sellerId` вместо документированного `sellerID` и успешно создаёт объявление.  
В исследовательских прогонах также подтвердилось, что API принимает и другие недокументированные имена и вариации регистра: `sellerid`, `SellerID`, `NAME`, `Price`, `STATISTICS`, `LIKES`.

**Шаги воспроизведения:**
1. Отправить `POST /api/1/item` с body:
```json
{
  "sellerId": 418955,
  "name": "Wrong key",
  "price": 1234,
  "statistics": {
    "contacts": 1,
    "likes": 1,
    "viewCount": 1
  }
}
```
2. Проверить `status code` и созданное объявление.

**Фактический результат:**  
`200 OK` - объявление успешно создаётся, хотя по контракту должны приниматься только документированные имена полей в точном написании.

**Ожидаемый результат:**  
`400 Bad Request` - API должно принимать только документированные имена полей из контракта: `sellerID`, `name`, `price`, `statistics`, `likes`, `viewCount`, `contacts`.

**Влияние:**  
Контракт валидации становится размытым: клиент может случайно отправлять неверные имена полей и не замечать ошибок интеграции.

**Severity:** Medium

**Окружение:**
- Host: `https://qa-internship.avito.com`
- Endpoint: `POST /api/1/item`
- Client: `pytest` + `requests`
- Дата прогона: `2026-04-17`

**Тест, фиксирующий дефект:**  
`test_create_item.py::TestCreateItemNegative::test_create_item_undocumented_field_name`

---

## BUG-06: POST /api/1/item принимает отрицательный sellerID

**Priority:** P2 - Medium

**Краткое описание:**  
Сервис принимает отрицательный `sellerID` и успешно создаёт объявление.  
С точки зрения здравого смысла и бизнес-логики идентификатор продавца не должен быть отрицательным.

**Шаги воспроизведения:**
1. Отправить `POST /api/1/item` с body:
```json
{
  "sellerID": -123456,
  "name": "Negative seller",
  "price": 1000,
  "statistics": {
    "contacts": 1,
    "likes": 1,
    "viewCount": 1
  }
}
```
2. Проверить `status code` и ответ сервиса.

**Фактический результат:**  
`200 OK` - объявление успешно создаётся с отрицательным `sellerID`.

**Ожидаемый результат:**  
`400 Bad Request` - API должно отклонять отрицательные идентификаторы продавца как невалидные данные.

**Влияние:**  
В систему могут попадать объявления с некорректными идентификаторами продавца, что размывает валидацию данных и повышает риск ошибок интеграции.

**Severity:** Medium

**Окружение:**
- Host: `https://qa-internship.avito.com`
- Endpoint: `POST /api/1/item`
- Client: `pytest` + `requests`
- Дата прогона: `2026-04-18`

**Тест, фиксирующий дефект:**  
`test_create_item.py::TestCreateItemNegative::test_create_item_negative_seller_id`
