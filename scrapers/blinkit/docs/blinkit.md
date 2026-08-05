# Blinkit Reverse Engineering Documentation

# Objective

Extract product data from Blinkit and normalize it so that it can later be compared with Zepto and Instamart.

---

# Search API

## Endpoint

```text
https://blinkit.com/v1/layout/search?q=<QUERY>&search_type=type_to_search
```

Example:

```text
https://blinkit.com/v1/layout/search?q=milk&search_type=type_to_search
```

Method:

```text
POST
```

Payload:

```json
{
    "previous_search_query": "milk"
}
```

Required headers:

```http
lat: 11.347158799999999
lon: 77.71941679999999
content-type: application/json
```

---

# Search Flow

```text
Query

↓

Blinkit Search API

↓

JSON Response

↓

Extract Products

↓

Normalize

↓

Store
```

---

# Pagination

Response contains:

```json
{
    "pagination": {
        "next_url": "/v1/layout/search?offset=12&limit=12..."
    }
}
```

Logic:

1. Extract products from current page.
2. Save only matching products.
3. Open next page.
4. Stop when matching products become zero.

---

# Metadata

Response metadata:

```json
{
    "search_actual_keyword": "milk",
    "search_result_count": "12"
}
```

Fields:

| Field | Description |
|--------|--------|
| search_actual_keyword | Actual search keyword |
| search_result_count | Number of matching products |

---

# Product Schema

Raw Blinkit fields:

```json
{
    "product_id": "34778",
    "merchant_id": "38452",
    "name": {
        "text": "Amul Moti Toned Milk"
    },
    "brand_name": {
        "text": "Amul"
    },
    "variant": {
        "text": "450 ml"
    },
    "normal_price": {
        "text": "₹30"
    },
    "inventory": 2,
    "image": {
        "url": "..."
    }
}
```

Normalized schema:

```json
{
    "platform": "blinkit",

    "product_id": "34778",

    "name": "Amul Moti Toned Milk",

    "brand": "Amul",

    "quantity": "450 ml",

    "price": 30,

    "inventory": 2,

    "image_url": "...",

    "search_rank": 6
}
```

---

# Fields Required For Comparison

Required:

- platform
- product_id
- name
- brand
- quantity
- price
- inventory
- image_url

Optional:

- mrp
- discount
- rating
- delivery_time

---

# Search Ranking

Example:

```text
Query: milk

1. Arokya Full Cream Milk

2. Heritage Milk

3. Amul Gold Milk
```

Store:

```json
{
    "query": "milk",
    "rank": 1,
    "product_id": "12345"
}
```

---

# Common Interface

Every platform should implement:

```python
class BaseScraper:

    def search(self, query):
        pass
```

Blinkit:

```python
blinkit.search("milk")
```

Zepto:

```python
zepto.search("milk")
```

Instamart:

```python
instamart.search("milk")
```

---

# Unified Product Schema

All platforms must produce:

```json
{
    "platform": "",

    "product_id": "",

    "name": "",

    "brand": "",

    "quantity": "",

    "price": "",

    "inventory": "",

    "image_url": ""
}
```

---

# Final Comparison

Input:

```text
milk
```

Output:

```json
[
    {
        "platform": "blinkit",
        "name": "Arokya Full Cream Milk",
        "price": 35
    },

    {
        "platform": "zepto",
        "name": "Arokya Milk",
        "price": 34
    },

    {
        "platform": "instamart",
        "name": "Arokya Fresh Milk",
        "price": 36
    }
]
```
