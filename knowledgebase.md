# Knowledge Base — Noise E-Commerce Platform

This document serves as the architectural reference and engineering manual for the **Noise E-Commerce Platform** (Storefront Microservice Consumer).

---

## 1. System Architecture & Topology

The overall system is designed as a distributed two-tier microservice architecture:
1. **Weighted Ranking Engine (B2B Backend Microservice)**:
   - Port: `5000`
   - Purpose: Multi-tenant catalog ranking, attribute dimension management, mathematical weight enforcement, deterministic Min-Max scoring, and anti-bias sponsored slot interleaving.
2. **Noise Smart Tech Storefront (Customer-Facing Consumer Application)**:
   - Port: `8000`
   - Purpose: Consumer electronics e-commerce shopping experience, personalized search sliders, interactive tuning UI, session-persisted cart, and checkout processing.

```
+-----------------------------------------------------------------------+
|                 NOISE SMART TECH STOREFRONT (PORT 8000)                |
|                                                                       |
|   +-------------------+    +--------------------+    +------------+   |
|   |   Engine 3: UI    |    |  Engine 1: Models  |    | Engine 4:  |   |
|   |  Templates & CSS  |    |  Product, CartItem |    | Validation |   |
|   | (Space Grotesk,   |    |   Order, OrderItem |    |  (GST 18%, |   |
|   |  Cyan #00F2FE)    |    |     (SQLite)       |    |  Shipping) |   |
|   +---------+---------+    +---------+----------+    +-----+------+   |
|             |                        |                     |          |
|             +------------+-----------+---------------------+          |
|                          |                                            |
|                +---------v----------+                                 |
|                |  Engine 2: Client  |                                 |
|                |  & Fallback Engine |                                 |
|                +---------+----------+                                 |
+--------------------------|--------------------------------------------+
                           | HTTP REST (JSON)
                           | GET /api/v1/search?category=...&weights=...
                           v
+-----------------------------------------------------------------------+
|             WEIGHTED RANKING ENGINE MICROSERVICE (PORT 5000)          |
|                                                                       |
|   * Tenant Isolation (Company #1: Noise)                              |
|   * Min-Max Continuous & Discrete Binary Normalization                |
|   * Strict 100% Weight Allocation Enforcement                         |
|   * 1:5 Anti-Bias Sponsored Placement Interleaving (Slots 1, 6, 11)   |
|   * 3-Tier Tie-Breaking (Composite Score DESC -> Date DESC -> ID ASC) |
+-----------------------------------------------------------------------+
```

---

## 2. The 4 Engineering Subsystems (Engines)

The storefront platform is structured into four cohesive engineering engines:

### Engine 1: Data & Integrity (Catalog & Persistence)
- **Role**: Manages relational entities, schemas, referential integrity, cascading actions, and data serializations.
- **Components**:
  - `Product`: Catalog items with pricing, category slug, review metrics, battery life (hours), ANC flags, specs JSON, and stock flags. Includes calculated properties such as `discount_pct` and `specs` parsing.
  - `CartItem`: Session-bound shopping cart entries (`session_id`), linked to `Product` via foreign key with dynamic backref. Includes real-time `subtotal` computation.
  - `Order`: Customer transaction header (`order_number`, customer metadata, delivery address, `total_amount`, and lifecycle status).
  - `OrderItem`: Line items associated with a parent `Order` with `cascade="all, delete-orphan"`, recording historical unit price and quantity snapshot.
- **Integrity Constraints**:
  - Unique index on `Product.slug` and `Order.order_number`.
  - Non-nullable session identification for carts to ensure guest isolation.
  - Automatic UTC timestamp tracking (`created_at`).

### Engine 2: Core Logic / Algorithm (Recommendation Client & Fallback)
- **Role**: Handles communication with the upstream ranking engine and ensures deterministic fallback computation.
- **Components**:
  - `RankingEngineClient`: HTTP client communicating with `http://localhost:5000/api/v1/search`.
  - **Dynamic Personalization**: Passes user weight preferences (`battery_life`, `price`, `rating`, `anc`) as query parameters or JSON payload.
  - **Offline Fallback Architecture**: If the microservice on port 5000 is unreachable, times out (>1.5s), or returns an HTTP 5xx error, the client activates local normalization ranking using the local SQLite database.
  - **Score Attribution Reconciliation**: Maps upstream attribution breakdowns (Min-Max scores and metric weights) to the storefront UI for maximum transparency.

### Engine 3: Interface & Access (Web Tech: Templates, CSS, UI)
- **Role**: User-facing presentation layer, responsive design system, and dynamic interaction.
- **Components**:
  - `app/templates/base.html`: Master layout featuring the tech-lifestyle dark theme, electric cyan accents (`#00F2FE`), responsive navbar, live engine status indicator pill (`RANKING ENGINE :5000`), cart counter badge, flash message alerts, and academic project footer.
  - `app/templates/index.html`: Storefront homepage featuring the hero section, domain category pills, featured product showcase cards, and architectural integration telemetry display.
  - `app/static/css/style.css`: Unified design system with custom properties, Space Grotesk display typography, Plus Jakarta Sans body, JetBrains Mono code/metrics, glassmorphism cards, and mobile-friendly responsive breakpoints.
  - **Shopping Cart & Tuner UI**: Real-time attribute slider controls for re-ranking products client-side or through AJAX search endpoints.

### Engine 4: Validation, Security & Reporting (Business Logic & Audit)
- **Role**: Order calculation validation, regulatory compliance, transaction sanitization, and automated test coverage.
- **Components**:
  - **Order Pricing Calculations**:
    - Free shipping threshold: Orders $\ge$ ₹999 qualify for free shipping; otherwise a flat ₹99 fee applies.
    - Statutory GST calculation: Fixed 18.0% Goods & Services Tax validation on product subtotals.
  - **Input Sanitization**: Session identifier validation, parameter sanitization for category and weight values.
  - **Testing & Verification**: Pytest suite covering model invariants, cart operations, template rendering, and client failover behaviors.

---

## 3. Microservice Consumer Protocols

The storefront interacts with the Weighted Ranking Engine via RESTful JSON endpoints:

| Endpoint | Method | Purpose | Consumer Handling |
| :--- | :--- | :--- | :--- |
| `/api/v1/search` | `GET` / `POST` | Fetches ranked products according to dynamic weights | Enforces 1.5s timeout; falls back to local SQLite on failure. |
| `/api/v1/categories` | `GET` | Retrieves active category definitions & default weights | Populates storefront filter sliders and spec bounds. |
| `/api/v1/product/<id>` | `GET` | Fetches single product ranking attribution telemetry | Displays score breakdown modal on product detail page. |

### Anti-Bias Sponsored Placement Compliance
- In accordance with platform governance, sponsored products from the microservice are interleaved at a strict **1:5 ratio** (slots 1, 6, 11).
- Sponsored cards in the storefront display clear visual disclosures (`SPONSORED PLACEMENT` gold badge) without altering organic score integrity.

---

## 4. Engineering Log & Evolution

### Phase 1: Foundation & Infrastructure
- Initialized storefront Flask application with application factory pattern (`app/__init__.py`).
- Established environment configuration classes (`DevelopmentConfig`, `TestingConfig`, `ProductionConfig`).
- Implemented foundational SQLite models in `app/models.py` (`Product`, `CartItem`, `Order`, `OrderItem`).
- Authored master dark-theme template `base.html` featuring `#00F2FE` electric cyan highlights, microservice health pill, and responsive navigation.
- Built interactive `index.html` with hero showcase, category pills, product cards, and ranking engine architecture explanation.
- Constructed comprehensive CSS design system (`app/static/css/style.css`) with typography tokens, glassmorphism cards, and responsive grids.
- Documented component function inventory (`function_map.md`) and deployment guide (`docs/setup_guide.md`).
