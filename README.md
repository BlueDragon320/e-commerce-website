# Noise E-Commerce Platform — Smart Tech Storefront

> **Listen to the Noise Within.**  
> A lifestyle electronics e-commerce storefront powered by the **Weighted Ranking Engine (B2B Microservice)**. Delivers deterministic multi-criteria product ranking, dynamic customer personalization sliders, transparent score attribution, and an embedded engine management console.

---

## Key Highlights & Capabilities

- **Multi-Tenant Weighted Ranking Integration**: Consumes the B2B REST API of the Weighted Ranking Engine running on port `5000` under Tenant Company `#1` (Noise).
- **Personalized Recommendation Sliders**: Shoppers can adjust attribute weights (Battery Life, Price, Rating, ANC) in real time to re-rank products dynamically.
- **Sponsored Placement Interleaving**: Renders organic search results interleaved with active sponsored products adhering to strict anti-bias policies (1:5 sponsored-to-organic ratio).
- **Transparent Mathematical Attribution**: Breakdown showing Min-Max normalized values, category weights, and raw metric contributions.
- **Resilient Offline Fallback Architecture**: If the Weighted Ranking Engine microservice is unreachable, the storefront gracefully switches to local database ranking.
- **Complete Shopping Experience**: Shopping bag, session-persisted cart, checkout with GST calculation, and order tracking.

---

## 📁 Repository Structure

```text
e-commerce-website/
├── app/
│   ├── __init__.py            # Flask app factory, extension initialization
│   ├── models.py              # Retail models: Product, CartItem, Order, OrderItem
│   ├── engine_client.py       # HTTP client connecting to Ranking Engine (Port 5000)
│   ├── storefront/            # Storefront catalog, cart, and checkout blueprint
│   │   └── routes.py          # /shop, /cart, /checkout, /api/smart-rank
│   ├── admin/                 # Storefront inventory administration blueprint
│   │   └── routes.py          # Product inventory CRUD, engine configuration hub
│   ├── static/                # FrontEnd CSS, icons, and JavaScript widgets
│   │   ├── css/style.css      # Dark-cyan storefront styling & responsive grid
│   │   └── js/storefront.js   # Dynamic recommendation tuner modal & sliders
│   └── templates/             # Jinja2 template hierarchy
│       ├── base.html          # Retail shell layout, navbar, live status indicator
│       ├── storefront/        # Product detail, cart, checkout, shop views
│       └── admin/             # Inventory dashboard, product forms, engine hub
├── documents/                 # College & Engine Deliverables (Word, Excel, SQL)
│   ├── DATABASE_QUERIES_ENGINE1.sql # Engine 1: Pure RDBMS DDL, ALTER, DML & audit queries
│   ├── TEST_CASES_ENGINE4.xlsx      # Engine 4: Master Test Cases Excel matrix (45 scenarios)
│   ├── FOUR_ENGINES_PROJECT_MANUAL_AND_VIVA_GUIDE.docx # Word project manual & viva prep
│   └── MASTER_DEVELOPMENT_PHASE_GUIDE.docx             # 6-Week development manual (.docx)
├── markdown/                  # Developer logs & markdown manuals
│   ├── DEV_LOGS_SHRINIVAS.md  # Daily developer issue & fix resolution log
│   ├── FOUR_ENGINES_PROJECT_MANUAL_AND_VIVA_GUIDE.md   # 4-Engine manual in Markdown
│   └── MASTER_DEVELOPMENT_PHASE_GUIDE.md               # Master phase guide in Markdown
├── tests/                     # Automated test suites
│   ├── conftest.py            # Test fixtures & test client
│   ├── test_storefront.py     # Catalog, cart, and checkout tests
│   ├── test_engine_client.py  # REST API integration & offline fallback tests
│   └── test_admin.py          # Store admin catalog management tests
├── config.py                  # Storefront configuration (Port 8000, GST, Currency)
├── requirements.txt           # Python package dependencies
├── run.py                     # Entry point (Port 8000)
└── seed.py                    # 16+ Noise devices seed catalog
```

---

## Tech Stack

- **Backend Framework**: Python 3.10+, Flask 3.x
- **Database / ORM**: SQLite 3 with SQLAlchemy ORM
- **Microservice Client**: `RankingEngineClient` with connection pooling, timeout guards, and deterministic fallback
- **Frontend / Styling**: Vanilla JavaScript, custom CSS design system featuring tech-lifestyle dark theme with electric cyan (`#00F2FE`) and neon accents
- **Testing**: Pytest

---

## Quick Setup Instructions

1. **Clone the repository:**
   ```bash
   git clone https://github.com/BlueDragon320/e-commerce-website.git
   cd e-commerce-website
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run development server:**
   ```bash
   python run.py
   ```
   *The application starts at `http://127.0.0.1:8000/`.*
