# Function Map — Noise E-Commerce Platform

A directory of application components, modules, classes, and helper functions within the **Noise E-Commerce Platform**.

---

## 1. Application Lifecycle & Entrypoint

### `run.py`
- **Role**: Command-Line entrypoint to launch the storefront server.
- **Logic**:
  - Detects `FLASK_ENV` from environment (defaults to `development`).
  - Calls `create_app(env)` to construct the application instance.
  - Extracts `PORT` (default: 8000) and `DEBUG` status from application config.
  - Prints startup banner including microservice connection target.
  - Executes `app.run(host='0.0.0.0', port=port, debug=debug)`.

### `app/__init__.py` (Application Factory)
- **Functions**:
  - `create_app(config_name: str = 'development') -> Flask`:
    - Instantiates Flask app.
    - Loads configuration object from `config.py`.
    - Ensures persistent `instance/` storage directory exists.
    - Attaches `SQLAlchemy` database instance (`db.init_app(app)`).
    - Dynamically registers blueprints (`storefront` mounted at `/`, `admin` mounted at `/admin`).
    - Establishes global context processor `inject_global_data()`.
    - Initializes relational database tables (`db.create_all()`) within app context.
  - `inject_global_data() -> dict`:
    - Context processor injecting global template variables into all Jinja2 templates:
      - `cart_count`: Total sum of item quantities for the current session.
      - `cart_total`: Monetary sum of all item subtotals for the current session.
      - `currency`: Configured currency symbol (defaults to `₹`).
      - `engine_url`: Target URL of the B2B Ranking Engine (`http://localhost:5000`).

---

## 2. Configuration (`config.py`)

### `BaseConfig`
- Baseline configuration shared across all environments:
  - `SECRET_KEY`: Session encryption and CSRF signing key.
  - `SQLALCHEMY_TRACK_MODIFICATIONS`: Set to `False` for performance optimization.
  - `RANKING_ENGINE_URL`: Microservice target address (default: `http://localhost:5000`).
  - `RANKING_COMPANY_ID`: Default tenant identifier for Noise (`1`).
  - `PORT`: Storefront listener port (`8000`).
  - `CURRENCY_SYMBOL`: `₹`.
  - `FREE_SHIPPING_THRESHOLD`: `999.0`.
  - `SHIPPING_FEE`: `99.0`.
  - `GST_PERCENT`: `18.0`.

### `DevelopmentConfig` (inherits `BaseConfig`)
- `DEBUG = True`
- `SQLALCHEMY_DATABASE_URI`: Local SQLite database at `instance/noise_ecommerce.db`.

### `TestingConfig` (inherits `BaseConfig`)
- `TESTING = True`
- `WTF_CSRF_ENABLED = False`
- `SQLALCHEMY_DATABASE_URI`: In-memory SQLite (`sqlite:///:memory:`).

### `ProductionConfig` (inherits `BaseConfig`)
- `DEBUG = False`
- `SQLALCHEMY_DATABASE_URI`: Production DB URI or fallback instance SQLite DB.

---

## 3. Data Models — Engine 1 (`app/models.py`)

### `Product(db.Model)`
- **Table**: `products`
- **Fields**:
  - `id`: Integer, primary key.
  - `name`: String(200), required.
  - `slug`: String(200), unique, indexed, required.
  - `category`: String(100), indexed, required.
  - `price`: Float, required.
  - `original_price`: Float, optional.
  - `image_url`: String(500), optional.
  - `description`: Text, optional.
  - `rating`: Float, default `0.0`.
  - `review_count`: Integer, default `0`.
  - `battery_life`: Float, hours, default `0.0`.
  - `anc`: Boolean, default `False`.
  - `specs_json`: Text, serialized specifications dictionary.
  - `in_stock`: Boolean, default `True`.
  - `is_featured`: Boolean, default `False`.
  - `is_sponsored`: Boolean, default `False`.
  - `created_at`: DateTime (UTC).
- **Properties & Methods**:
  - `discount_pct -> int`: Calculates percentage markdown from `original_price` to `price`.
  - `specs -> dict`: Deserializes JSON string into a Python dictionary with fault tolerance.
  - `specs.setter`: Automatically serializes dictionary or list inputs into JSON string.
  - `to_dict() -> dict`: Serializes all fields and computed properties for JSON responses.
  - `__repr__() -> str`: Human-readable debug representation.

### `CartItem(db.Model)`
- **Table**: `cart_items`
- **Fields**:
  - `id`: Integer, primary key.
  - `session_id`: String(100), indexed, required.
  - `product_id`: Integer, foreign key to `products.id`.
  - `quantity`: Integer, default `1`.
- **Relationships & Properties**:
  - `product`: Relationship to `Product`, backref `cart_items`.
  - `subtotal -> float`: Computes `product.price * quantity` rounded to 2 decimals.
  - `to_dict() -> dict`: Serializes cart item including nested product dictionary.

### `Order(db.Model)`
- **Table**: `orders`
- **Fields**:
  - `id`: Integer, primary key.
  - `order_number`: String(50), unique, indexed.
  - `customer_name`: String(100), required.
  - `customer_email`: String(120), required.
  - `address`: Text, required.
  - `total_amount`: Float, required.
  - `status`: String(50), default `'completed'`.
  - `created_at`: DateTime (UTC).
- **Relationships & Methods**:
  - `items`: Cascading one-to-many relationship with `OrderItem` (`cascade='all, delete-orphan'`).
  - `to_dict() -> dict`: Serializes order and all child `order_items`.

### `OrderItem(db.Model)`
- **Table**: `order_items`
- **Fields**:
  - `id`: Integer, primary key.
  - `order_id`: Integer, foreign key to `orders.id`.
  - `product_id`: Integer, foreign key to `products.id`.
  - `quantity`: Integer, required.
  - `unit_price`: Float, historical snapshot of price at purchase time.
- **Relationships & Properties**:
  - `product`: Relationship to `Product`.
  - `subtotal -> float`: Computes `unit_price * quantity`.
  - `to_dict() -> dict`: Serializes order item with product name snapshot.

---

## 4. Templates & Interface — Engine 3

### `app/templates/base.html`
- Master layout template implementing:
  - Responsive header with brand identity and glowing cyan symbol.
  - Microservice health pill (`RANKING ENGINE :5000`) linked to `engine_url`.
  - Navigation links: Shop, Categories, Orders.
  - Interactive shopping cart button with dynamic badge bound to `cart_count`.
  - Flashed alerts block supporting `success`, `error`/`danger`, `warning`, and `info`.
  - Main extensible block `{% block content %}{% endblock %}`.
  - Multi-column footer with student academic capstone disclaimer.

### `app/templates/index.html`
- Extends `base.html` to provide:
  - Hero banner with headline: *"Listen to the Noise Within — Smart Tech Powered by Multi-Criteria Ranked Search"*.
  - Cyber-themed soundwave visual showcase with live telemetry preview.
  - Category navigation pills for Smartwatches, Wireless Earbuds, Headphones, and Audio Gear.
  - Featured products grid illustrating high-priority products with spec pills and pricing.
  - Ranking engine integration explanation card detailing Min-Max normalization, dynamic weights, and 1:5 anti-bias sponsored interleaving.

### `app/static/css/style.css`
- Design system stylesheet defining:
  - Color variables with electric cyan (`#00F2FE`) and deep dark mode surfaces (`#080c14`, `#0e1526`).
  - Typography settings for Space Grotesk, Plus Jakarta Sans, and JetBrains Mono.
  - Glassmorphic card styling, gradient borders, and ambient background glow.
  - Mobile responsive layouts covering viewport widths down to 480px.
