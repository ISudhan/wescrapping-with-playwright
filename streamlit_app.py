"""Streamlit UI for Grocery Price Comparison.

Communicates with the FastAPI backend — does NOT access MongoDB directly.
"""

import streamlit as st
import requests

# FastAPI base URL
API_URL = "http://localhost:8000"

st.set_page_config(
    page_title="Grocery Price Comparison",
    page_icon="🛒",
    layout="wide",
)

st.title("🛒 Grocery Price Comparison")
st.caption("Compare prices across Blinkit, Swiggy Instamart & Zepto")


def api_request(method: str, endpoint: str):
    """Make a request to the FastAPI backend."""
    try:
        url = f"{API_URL}{endpoint}"
        if method == "GET":
            resp = requests.get(url, timeout=10)
        else:
            resp = requests.post(url, timeout=10)
        resp.raise_for_status()
        return resp.json(), None
    except requests.ConnectionError:
        return None, "Cannot connect to API. Is FastAPI running on localhost:8000?"
    except requests.HTTPError as e:
        return None, f"API error: {e.response.status_code} — {e.response.text}"
    except Exception as e:
        return None, f"Error: {e}"


# ─── Sidebar: Scrape Trigger ─────────────────────────────────────

with st.sidebar:
    st.header("⚙️ Controls")
    if st.button("🔄 Run Scrapers", use_container_width=True):
        data, error = api_request("POST", "/scrape")
        if error:
            st.error(error)
        else:
            st.success(data.get("message", "Scraping started!"))

    st.divider()
    st.markdown("**API Status**")
    health_data, health_error = api_request("GET", "/")
    if health_error:
        st.error(f"🔴 API Offline\n\n{health_error}")
    else:
        st.success(f"🟢 {health_data.get('status', 'unknown').capitalize()}")

# ─── Main: Product Search ────────────────────────────────────────

search_query = st.text_input(
    "🔍 Search for a product",
    placeholder="e.g., Tata Salt, Amul Milk, Fortune Oil...",
)

if search_query:
    col1, col2 = st.columns(2)

    # Products list
    with col1:
        st.subheader("📦 Products Found")
        data, error = api_request("GET", f"/products/{search_query}")
        if error:
            st.warning(error)
        elif data:
            count = data.get("count", 0)
            st.info(f"Found **{count}** product(s)")
            products = data.get("products", [])
            for p in products[:20]:  # Limit display
                with st.container(border=True):
                    pcol1, pcol2 = st.columns([1, 3])
                    with pcol1:
                        if p.get("image"):
                            st.image(p["image"], width=80)
                    with pcol2:
                        st.markdown(f"**{p.get('name', 'N/A')}**")
                        st.caption(
                            f"Platform: {p.get('platform', 'N/A').capitalize()} · "
                            f"Price: ₹{p.get('price', 'N/A')} · "
                            f"MRP: ₹{p.get('mrp', 'N/A')} · "
                            f"Qty: {p.get('quantity', 'N/A')}"
                        )
                        if p.get("discount"):
                            st.caption(f"🏷️ {p['discount']}")

    # Price comparison
    with col2:
        st.subheader("💰 Price Comparison")
        comp_data, comp_error = api_request("GET", f"/compare/{search_query}")
        if comp_error:
            st.warning(comp_error)
        elif comp_data:
            prices = comp_data.get("prices", {})
            lowest_platform = comp_data.get("lowest_platform")
            lowest_price = comp_data.get("lowest_price")

            if lowest_platform and lowest_price:
                st.success(
                    f"🏆 Lowest price: **₹{lowest_price}** on **{lowest_platform.capitalize()}**"
                )

            for platform, price in prices.items():
                icon = "🟢" if platform == lowest_platform else "⚪"
                price_str = f"₹{price}" if price is not None else "N/A"
                st.markdown(f"{icon} **{platform.capitalize()}**: {price_str}")
else:
    st.info("Enter a product name above to search and compare prices across platforms.")
