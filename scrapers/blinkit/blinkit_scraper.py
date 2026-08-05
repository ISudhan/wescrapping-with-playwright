from playwright.sync_api import sync_playwright
import json


# ===================== CONFIG =====================

LAT = 11.347158799999999
LON = 77.71941679999999

QUERY = "milk"

PAYLOAD = {
    "previous_search_query": QUERY
}

BASE_URL = (
    f"https://blinkit.com/v1/layout/search"
    f"?q={QUERY}&search_type=type_to_search"
)


# ===================== HELPER =====================

def fetch_json(page, url, payload):

    return page.evaluate(
        """
        async ({ url, payload }) => {

            const response = await fetch(url, {
                method: "POST",
                headers: {
                    "content-type": "application/json"
                },
                body: JSON.stringify(payload)
            });

            const text = await response.text();

            try {
                return JSON.parse(text);
            } catch {
                return {
                    error: true,
                    body: text
                };
            }
        }
        """,
        {
            "url": url,
            "payload": payload
        }
    )


def matches_query(product_name, query):

    return query.lower() in product_name.lower()


# ===================== SCRAPER =====================

products = []

visited_urls = set()

with sync_playwright() as p:

    browser = p.chromium.launch(headless=False)

    context = browser.new_context(
        extra_http_headers={
            "lat": str(LAT),
            "lon": str(LON),
        }
    )

    page = context.new_page()

    url = BASE_URL

    page_number = 1

    while url:

        if url in visited_urls:
            print("Duplicate URL found. Stopping.")
            break

        visited_urls.add(url)

        print(f"\n===== PAGE {page_number} =====")

        result = fetch_json(page, url, PAYLOAD)

        if result.get("error"):
            print("Received HTML instead of JSON.")
            break

        snippets = result["response"]["snippets"]

        matched_count = 0

        for item in snippets:

            data = item.get("data", {})

            name = data.get("name", {}).get("text")

            if not name:
                continue

            if not matches_query(name, QUERY):
                continue

            product = {
                "product_id": data.get("product_id"),
                "merchant_id": data.get("merchant_id"),
                "name": name,
                "brand": data.get("brand_name", {}).get("text"),
                "quantity": data.get("variant", {}).get("text"),
                "price": data.get("normal_price", {}).get("text"),
                "inventory": data.get("inventory"),
                "image_url": data.get("image", {}).get("url"),
                "page": page_number
            }

            products.append(product)

            matched_count += 1

            print(f"{len(products)}. {name}")

        print(f"\nMatched products on page {page_number}: {matched_count}")

        # Stop if there are no matching products

        if matched_count == 0:
            print("\nNo matching products found. Stopping.")
            break

        next_url = result["response"]["pagination"].get("next_url")

        if next_url:
            url = "https://blinkit.com" + next_url
            page_number += 1
        else:
            break

    browser.close()


# ===================== SAVE =====================

output = {
    "query": QUERY,
    "total_products": len(products),
    "products": products
}

with open("response.json", "w", encoding="utf-8") as f:

    json.dump(
        output,
        f,
        indent=4,
        ensure_ascii=False
    )

print(f"\nSaved {len(products)} products to response.json")