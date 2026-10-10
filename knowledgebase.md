# Knowledgebase — Noise E-Commerce Platform

> Comprehensive chronological log, architecture reference, and technical decisions register for the Noise E-Commerce storefront project.  
> Engineers and agents reference this document to track component responsibilities, implementation evolution, and architectural rationale.

---

## 1. Project Component Registry & Architectural Log

| Timestamp | Phase | File | Lines | Developer | Architectural Responsibility |
|---|---|---|---|---|---|
| 2026-09-27 | P1 | `run.py` | 1-20 | Dev-A | Application entry point; runs local development server on port `8000`. |
| 2026-09-27 | P1 | `config.py` | 1-43 | Dev-A | Centralized configuration managing port 8000, SQLite database URIs, and ranking engine URL (`http://localhost:5000`) and tenant ID (`1`). |
| 2026-09-27 | P1 | `requirements.txt` | 1-6 | Dev-A | System package requirements: `Flask`, `Flask-SQLAlchemy`, `requests`, `pytest`, `python-slugify`. |
| 2026-09-27 | P1 | `app/__init__.py` | 1-50 | Dev-A | Flask application factory `create_app()`; initializes SQLAlchemy, registers `storefront` and `admin` blueprints, injects global context processors (engine status, cart count). |
| 2026-09-27 | P1 | `app/models.py` | 1-152 | Dev-A | SQLAlchemy data models: `Product` (specs, pricing, battery, ANC, discount), `CartItem` (session cart), `Order`, and `OrderItem`. |
| 2026-09-27 | P1 | `README.md` | 1-120 | Dev-A | Project overview, tech stack, architecture diagram, dual-server setup commands, and endpoint reference. |
| 2026-09-27 | P1 | `app/templates/base.html` | 1-215 | Dev-B | Master storefront layout with top live engine status bar, brand navigation, live search form, recommendation tuner modal, and footer. |
| 2026-09-27 | P1 | `app/static/css/style.css` | 1-1037 | Dev-B | Comprehensive storefront design system: tech-lifestyle dark theme (`#0A0D14`), electric cyan accents (`#00F2FE`), neon glows, glassmorphism, responsive product grids. |
| 2026-09-27 | P1 | `knowledgebase.md` | 1-80 | Dev-B | Chronological development and architecture log initialized. |
| 2026-09-27 | P1 | `function_map.md` | 1-60 | Dev-B | Function, route, and method registry initialized. |
| 2026-09-27 | P1 | `docs/setup_guide.md` | 1-90 | Dev-B | Step-by-step developer orchestration guide for running both services. |
| 2026-09-27 | P2 | `app/engine_client.py` | 1-489 | Dev-A | B2B REST client connecting to Weighted Ranking Engine (`:5000`); handles `health_check()`, `get_categories()`, `search()`, `get_product_breakdown()`, and local fallback algorithms. |
| 2026-09-27 | P2 | `app/templates/base.html` | — | Dev-B | Added real-time engine connectivity dot and dynamic offline alert banner in header. |
| 2026-09-27 | P3 | `app/storefront/__init__.py`| 1-6 | Dev-B | Storefront blueprint definition. |
| 2026-09-27 | P3 | `app/storefront/routes.py` | 1-381 | Dev-A | Public customer routes: homepage (`/`), catalog search (`/shop`), re-ranking API (`/api/smart-rank`), product page (`/product/<id>`), cart management (`/cart`), and checkout. |
| 2026-09-27 | P3 | `app/templates/storefront/index.html` | 1-140 | Dev-A | Homepage featuring hero electronics showcase, category shortcut cards, and "Top Ranked by Engine" product grid. |
| 2026-09-27 | P3 | `app/templates/storefront/shop.html` | 1-160 | Dev-A | Interactive catalog listing with search query bar, filter tags, rank medals (`#01`, `#02`, `#03`), sponsored badges, and score percentages. |
| 2026-09-27 | P3 | `app/static/js/storefront.js` | 1-126 | Dev-B | Client-side recommendation tuner script: slider event listeners, 100% weight validation, preset loaders (Max Battery, Budget Value, Audiophile), and dynamic AJAX re-ranking. |
| 2026-09-27 | P4 | `app/templates/storefront/product_detail.html` | 1-165 | Dev-A | Detailed product page with specifications, image gallery, customer ratings, and the "Ranking Score Breakdown" widget. |
| 2026-09-27 | P4 | `app/templates/storefront/cart.html` | 1-115 | Dev-B | Shopping cart view with item quantity adjustment, price calculation, GST breakdown, and shipping threshold tracker. |
| 2026-09-27 | P4 | `app/templates/storefront/order_success.html`| 1-75 | Dev-B | Checkout confirmation page with simulated order number, tracking timeline, and purchase summary. |
| 2026-09-27 | P5 | `app/admin/__init__.py` | 1-6 | Dev-A | Admin blueprint definition. |
| 2026-09-27 | P5 | `app/admin/routes.py` | 1-192 | Dev-A | Admin portal routes: store overview (`/admin/`), inventory CRUD (`/admin/products`), embedded engine console (`/admin/ranking-engine`), and engine status JSON API (`/admin/api/engine-status`). |
| 2026-09-27 | P5 | `app/templates/admin/base.html` | 1-85 | Dev-B | Admin sidebar layout with navigation, live engine connection pill, and store telemetry. |
| 2026-09-27 | P5 | `app/templates/admin/dashboard.html` | 1-120 | Dev-B | Admin dashboard featuring revenue stats, order count, inventory alerts, and engine latency health card. |
| 2026-09-27 | P5 | `app/templates/admin/products.html` | 1-90 | Dev-B | Inventory management table with price, stock toggles, and edit/delete actions. |
| 2026-09-27 | P5 | `app/templates/admin/ranking_engine.html` | 1-103 | Dev-B | Dedicated Ranking Engine Hub: embedded iframe browser console, quick navigation toolbar, and live REST API query simulator. |
| 2026-09-27 | P5 | `app/static/css/admin.css` | 1-280 | Dev-B | Dark-mode admin console styling with dashboard grids, status tags, and embedded iframe container. |
| 2026-09-27 | P5 | `app/static/js/admin_ranking.js` | 1-81 | Dev-B | Admin console JavaScript: iframe URL switcher, background engine latency polling, and interactive REST query simulator execution. |
| 2026-09-27 | P6 | `seed.py` | 1-428 | Dev-A | Database seeder populating 16+ Noise devices (ColorFit Ultra 3, Halo, Icon 2, Buds VS104, Buds X Prime, etc.), categories, and mock orders. |
| 2026-09-27 | P6 | `docs/api_reference.md` | 1-220 | Dev-B | Complete B2B Engine API reference specification for client developers. |
| 2026-09-27 | P6 | `docs/integration_guide.md` | 1-650 | Dev-B | Flagship enterprise integration guide covering architecture, onboarding, catalog sync, frontend tuner, score transparency, and admin embedding. |

---

## 2. Architectural & Technical Decisions Log

### Decision 1: Microservice Separation (Port 5000 vs Port 8000)
- **Context**: The project required demonstrating how an independent e-commerce platform integrates with a dedicated B2B ranking engine microservice.
- **Decision**: Keep the ranking engine on port `5000` and the Noise storefront on port `8000`. The storefront communicates exclusively via standard HTTP REST API requests (`requests` library) using `X-Company-ID: 1`.
- **Rationale**: Demonstrates true B2B SaaS separation of concerns. The storefront has no direct database access to the ranking engine's internal tables, honoring multi-tenant boundaries.

### Decision 2: Resilient In-Process Offline Fallback
- **Context**: If the ranking engine microservice is halted, undergoing maintenance, or experiencing network latency, the customer storefront must not crash or display empty pages.
- **Decision**: Implemented an automated fallback in `RankingEngineClient`. When an HTTP timeout or connection error occurs, the client catches `RequestException`, sets `engine_status = 'offline'`, and invokes `_fallback_local_search()`.
- **Implementation**: The fallback uses local product attributes (`battery_life`, `price`, `rating`, `anc`) and applies the standard Min-Max normalization formula in memory to compute deterministic composite scores.
- **Outcome**: 100% storefront availability regardless of microservice health.

### Decision 3: Embedded Search Engine Admin Console (Iframe + Native Simulator)
- **Context**: Store administrators need to configure category criteria weights, inspect active attributes, and manage sponsored placement slots without logging into a separate server portal.
- **Decision**: Built a hybrid admin hub (`/admin/ranking-engine`) featuring:
  1. An embedded, sandboxed iframe loaded directly from `http://localhost:5000/admin` with quick navigation tabs (`Operations Hub`, `Category Overview`, `Attributes & Weights`, `Sponsored Placements`, `Insights & Analytics`).
  2. A native REST API Query Simulator that fetches live JSON from `http://localhost:5000/api/v1/search` and renders formatted scoring breakdowns.
- **Outcome**: Store managers have single-pane-of-glass administrative control over search and ranking without duplicate code.

### Decision 4: Interactive Client-Side Dynamic Weight Sliders (Smart Tuner)
- **Context**: Modern shoppers expect personalized discovery. For example, a student may prioritize price and battery life, while an audiophile prioritizes Active Noise Cancelling (ANC) and sound quality.
- **Decision**: Designed the **Smart Recommendation Tuner** drawer with 4 attribute sliders summing to 100%. Preset buttons (`Max Battery`, `Budget Value`, `Audiophile & ANC`, `Balanced`) automatically distribute weights.
- **API Contract**: Sliders submit `custom_weights` to `/api/smart-rank`, which proxies the request to the engine's `POST /api/v1/search`. The engine re-ranks products on the fly using custom weights and returns real-time scored results.

### Decision 5: Transparent Mathematical Attribution ("Why Ranked #X?")
- **Context**: E-commerce customers often distrust search rankings, suspecting hidden sponsor bias.
- **Decision**: Built a dedicated mathematical attribution widget on both catalog cards and product detail pages (`/product/<id>`).
- **Display Details**: Breaks down every scoring component:
  $$\text{Raw Value} \longrightarrow \text{Normalized Value } (0.00 - 1.00) \times \text{Weight } (\%) = \text{Score Contribution}$$
- **Outcome**: Total algorithmic transparency builds consumer trust while distinguishing organic score merits from sponsored overrides.

### Decision 6: Session-Persisted Shopping Bag with Local Storage Sync
- **Context**: Support end-to-end e-commerce flow without mandatory user registration.
- **Decision**: Anonymous shopping sessions identified via UUID cookies in Flask sessions (`session['session_id']`). Cart items are linked in SQLite to the session UUID, enabling instant checkout with automated GST and shipping calculations.
