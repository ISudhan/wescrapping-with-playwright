# 🛒 Multi-Platform Grocery Price Comparison System

A web scraping and data normalization pipeline that aggregates live product listings from **Blinkit**, **Swiggy Instamart**, and **Zepto** into a unified schema, enabling real-time price comparison across platforms.

## Architecture

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Blinkit    │     │    Swiggy    │     │    Zepto     │
│  (Playwright)│     │ (Playwright) │     │ (Playwright) │
└──────┬───────┘     └──────┬───────┘     └──────┬───────┘
       │                    │                    │
       └────────────┬───────┘────────────────────┘
                    ▼
          ┌─────────────────┐
          │   Normalizer    │  ← Pydantic schema + name normalization
          └────────┬────────┘
                   ▼
          ┌─────────────────┐
          │  Matcher +      │  ← Exact + fuzzy (difflib) matching
          │  Comparator     │
          └────────┬────────┘
                   ▼
          ┌─────────────────┐
          │    MongoDB      │  ← products + price_comparisons
          └────────┬────────┘
                   ▼
          ┌─────────────────┐
          │    FastAPI      │  ← REST API with /docs
          └────────┬────────┘
                   ▼
          ┌─────────────────┐
          │   Streamlit     │  ← Search, compare, scrape UI
          └─────────────────┘
```

## Features

- **Multi-platform scraping** — Playwright-based scrapers for Blinkit, Swiggy Instamart, and Zepto with asyncio concurrency and retry handling
- **Data normalization** — Pydantic schema with name normalization (lowercase, punctuation removal, whitespace collapse)
- **Product matching** — Exact match by normalized name + optional fuzzy matching via `difflib.SequenceMatcher`
- **Price comparison** — Groups matched products, identifies lowest price per product across platforms
- **MongoDB storage** — Products and comparisons persisted with upsert logic
- **REST API** — FastAPI with auto-generated `/docs`, background scraping, search, and comparison endpoints
- **Web UI** — Streamlit dashboard for search, comparison, and scrape triggering
- **Scheduled scraping** — Configurable scheduler for automated daily scraping

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Scraping | Python, Playwright, asyncio |
| Schema | Pydantic |
| Database | MongoDB (PyMongo) |
| API | FastAPI, Uvicorn |
| UI | Streamlit |
| Scheduler | schedule |
| Testing | pytest, httpx |

## Project Structure

```
├── blinkit.py              # Blinkit scraper (Playwright)
├── swiggy.py               # Swiggy Instamart scraper (Playwright)
├── zepto.py                # Zepto scraper (Playwright)
├── scheduler.py            # Scheduled scraping (cron-like)
├── models/
│   └── product.py          # Pydantic models, normalization, price parsing
├── services/
│   ├── normalizer.py       # Raw JSON → Product schema conversion
│   ├── matcher.py          # Exact + fuzzy product matching
│   └── comparator.py       # Price comparison logic
├── db/
│   └── mongodb.py          # MongoDB connection + CRUD helpers
├── api/
│   └── main.py             # FastAPI application
├── streamlit_app.py        # Streamlit UI
├── tests/
│   ├── test_normalizer.py  # Normalization + price parsing tests
│   ├── test_matcher.py     # Matching logic tests
│   ├── test_comparator.py  # Price comparison tests
│   └── test_api.py         # API endpoint tests
├── input_*.json            # Scraper input URLs
├── requirements.txt
├── .env.example
└── .gitignore
```

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
playwright install chromium
```

### 2. Environment Variables

```bash
cp .env.example .env
# Edit .env with your MongoDB connection string
```

```env
MONGODB_URI=mongodb://localhost:27017
MONGODB_DATABASE=grocery_price_comparison
```

### 3. MongoDB

Make sure MongoDB is running locally (default: `localhost:27017`).

The application auto-creates the database and collections (`products`, `price_comparisons`) on first use.

## Running

### Scrapers (standalone)

```bash
python blinkit.py
python swiggy.py
python zepto.py
```

### Scheduler (automated daily scraping)

```bash
python scheduler.py
```

### FastAPI

```bash
uvicorn api.main:app --reload
```

API docs available at: [http://localhost:8000/docs](http://localhost:8000/docs)

### Streamlit

```bash
streamlit run streamlit_app.py
```

> **Note:** FastAPI must be running for Streamlit to work. Start FastAPI first.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Health check |
| `GET` | `/products` | List all products (optional `?platform=blinkit`) |
| `GET` | `/products/{name}` | Search products by name |
| `GET` | `/compare/{name}` | Price comparison across platforms |
| `POST` | `/scrape` | Trigger scraping pipeline (background) |

### Example: Price Comparison

```bash
curl http://localhost:8000/compare/tata%20salt
```

```json
{
  "product_name": "tata salt",
  "prices": {
    "blinkit": 24.0,
    "swiggy": 26.0,
    "zepto": 22.0
  },
  "lowest_price": 22.0,
  "lowest_platform": "zepto"
}
```

## Data Flow

1. **Scrape** → Playwright scrapers fetch product data from each platform
2. **Normalize** → Raw JSON converted to common Pydantic `Product` schema with normalized names
3. **Store** → Products saved to MongoDB `products` collection
4. **Match** → Products matched across platforms by normalized name (exact + optional fuzzy)
5. **Compare** → Prices grouped and lowest identified per product
6. **Serve** → FastAPI exposes data via REST API
7. **Display** → Streamlit UI consumes API for search and comparison

## Testing

```bash
python -m pytest tests/ -v
```

## Future Improvements

- Category-based browsing and filtering
- Price history tracking and trend charts
- Alerts/notifications for price drops
- Enhanced fuzzy matching with brand/quantity awareness
- Containerized deployment with Docker
- CI/CD pipeline
