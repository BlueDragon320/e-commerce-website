# Noise E-Commerce Platform — Smart Tech Storefront

> **Listen to the Noise Within.**  
> A high-performance lifestyle electronics e-commerce storefront powered by the **Weighted Ranking Engine (B2B Microservice)**. Delivers deterministic multi-criteria product ranking, dynamic customer personalization sliders, transparent score attribution, and an embedded engine management console.

---

## 🌟 Key Highlights & Capabilities

- **Multi-Tenant Weighted Ranking Integration**: Consumes the B2B REST API of the Weighted Ranking Engine running on port `5000` under Tenant Company `#1` (TechMart / Noise).
- **Personalized Recommendation Sliders**: Shoppers can open the **Smart Tuner** drawer to adjust attribute weights (Battery Life, Price, Rating, ANC) in real time. Products re-rank dynamically via AJAX.
- **Sponsored Placement Interleaving**: Renders organic search results interleaved with active sponsored products adhering to strict anti-bias policies (1:5 sponsored-to-organic ratio).
- **Transparent Mathematical Attribution**: "Why is this ranked #X?" modal and breakdown widget showing Min-Max normalized values, category weights, and raw metric contributions.
- **Embedded Engine Admin Console**: Store administrators can manage category attributes, weights, and sponsored campaigns without leaving their store dashboard via an embedded, sandboxed console and native REST query simulator.
- **Resilient Offline Fallback Architecture**: If the Weighted Ranking Engine microservice is unreachable, the storefront gracefully switches to local database ranking, ensuring zero user-facing downtime.
- **Complete Shopping Experience**: Seamless shopping bag, session-persisted cart, checkout with GST calculation, and order tracking.

---

## 🏗️ Architecture & Tech Stack

```
┌─────────────────────────────────────────────────────────────┐
│                       End-User Browser                      │
└──────────────┬───────────────────────────────▲──────────────┘
               │                               │
               │ HTTP Requests (:8000)         │ HTML / JSON
               ▼                               │
┌─────────────────────────────────────────────────────────────┐
│             Noise E-Commerce Web App (Flask :8000)          │
│                                                             │
│   ├── Storefront Blueprint (/shop, /product/<id>, /cart)    │
│   ├── Admin Blueprint (/admin, /admin/ranking-engine)       │
│   ├── Local Catalog DB (SQLite: instance/noise_ecommerce.db)│
│   └── RankingEngineClient (app/engine_client.py)            │
└──────────────┬───────────────────────────────▲──────────────┘
               │                               │
               │ REST API (:5000/api/v1/...)   │ JSON Payload
               ▼                               │
┌─────────────────────────────────────────────────────────────┐
│          Weighted Ranking Engine (Flask Microservice :5000) │
│                                                             │
│   ├── Normalization Engine (Min-Max continuous & binary)    │
│   ├── Composite Scorer & Multi-Tenant Isolation (Tenant #1) │
│   ├── Sponsored Placement Interleaving (1:5 ratio)          │
│   └── Platform Operations Console & Search Analytics        │
└─────────────────────────────────────────────────────────────┘
```

- **Backend Framework**: Python 3.10+, Flask 3.x
- **Database / ORM**: SQLite 3 with SQLAlchemy ORM
- **Microservice Client**: `RankingEngineClient` with connection pooling, timeout guards, and deterministic fallback
- **Frontend / Styling**: Vanilla JavaScript (no heavy frontend frameworks), custom CSS design system featuring tech-lifestyle dark theme with electric cyan (`#00F2FE`) and neon accents
- **Typography**: Space Grotesk, Plus Jakarta Sans, JetBrains Mono

---

## ⚡ Dual-Server Setup & Quick Start

The platform operates as a distributed system: the **Weighted Ranking Engine** runs as a B2B backend service on port `5000`, while the **Noise E-Commerce Site** runs on port `8000`.

### Prerequisites
- Python 3.10 or higher
- `virtualenv` or `venv`

---

### Step 1: Start the Weighted Ranking Engine (Port 5000)

Open Terminal 1:

```bash
cd /home/blue/MiniProject/weighted-ranking-engine

# Activate virtual environment
source venv/bin/activate  # or python3 -m venv venv && source venv/bin/activate

# Install dependencies (if not already installed)
pip install -r requirements.txt

# Run seed script (creates companies, attributes, products, and sponsors)
python seed.py

# Start ranking engine server
python run.py
```
> The Weighted Ranking Engine is now running at `http://localhost:5000`.

---

### Step 2: Start the Noise E-Commerce Storefront (Port 8000)

Open Terminal 2:

```bash
cd /home/blue/MiniProject/ECommerce-Site

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Seed the local Noise product catalog and demo orders
python seed.py

# Start the Noise storefront server
python run.py
```
> The Noise E-Commerce Site is now live at `http://localhost:8000`.

---

## 🛒 Feature Walkthrough

### 1. Storefront Catalog & Dynamic Multi-Criteria Search
- Navigate to `http://localhost:8000/shop`.
- Free-text search matches across product titles and categories.
- Results are ranked by the Weighted Ranking Engine using multi-attribute scoring (`Battery Life`, `Price`, `Rating`, `ANC`).
- Product cards highlight rank badges (`#01`, `#02`, `#03`), composite score percentage (e.g. `88.5% SCORE`), and specification pills.

### 2. Interactive Recommendation Tuner Drawer
- Click the **⚡ Smart Tuner: Adjust Multi-Criteria Weights** button in the header.
- Use presets like **Max Battery**, **Budget Value**, or **Audiophile & ANC**, or manually drag sliders.
- A live validator ensures total weights equal 100%.
- Clicking **Apply & Re-Rank** dispatches an asynchronous request to the ranking engine and dynamically re-orders products without a full page reload.

### 3. Sponsored Placement Transparency
- Products with active sponsorship campaigns appear at position #1 or interleaved every 5 slots.
- Clearly marked with an amber **⭐ SPONSORED** disclosure badge.
- Clicking the badge opens the anti-bias audit drawer explaining the placement criteria.

### 4. Mathematical Score Transparency ("Why Ranked #X?")
- Open any product detail page (e.g., `http://localhost:8000/product/1`).
- The **Ranking Score Breakdown** widget details:
  - Raw metric values (e.g., `30 hrs`, `₹12,990`, `4.5 / 5.0`).
  - Min-Max normalized score ($0.00$ to $1.00$).
  - Configured category weight percentage.
  - Final calculated contribution to the composite score.

### 5. Embedded Search Engine Admin Console
- Navigate to `http://localhost:8000/admin/ranking-engine`.
- Provides an embedded, sandboxed console pointing to `http://localhost:5000/admin`.
- Store managers can adjust category weights, inspect active attributes, configure sponsored campaigns, and review search telemetry directly within the store admin interface.
- Includes a live **B2B API Query Simulator** to test REST calls directly against the engine.

### 6. Zero-Downtime Offline Fallback
- If the ranking engine at port `5000` is stopped, the storefront automatically detects the outage.
- The top header ribbon switches to `Ranking Engine: Offline (Serving Local Noise Catalog Fallback)`.
- Search and catalog browsing remain functional using the local fallback scoring algorithm.

---

## 📡 REST API & Client Endpoints Summary

### Storefront Client Internal Routes (`:8000`)
| Endpoint | Method | Description |
|---|---|---|
| `/` | `GET` | Storefront landing page with top ranked gear & hero banners |
| `/shop` | `GET`, `POST` | Catalog search with category filter, sorting, and custom weights |
| `/product/<int:id>` | `GET` | Product page with full ranking attribution & specs |
| `/api/smart-rank` | `GET`, `POST` | Asynchronous re-ranking endpoint for weight sliders |
| `/cart` | `GET` | Shopping bag overview |
| `/cart/add/<int:id>` | `POST` | Add product to session cart |
| `/checkout` | `POST` | Process order and generate receipt |
| `/admin/` | `GET` | Store operations dashboard |
| `/admin/ranking-engine` | `GET` | Embedded engine admin panel & API simulator |
| `/admin/api/engine-status` | `GET` | Live health and latency check for the ranking engine |

### B2B Engine Service Endpoints (`:5000`)
| Endpoint | Method | Description |
|---|---|---|
| `/api/v1/search` | `GET`, `POST` | Multi-tenant search with custom weights & sponsor interleaving |
| `/api/v1/categories` | `GET` | Tenant schema, categories, active attributes, and bounds |
| `/api/v1/product/<id>` | `GET` | Product composite score, normalized values, and math breakdown |

---

## 👥 Development Team

- **Vaibhav** (Dev-A) — Backend Architecture, Client Integration, Seed Data
- **Shrinivas** (Dev-B) — UI/UX Design System, Admin Embeds, Documentation

---

## 📄 License

**Proprietary & Commercial Software License — All Rights Reserved.**

Copyright © 2026 Vaibhav (01fe24bca300) & Shrinivas (01fe24bca311).

This software, source code, and its documentation are strictly proprietary. Unauthorized copying, modification, distribution, public display, or commercial deployment without an explicit, executed, and paid commercial license agreement is strictly prohibited. See the [LICENSE](file:///home/blue/MiniProject/ECommerce-Site/LICENSE) file for terms and commercial licensing inquiries.
