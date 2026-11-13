import json
from app import db
from app.models import Product

def test_admin_auth_required(client):
    """Assert unauthenticated access redirects to /admin/login or returns 401 for JSON requests."""
    resp = client.get('/admin')
    assert resp.status_code == 302
    assert '/admin/login' in resp.headers.get('Location', '')

    resp_json = client.get('/admin', headers={'Accept': 'application/json'})
    assert resp_json.status_code == 401
    data = resp_json.get_json()
    assert data['status'] == 'error'
    assert 'Unauthorized' in data['message']

    resp_json_arg = client.get('/admin?format=json')
    assert resp_json_arg.status_code == 401

def test_admin_login_logout_flow(client):
    """Test GET /admin/login, POST authentication, and logout."""
    # GET login page
    resp = client.get('/admin/login')
    assert resp.status_code == 200
    assert b'Admin Login' in resp.data

    # POST with invalid credentials
    resp_fail = client.post('/admin/login', data={'username': 'wrong', 'password': 'wrongpassword'})
    assert resp_fail.status_code == 200
    assert b'Invalid admin username or password.' in resp_fail.data

    # POST with correct credentials
    resp_success = client.post('/admin/login', data={'username': 'admin', 'password': 'admin123'})
    assert resp_success.status_code == 302
    assert '/admin' in resp_success.headers.get('Location', '')

    # Follow redirect to dashboard
    resp_dash = client.get('/admin')
    assert resp_dash.status_code == 200
    assert b'Store Overview' in resp_dash.data

    # Visiting login while authenticated redirects to dashboard
    resp_relogin = client.get('/admin/login')
    assert resp_relogin.status_code == 302
    assert '/admin' in resp_relogin.headers.get('Location', '')

    # Logout
    resp_logout = client.get('/admin/logout')
    assert resp_logout.status_code == 302
    assert '/admin/login' in resp_logout.headers.get('Location', '')

    # Post-logout admin access should redirect to login
    resp_after_logout = client.get('/admin')
    assert resp_after_logout.status_code == 302
    assert '/admin/login' in resp_after_logout.headers.get('Location', '')

def test_admin_dashboard(admin_client):
    """Test admin dashboard loads with store metrics, health status, and top ranked products."""
    resp = admin_client.get('/admin')
    assert resp.status_code == 200
    assert b'Store Overview' in resp.data
    assert b'Ranking Engine' in resp.data
    assert b'Top Engine-Ranked Products' in resp.data

    # Test JSON output
    resp_json = admin_client.get('/admin', headers={'Accept': 'application/json'})
    assert resp_json.status_code == 200
    data = resp_json.get_json()
    assert data['status'] == 'success'
    assert 'stats' in data
    assert 'product_count' in data['stats']
    assert data['stats']['product_count'] >= 3
    assert 'top_ranked_products' in data

def test_admin_products_list(admin_client):
    """Test admin products catalog listing with Engine Rank and Composite Score columns."""
    resp = admin_client.get('/admin/products')
    assert resp.status_code == 200
    assert b'Noise Buds VS102 Test' in resp.data
    assert b'Add New Product' in resp.data
    assert b'Engine Rank' in resp.data
    assert b'Composite Score' in resp.data

def test_admin_product_crud(admin_client):
    """Test creating, editing, and deleting a product via admin routes."""
    # Create product
    new_data = {
        'name': 'Noise Test Headphones 500',
        'category': 'Headphones',
        'price': 1899.0,
        'original_price': 3999.0,
        'battery_life': 60.0,
        'rating': 4.3,
        'review_count': 45,
        'description': 'Created via admin test.',
        'image_url': 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=600',
        'anc': 'on',
        'in_stock': 'on',
        'is_featured': 'on'
    }
    resp_create = admin_client.post('/admin/products/new', data=new_data, follow_redirects=True)
    assert resp_create.status_code == 200
    assert b'Noise Test Headphones 500' in resp_create.data

    prod = Product.query.filter_by(name='Noise Test Headphones 500').first()
    assert prod is not None
    assert prod.anc is True

    # Edit product
    edit_data = new_data.copy()
    edit_data['price'] = 1799.0
    edit_data['description'] = 'Updated description.'
    resp_edit = admin_client.post(f'/admin/products/{prod.id}/edit', data=edit_data, follow_redirects=True)
    assert resp_edit.status_code == 200
    assert prod.price == 1799.0

    # Delete product
    resp_del = admin_client.post(f'/admin/products/{prod.id}/delete', follow_redirects=True)
    assert resp_del.status_code == 200
    assert db.session.get(Product, prod.id) is None

def test_admin_ranking_engine_page(admin_client):
    """
    Test dedicated Search Engine Admin Panel satisfying:
    a) Embedded iframe view of Weighted Ranking Engine console
    b) Native status check & schema inspection
    c) Section A Schema bounds & Section B Ranked Products
    d) Interactive Weight Simulator
    """
    resp = admin_client.get('/admin/ranking-engine')
    assert resp.status_code == 200
    assert b'Weighted Ranking Engine' in resp.data
    assert b'Engine Schema & Attribute Weight Configuration' in resp.data
    assert b'Section A: Attribute Schema' in resp.data
    assert b'Section B: Ranked Products in this Category' in resp.data
    assert b'Interactive Weight Simulator' in resp.data
    assert b'Simulated Ranking Order' in resp.data
    # Assert iframe element present
    assert b'<iframe' in resp.data
    assert b':5000' in resp.data

def test_admin_ranking_engine_product_names_and_rankings(admin_client):
    """
    Verify that /admin/ranking-engine:
    - Returns HTTP 200.
    - Contains product names in the response (e.g. Noise Buds VS102, Noise ColorFit Ultra 3, Noise Air Buds Pro 2).
    - Contains engine ranking elements (e.g. rank badges, composite scores).
    """
    resp = admin_client.get('/admin/ranking-engine')
    assert resp.status_code == 200
    # Verify product names appear in ranked product tables
    assert b'Noise Buds VS102' in resp.data
    assert b'Noise ColorFit Ultra 3' in resp.data
    assert b'Noise Air Buds Pro 2' in resp.data
    # Verify engine ranking elements
    assert b'Composite Score' in resp.data
    assert b'Score:' in resp.data or b'score_pct' in resp.data or b'%' in resp.data
    assert b'#' in resp.data or b'Rank' in resp.data

def test_admin_products_renders_engine_rank_metadata(admin_client):
    """
    Verify /admin/products renders products along with Engine Rank metadata and composite scores.
    """
    resp = admin_client.get('/admin/products')
    assert resp.status_code == 200
    assert b'Engine Rank' in resp.data
    assert b'Composite Score' in resp.data
    assert b'Noise Buds VS102 Test' in resp.data

    # Test JSON API endpoint for /admin/products
    resp_json = admin_client.get('/admin/products', headers={'Accept': 'application/json'})
    assert resp_json.status_code == 200
    data = resp_json.get_json()
    assert data['status'] == 'success'
    assert 'products' in data
    assert len(data['products']) > 0
    p = data['products'][0]
    assert 'engine_rank' in p
    assert 'composite_score' in p

def test_admin_api_engine_status(admin_client):
    """Test JSON endpoint returning live health, active attributes, and ranked products from the engine."""
    resp = admin_client.get('/admin/api/engine-status')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['status'] == 'success'
    assert 'health' in data
    assert 'engine_data' in data
    assert 'company_id' in data
    assert data['company_id'] == 1
    # Verify categories and ranked products
    categories = data['engine_data'].get('categories', [])
    assert len(categories) >= 1
    assert any('ranked_products' in cat and len(cat['ranked_products']) > 0 for cat in categories)

def test_admin_toggle_sponsored(admin_client):
    """Test toggling sponsored flag on a product via POST /admin/products/<id>/toggle-sponsored."""
    prod = Product.query.first()
    assert prod is not None
    initial_sponsored = prod.is_sponsored

    resp = admin_client.post(f'/admin/products/{prod.id}/toggle-sponsored', follow_redirects=True)
    assert resp.status_code == 200

    db.session.refresh(prod)
    assert prod.is_sponsored != initial_sponsored

    # Toggle back to original state
    resp2 = admin_client.post(f'/admin/products/{prod.id}/toggle-sponsored', follow_redirects=True)
    assert resp2.status_code == 200
    db.session.refresh(prod)
    assert prod.is_sponsored == initial_sponsored


def test_admin_product_rating_conversion(admin_client):
    """Test creating and editing products with rating scores (0-100 and 0-5.0)."""
    # 1. Create with rating = 88.0 -> converts to 4.4
    data_88 = {
        'name': 'Rating Test 88',
        'category': 'Wireless Earbuds',
        'price': 1499.0,
        'rating': 88.0,
        'review_count': 100
    }
    resp = admin_client.post('/admin/products/new', data=data_88, follow_redirects=True)
    assert resp.status_code == 200
    prod_88 = Product.query.filter_by(name='Rating Test 88').first()
    assert prod_88 is not None
    assert prod_88.rating == 4.4

    # 2. Create with rating = 100.0 -> converts to 5.0
    data_100 = {
        'name': 'Rating Test 100',
        'category': 'Wireless Earbuds',
        'price': 1499.0,
        'rating': 100.0,
        'review_count': 100
    }
    resp = admin_client.post('/admin/products/new', data=data_100, follow_redirects=True)
    assert resp.status_code == 200
    prod_100 = Product.query.filter_by(name='Rating Test 100').first()
    assert prod_100 is not None
    assert prod_100.rating == 5.0

    # 3. Create with rating = 0.0 -> preserved as 0.0
    data_0 = {
        'name': 'Rating Test 0',
        'category': 'Wireless Earbuds',
        'price': 1499.0,
        'rating': 0.0,
        'review_count': 100
    }
    resp = admin_client.post('/admin/products/new', data=data_0, follow_redirects=True)
    assert resp.status_code == 200
    prod_0 = Product.query.filter_by(name='Rating Test 0').first()
    assert prod_0 is not None
    assert prod_0.rating == 0.0

    # 4. Edit product to rating = 95.0 -> converts to 4.75
    edit_data = {
        'name': 'Rating Test 88',
        'category': 'Wireless Earbuds',
        'price': 1499.0,
        'rating': 95.0,
        'review_count': 100
    }
    resp_edit = admin_client.post(f'/admin/products/{prod_88.id}/edit', data=edit_data, follow_redirects=True)
    assert resp_edit.status_code == 200
    db.session.refresh(prod_88)
    assert prod_88.rating == 4.75

    # 5. Edit product back to 4.2 -> preserved as 4.2 (0-5.0 range preserved)
    edit_data_std = {
        'name': 'Rating Test 88',
        'category': 'Wireless Earbuds',
        'price': 1499.0,
        'rating': 4.2,
        'review_count': 100
    }
    resp_edit_std = admin_client.post(f'/admin/products/{prod_88.id}/edit', data=edit_data_std, follow_redirects=True)
    assert resp_edit_std.status_code == 200
    db.session.refresh(prod_88)
    assert prod_88.rating == 4.2

    # 6. Verify product form template contains updated UI labels and help caption
    resp_form = admin_client.get('/admin/products/new')
    assert resp_form.status_code == 200
    assert b'Customer Rating (0 - 100 or 0 - 5.0)' in resp_form.data
    assert b'Accepts 0 - 5.0 stars or 0 - 100 score' in resp_form.data

