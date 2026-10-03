# Setup & Deployment Guide — Noise E-Commerce Storefront

This guide provides step-by-step instructions for installing, configuring, and operating the **Noise E-Commerce Platform** (Storefront Microservice Consumer).

---

## 1. System Prerequisites

Before getting started, ensure your environment meets the following requirements:

- **Python**: Version 3.10 or higher (`python3 --version`)
- **pip**: Package installer for Python (`pip --version`)
- **Git**: Version control system (`git --version`)
- **Web Browser**: Chrome, Firefox, Edge, or Safari with modern CSS Grid support
- **Sister Microservice**: `Product-Catalogue-Ranked-Search` running on port `5000` (optional for offline testing, required for live microservice telemetry).

---

## 2. Installation Steps

### Step 1: Navigate to the Project Directory
```bash
cd /home/blue/Collage-Mini-Project/e-commerce-website
```

### Step 2: Create and Activate a Virtual Environment
It is strongly recommended to isolate dependencies inside a dedicated virtual environment:

```bash
# Create virtual environment named 'venv'
python3 -m venv venv

# Activate on Linux / macOS:
source venv/bin/activate

# Or activate on Windows (PowerShell):
# .\venv\Scripts\Activate.ps1
```

### Step 3: Install Required Dependencies
Install the required packages using the project `requirements.txt`:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

Verified core dependencies include:
- `Flask>=3.0.0`
- `Flask-SQLAlchemy>=3.1.0`
- `requests>=2.31.0`
- `pytest>=7.4.0`

---

## 3. Environment Variables Configuration

The application uses sensible defaults out of the box, but can be customized via environment variables:

| Variable Name | Default Value | Description |
| :--- | :--- | :--- |
| `FLASK_ENV` | `development` | Runtime mode: `development`, `testing`, or `production`. |
| `PORT` | `8000` | Port where the storefront web server listens. |
| `RANKING_ENGINE_URL` | `http://localhost:5000` | Target URL of the Weighted Ranking Engine microservice. |
| `RANKING_COMPANY_ID` | `1` | Multi-tenant tenant identifier assigned to Noise. |
| `SECRET_KEY` | `noise-ecommerce-secret-key-2026` | Secret key used to sign session cookies and CSRF tokens. |
| `DEV_DATABASE_URL` | `sqlite:///instance/noise_ecommerce.db` | Custom database connection URI (optional). |

### Setting Environment Variables (Optional):
```bash
export PORT=8000
export RANKING_ENGINE_URL="http://localhost:5000"
export RANKING_COMPANY_ID=1
export SECRET_KEY="your-production-secret-here"
```

---

## 4. Running the Platform

### Mode A: Running the Complete Dual-Service Stack (Recommended)

To experience the full distributed microservice architecture, start both services concurrently in separate terminal sessions:

#### Terminal 1 — Start the Weighted Ranking Engine (Port 5000):
```bash
cd /home/blue/Collage-Mini-Project/Product-Catalogue-Ranked-Search
source venv/bin/activate 2>/dev/null || true
python run.py
```
*Expected log:*
```text
 * Running on http://127.0.0.1:5000
```

#### Terminal 2 — Start the Noise Storefront (Port 8000):
```bash
cd /home/blue/Collage-Mini-Project/e-commerce-website
source venv/bin/activate 2>/dev/null || true
python run.py
```
*Expected log:*
```text
🚀 Starting Noise E-Commerce Site on http://0.0.0.0:8000 (env: development)
🔗 Ranking Engine URL: http://localhost:5000
 * Running on http://127.0.0.1:8000
```

### Mode B: Standalone Storefront (Offline Fallback Testing)
You can run the storefront without the ranking engine running. The built-in offline fallback architecture seamlessly handles missing upstream responses by falling back to local SQLite product ordering:

```bash
cd /home/blue/Collage-Mini-Project/e-commerce-website
python run.py
```

---

## 5. Verification & Smoke Testing

Once launched, verify the deployment:

1. **Access the Homepage**:
   Open `http://localhost:8000` in your web browser. You should see:
   - Header with the glowing Noise cyan logo (`#00F2FE`).
   - Active microservice status indicator pill (`RANKING ENGINE :5000`).
   - Cart button displaying the default session badge count (`0`).
   - Hero banner: *"Listen to the Noise Within — Smart Tech Powered by Multi-Criteria Ranked Search"*.
   - Domain category pills and featured product cards.
   - Ranking engine integration explanation card.

2. **Verify Database Initialization**:
   Check that SQLite database tables were created:
   ```bash
   ls -la instance/noise_ecommerce.db
   ```

3. **Verify Static Assets**:
   Check that styles load without errors:
   - `http://localhost:8000/static/css/style.css` returns HTTP 200.

---

## 6. Troubleshooting & FAQ

### Issue: Port 8000 Already in Use
**Solution**: Specify a different port using the `PORT` environment variable:
```bash
PORT=8080 python run.py
```

### Issue: Cannot Connect to Ranking Engine (Port 5000)
**Symptom**: Clicking on the `RANKING ENGINE :5000` indicator pill fails to open the upstream API.
**Solution**: Ensure that `Product-Catalogue-Ranked-Search` is started on port 5000. If running on another machine or port, update `RANKING_ENGINE_URL`:
```bash
export RANKING_ENGINE_URL="http://127.0.0.1:5000"
```
Even if the ranking engine is offline, the storefront remains fully functional using local fallback data.

### Issue: Resetting the Database
To reset all catalog and cart tables back to a clean state:
```bash
rm instance/noise_ecommerce.db
python run.py
```
The application will automatically recreate all tables on the next startup.
