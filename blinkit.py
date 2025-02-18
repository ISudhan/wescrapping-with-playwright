import json
import asyncio
import re
from playwright.async_api import async_playwright
import aiofiles

SEMAPHORE_LIMIT = 5  # Controls the number of concurrent scrapes
RETRY_LIMIT = 2  # Number of retries for failed scrapes

async def scrape_blinkit(start_url, semaphore):
    """Scrapes product data from Blinkit using a persistent browser context with concurrency control."""
    async with semaphore:  # Limit concurrency to avoid overloading system
        for attempt in range(RETRY_LIMIT):
            try:
                async with async_playwright() as p:
                    browser = await p.chromium.launch(headless=True)
                    context = await browser.new_context(
                        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                    )
                    page = await context.new_page()

                    print(f"[{attempt+1}/{RETRY_LIMIT}] Navigating to: {start_url}")
                    await page.goto(start_url, timeout=20000)

                    # Scroll down to load more products
                    for _ in range(3):  
                        await page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
                        await asyncio.sleep(2)

                    await page.wait_for_selector("div.Product__UpdatedPlpProductContainer-sc-11dk8zk-0", timeout=10000)

                    products = await page.query_selector_all("div.Product__UpdatedPlpProductContainer-sc-11dk8zk-0")
                    print(f"Found {len(products)} products on {start_url}")

                    scraped_data = []
                    for product in products:
                        scraped_data.append({
                            "name": await (await product.query_selector("div.Product__UpdatedTitle-sc-11dk8zk-9")).inner_text() if await product.query_selector("div.Product__UpdatedTitle-sc-11dk8zk-9") else None,
                            "image": await (await product.query_selector(".Imagestyles__ImageContainer-sc-1u3ccmn-0 img")).get_attribute("src") if await product.query_selector(".Imagestyles__ImageContainer-sc-1u3ccmn-0 img") else None,
                            "quantity": await (await product.query_selector("span")).inner_text() if await product.query_selector("span") else None,
                            
                            # Remove ₹ symbol using replace()
                            "mrp": (await (await product.query_selector(".Product__UpdatedPriceAndAtcContainer-sc-11dk8zk-10 div div:nth-of-type(2)")).inner_text()).replace("\u20b9", "").strip() if await product.query_selector(".Product__UpdatedPriceAndAtcContainer-sc-11dk8zk-10 div div:nth-of-type(2)") else None,
                            
                            "price": (await (await product.query_selector(".Product__UpdatedPriceAndAtcContainer-sc-11dk8zk-10 div div:nth-of-type(1)")).inner_text()).replace("\u20b9", "").strip() if await product.query_selector(".Product__UpdatedPriceAndAtcContainer-sc-11dk8zk-10 div div:nth-of-type(1)") else None,

                            # Alternative: Remove any non-numeric characters (use this instead if needed)
                            # "mrp": re.sub(r"[^\d.]", "", await (await product.query_selector(".Product__UpdatedPriceAndAtcContainer-sc-11dk8zk-10 div div:nth-of-type(2)")).inner_text()) if await product.query_selector(".Product__UpdatedPriceAndAtcContainer-sc-11dk8zk-10 div div:nth-of-type(2)") else None,
                            
                            # "price": re.sub(r"[^\d.]", "", await (await product.query_selector(".Product__UpdatedPriceAndAtcContainer-sc-11dk8zk-10 div div:nth-of-type(1)")).inner_text()) if await product.query_selector(".Product__UpdatedPriceAndAtcContainer-sc-11dk8zk-10 div div:nth-of-type(1)") else None,

                            "discount": await (await product.query_selector("div.Product__UpdatedOfferTitle-sc-11dk8zk-2")).inner_text() if await product.query_selector("div.Product__UpdatedOfferTitle-sc-11dk8zk-2") else None,
                            })

                    await browser.close()
                    return scraped_data

            except Exception as e:
                print(f"Error on attempt {attempt+1} for {start_url}: {e}")
                if attempt == RETRY_LIMIT - 1:
                    print(f"Failed to scrape {start_url} after {RETRY_LIMIT} attempts.")

    return []

async def main():
    """Main function to handle concurrent scraping efficiently and store output in a single list."""
    with open("input_blinkit.json", "r") as f:
        start_urls = json.load(f)

    start_urls = [url for url in start_urls if url.startswith("https://www.blinkit.com")]

    semaphore = asyncio.Semaphore(SEMAPHORE_LIMIT)  # Control concurrency

    tasks = [scrape_blinkit(url, semaphore) for url in start_urls]
    results = await asyncio.gather(*tasks)

    # Flatten results into a single list
    all_data = [item for sublist in results for item in sublist]

    # Save in a properly formatted single JSON list
    async with aiofiles.open("output_blinkit.json", "w") as f:
        await f.write(json.dumps(all_data, indent=4))

    print("Scraping completed. Data saved to output_blinkit.json")

if __name__ == "__main__":
    asyncio.run(main())
