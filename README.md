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
   git clone <repo-url>
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
