# Function Map — Noise E-Commerce Platform

> Comprehensive mapping of every route handler, database model method, API client method, and frontend controller function across the project.  
> Developers and AI agents reference this map to locate implementations, understand dependencies, and verify requirements.

---

## 1. Application Factory & Global Context (`app/__init__.py`)

| Function | File | Line Est. | Feature Area | Description |
|---|---|---|---|---|
| `create_app(config_name)` | `app/__init__.py` | 10 | Core Bootstrap | Application factory that configures extensions, registers `storefront` and `admin` blueprints, and initializes the SQLite database. |
| `inject_globals()` | `app/__init__.py` | 35 | Context Processor | Injects `engine_status`, `cart_count`, and global store currency symbols across all Jinja2 templates automatically. |

---

## 2. Database Models & Business Logic (`app/models.py`)

| Method / Property | Model | Line Est. | Feature Area | Description |
|---|---|---|---|---|
| `discount_pct` | `Product` | 26 | Pricing | Computes integer percentage discount comparing `original_price` against selling `price`. |
| `specs` (getter/setter) | `Product` | 32 | Catalog Metadata | Serializes and deserializes the JSON string stored in `specs_json` into a native Python dictionary. |
| `to_dict()` | `Product` | 48 | Serialization | Serializes product attributes, specs, ratings, and image URLs to JSON-compatible dictionary. |
| `__repr__()` | `Product` | 68 | Debugging | Formats clean string representation of a Product instance with ID and name. |
| `subtotal` | `CartItem` | 83 | Cart Operations | Calculates `product.price * quantity` rounded to 2 decimal places. |
| `to_dict()` | `CartItem` | 89 | Serialization | Serializes a cart item and nested product entity for AJAX cart drawers. |
| `to_dict()` | `Order` | 120 | Orders & Checkout | Formats order summary including items, tax, shipping, and total for receipt generation. |
| `subtotal` | `OrderItem` | 145 | Order Accounting | Calculates line-item total based on historical purchase price and quantity. |
| `to_dict()` | `OrderItem` | 150 | Serialization | Serializes order line-items for display in receipts and order history. |

---

## 3. Weighted Ranking Engine Client (`app/engine_client.py`)

| Method | File | Line Est. | Feature Area | Description |
|---|---|---|---|---|
| `__init__()` | `app/engine_client.py` | 12 | Client Init | Initializes HTTP client with configurable base URL, tenant company ID, and request timeout. |
| `base_url` (property) | `app/engine_client.py` | 18 | Dynamic Config | Resolves ranking engine base URL from Flask `current_app.config['RANKING_ENGINE_URL']` or fallback default `http://localhost:5000`. |
| `company_id` (property) | `app/engine_client.py` | 26 | Tenant Resolution | Resolves tenant ID from Flask config `RANKING_COMPANY_ID` (default: `1`). |
| `health_check()` | `app/engine_client.py` | 33 | Health Monitoring | Pings `GET /api/v1/categories`, measures network latency in milliseconds, and returns status (`online` / `offline`). |
| `get_categories()` | `app/engine_client.py` | 69 | Schema Discovery | Retrieves all configured categories, attributes, and bounds for Tenant #1. Falls back to cached offline schema if engine is down. |
| `get_product_breakdown()` | `app/engine_client.py` | 115 | Attribution | Calls `GET /api/v1/product/<id>` on engine to retrieve exact composite score breakdown. Falls back to local mathematical breakdown if offline. |
| `search()` | `app/engine_client.py` | 134 | Search & Ranking | Central integration method. Executes `GET/POST /api/v1/search` with free-text queries and custom weight payloads. Handles sponsor interleaving and offline fallback. |
| `_enrich_with_local_products()` | `app/engine_client.py` | 195 | Catalog Merge | Merges rich local database fields (product images, markdown descriptions, local slugs) into raw engine search result records. |
| `_fallback_local_search()` | `app/engine_client.py` | 218 | Zero-Downtime Fallback | Executes in-process Min-Max normalization and weighted ranking over local SQLite database products when the remote engine is unreachable. |
| `_fallback_product_breakdown()` | `app/engine_client.py` | 310 | Offline Attribution | Generates synthetic yet deterministic mathematical score breakdown matching engine formulas for local product pages during offline mode. |

---

## 4. Storefront Controller & Customer Routes (`app/storefront/routes.py`)

| Route Handler | URL Pattern | Methods | Line Est. | Description |
|---|---|---|---|---|
| `get_session_id()` | Internal Helper | — | 10 | Generates or retrieves unique anonymous customer UUID stored in `session['session_id']`. |
| `index()` | `/` | `GET` | 17 | Homepage presenting brand hero banners, featured categories, and top-ranked electronics fetched from engine. |
| `shop()` | `/shop` | `GET`, `POST` | 41 | Main shopping catalog with keyword search `q`, category filtering, sorting, and dynamic weight application. |
| `product_detail()` | `/product/<int:product_id>` | `GET` | 123 | Detailed product view showing images, specs, customer reviews, and the "Ranking Score Breakdown" widget. |
| `smart_rank()` | `/api/smart-rank` | `GET`, `POST` | 167 | Asynchronous JSON endpoint invoked by client-side sliders to re-rank products dynamically with custom weight distribution. |
| `product_breakdown_api()` | `/api/product-breakdown/<int:product_id>` | `GET` | 210 | Returns JSON representation of the mathematical score breakdown for interactive modal dialogs. |
| `cart()` | `/cart` | `GET` | 230 | Displays current shopping bag, price subtotals, GST tax, and free shipping progress meter. |
| `cart_add()` | `/cart/add/<int:product_id>` | `POST` | 260 | Adds a product to the user's session cart; increments quantity if already present. |
| `cart_update()` | `/cart/update/<int:item_id>` | `POST` | 290 | Updates line-item quantity; deletes item if quantity is set to 0. |
| `cart_remove()` | `/cart/remove/<int:item_id>` | `POST` | 315 | Removes an item from the shopping bag immediately. |
| `checkout()` | `/checkout` | `POST` | 335 | Converts cart items into an active `Order`, generates unique order number, clears cart, and redirects to confirmation. |
| `order_success()` | `/order/<order_number>` | `GET` | 365 | Renders order success confirmation page with tracking timeline and itemized receipt. |

---

## 5. Store Operations & Admin Console (`app/admin/routes.py`)

| Route Handler | URL Pattern | Methods | Line Est. | Description |
|---|---|---|---|---|
| `dashboard()` | `/admin/` | `GET` | 10 | Administrative overview displaying total store revenue, order counts, product inventory count, and live engine status. |
| `products()` | `/admin/products` | `GET` | 47 | Inventory directory with category filters, stock search, and price listings. |
| `new_product()` | `/admin/products/new` | `GET`, `POST` | 78 | Form to create a new product, define specs, and assign technical attributes (`battery_life`, `price`, `rating`, `anc`). |
| `edit_product()` | `/admin/products/<int:product_id>/edit` | `GET`, `POST` | 122 | Form to edit existing product pricing, specifications, stock flags, or featured status. |
| `delete_product()` | `/admin/products/<int:product_id>/delete` | `POST` | 147 | Removes a product record from the local database. |
| `ranking_engine()` | `/admin/ranking-engine` | `GET` | 157 | Embedded Search Engine Admin Hub: integrates sandboxed iframe console (:5000) and native REST query simulator. |
| `api_engine_status()` | `/admin/api/engine-status` | `GET` | 178 | Polling endpoint returning engine latency in ms, connectivity status, and active attribute weights in JSON format. |

---

## 6. Frontend Client-Side Controllers (`app/static/js/`)

| Function | File | Line Est. | Feature Area | Description |
|---|---|---|---|---|
| `initRecommendationTuner()` | `storefront.js` | 12 | Smart Tuner | Initializes open/close event handlers, backdrop listeners, and weight slider state. |
| `updateWeights()` | `storefront.js` | 44 | Live Calculation | Recalculates sum of active weight sliders, updates percentage badges, and toggles `valid`/`invalid` indicator class. |
| `applyCustomWeights()` | `storefront.js` | 75 | AJAX Re-Rank | Submits custom weights to `/api/smart-rank`, updates product cards dynamically, and triggers smooth entrance animations. |
| `initCartFeedback()` | `storefront.js` | 105 | Cart UX | Adds animated micro-interaction feedback when users click "Add to Bag". |
| `initIframeToolbar()` | `admin_ranking.js` | 13 | Admin Embed | Manages tab buttons above the embedded engine iframe, switching URLs between Operations Hub, Category, and Insights. |
| `initEngineHealthCheck()`| `admin_ranking.js` | 31 | Latency Monitor | Polls `/admin/api/engine-status` in the background and updates latency text and pulse dot in the admin navbar. |
| `initRankingSimulator()` | `admin_ranking.js` | 58 | REST Simulator | Dispatches test queries to the engine REST API directly from the admin UI and renders syntax-highlighted JSON responses. |
