from app.models import Product, CartItem, Order, OrderItem

def test_homepage(client):
    """Test homepage loads with hero banners and top ranked grid."""
    resp = client.get('/')
    assert resp.status_code == 200
    assert b'noise' in resp.data
    assert b'Top Ranked by Engine' in resp.data

def test_shop_page(client):
    """Test catalog page with search, filters, and dynamic weights."""
    resp = client.get('/shop')
    assert resp.status_code == 200
    assert b'Product Catalog' in resp.data

    # Test with search query
    resp_search = client.get('/shop?q=VS102')
    assert resp_search.status_code == 200
    assert b'VS102' in resp_search.data

    # Test with category filter
    resp_cat = client.get('/shop?category=Smartwatches')
    assert resp_cat.status_code == 200

    # Test with sorting
    resp_sort = client.get('/shop?sort=price_asc')
    assert resp_sort.status_code == 200

    # Test with custom weights via GET
    resp_weights = client.get('/shop?w_battery=40&w_price=30&w_rating=15&w_anc=15')
    assert resp_weights.status_code == 200

def test_product_detail(client):
    """Test product detail page and engine explainability breakdown."""
    resp = client.get('/product/1')
    assert resp.status_code == 200
    assert b'Why is this ranked' in resp.data
    assert b'Noise' in resp.data
    assert b'Add to Cart' in resp.data

def test_smart_rank_api(client):
    """Test dynamic weight sliders JSON API."""
    payload = {
        'category_id': 1,
        'custom_weights': {
            'Battery Life (hours)': 40.0,
            'Price (INR)': 30.0,
            'Rating': 15.0,
            'Active Noise Cancelling': 15.0
        }
    }
    resp = client.post('/api/smart-rank', json=payload)
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['status'] == 'success'
    assert 'results' in data

def test_cart_operations(client):
    """Test adding, updating, viewing, and removing cart items."""
    # View initial empty cart
    resp = client.get('/cart')
    assert resp.status_code == 200
    assert b'empty' in resp.data.lower()

    # Add product 1 to cart
    resp_add = client.post('/cart/add/1', data={'quantity': 2}, follow_redirects=True)
    assert resp_add.status_code == 200
    assert b'Shopping Bag' in resp_add.data
    assert b'Noise' in resp_add.data

    # Check cart JSON API
    resp_json = client.get('/cart', headers={'Accept': 'application/json'})
    assert resp_json.status_code == 200
    data = resp_json.get_json()
    assert data['count'] == 2
    assert len(data['items']) == 1
    item_id = data['items'][0]['id']

    # Update quantity
    resp_update = client.post(f'/cart/update/{item_id}', data={'quantity': 3}, follow_redirects=True)
    assert resp_update.status_code == 200

    # Remove from cart
    resp_remove = client.get(f'/cart/remove/{item_id}', follow_redirects=True)
    assert resp_remove.status_code == 200
    assert b'empty' in resp_remove.data.lower()

def test_checkout_flow(client):
    """Test full checkout flow: add to cart -> checkout form -> place order."""
    # Add product 2 to cart
    client.post('/cart/add/2', data={'quantity': 1}, follow_redirects=True)

    # View checkout
    resp_checkout_get = client.get('/checkout')
    assert resp_checkout_get.status_code == 200
    assert b'Delivery Address' in resp_checkout_get.data

    # Submit checkout order
    order_data = {
        'customer_name': 'Test Shopper',
        'customer_email': 'shopper@test.com',
        'address': '123 Test Street, Bengaluru - 560001'
    }
    resp_checkout_post = client.post('/checkout', data=order_data, follow_redirects=True)
    assert resp_checkout_post.status_code == 200
    assert b'Order Confirmed' in resp_checkout_post.data
    assert b'Test Shopper' in resp_checkout_post.data

    # Verify order in DB has financial breakdown and UUID suffix in order number
    order = Order.query.filter_by(customer_email='shopper@test.com').first()
    assert order is not None
    assert order.subtotal > 0
    assert order.gst_amount > 0
    assert order.total_amount == round(order.subtotal + order.shipping_fee + order.gst_amount, 2)
    assert len(order.order_number.split('-')[-1]) == 6
    o_dict = order.to_dict()
    assert o_dict['subtotal'] == order.subtotal
    assert o_dict['shipping_fee'] == order.shipping_fee
    assert o_dict['gst_amount'] == order.gst_amount

    # Verify cart is now empty
    resp_cart = client.get('/cart')
    assert b'empty' in resp_cart.data.lower()

def test_checkout_out_of_stock_rejected(client):
    """Test that checkout is blocked if an item in the cart is out of stock."""
    from app import db
    p = db.session.get(Product, 1)
    p.in_stock = False
    db.session.commit()

    # Add out of stock product to cart directly
    cart_item = CartItem(session_id='test-oos-session', product_id=1, quantity=1)
    db.session.add(cart_item)
    db.session.commit()

    with client.session_transaction() as sess:
        sess['session_id'] = 'test-oos-session'

    resp = client.post('/checkout', data={
        'customer_name': 'OOS Customer',
        'customer_email': 'oos@test.com',
        'address': '123 Address'
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert b'out of stock' in resp.data.lower()
    # Order should not have been created
    assert Order.query.filter_by(customer_email='oos@test.com').first() is None

    # Reset in_stock
    p.in_stock = True
    db.session.commit()

def test_search_synonyms_ear_phones(client):
    """Test searching for 'ear phones' surfaces audio products and earbuds."""
    resp = client.get('/shop?q=ear+phones')
    assert resp.status_code == 200
    assert b'VS102' in resp.data or b'Air Buds' in resp.data
    # Verify no smartwatches are returned when searching audio synonyms
    assert b'Ultra 3' not in resp.data

def test_search_synonyms_ear_pods(client):
    """Test searching for 'ear pods' surfaces earbuds."""
    resp = client.get('/shop?q=ear+pods')
    assert resp.status_code == 200
    assert b'VS102' in resp.data or b'Air Buds' in resp.data
    assert b'Ultra 3' not in resp.data

def test_search_headphones_whitespace_and_typos(client):
    """Test that 'headphones', 'head phones', 'head-phones', and 'headfone' all return headphones."""
    for query in ['headphones', 'head phones', 'head-phones', 'headfone', 'headfones']:
        resp = client.get(f'/shop?q={query}&format=json')
        assert resp.status_code == 200
        prods = resp.get_json().get('products', [])
        assert len(prods) >= 1
        names = [p['name'] for p in prods]
        assert any('Headphones' in n or 'Noise Two' in n for n in names)

def test_search_typo_tolerance_and_whitespace(client):
    """Test typo tolerance across categories: samrtwatch, nekband, sunglases, earfones."""
    # Typos in categories
    resp_watch = client.get('/shop?q=samrtwatch&format=json')
    assert resp_watch.status_code == 200
    assert len(resp_watch.get_json().get('products', [])) >= 1

    resp_neck = client.get('/shop?q=nekband&format=json')
    assert resp_neck.status_code == 200
    assert len(resp_neck.get_json().get('products', [])) >= 1

    resp_ear = client.get('/shop?q=earfones&format=json')
    assert resp_ear.status_code == 200
    assert len(resp_ear.get_json().get('products', [])) >= 1

def test_sorting_strategies(client):
    """Test sorting by price_asc, price_desc, rating, and relevant with sponsored items pinned to top."""
    # Price Low to High: sponsored items lead, organic items sorted ascending
    resp_low = client.get('/shop?sort=price_asc&format=json')
    assert resp_low.status_code == 200
    data_low = resp_low.get_json()['products']
    spons_low = [p for p in data_low if p.get('is_sponsored')]
    organic_low = [p for p in data_low if not p.get('is_sponsored')]
    assert data_low[:len(spons_low)] == spons_low
    prices_organic = [p['price'] for p in organic_low]
    assert prices_organic == sorted(prices_organic)

    # Price High to Low: sponsored items lead, organic items sorted descending
    resp_high = client.get('/shop?sort=price_desc&format=json')
    assert resp_high.status_code == 200
    data_high = resp_high.get_json()['products']
    spons_high = [p for p in data_high if p.get('is_sponsored')]
    organic_high = [p for p in data_high if not p.get('is_sponsored')]
    assert data_high[:len(spons_high)] == spons_high
    prices_high = [p['price'] for p in organic_high]
    assert prices_high == sorted(prices_high, reverse=True)

    # Rating (highest rated on top for organic items, sponsored items lead)
    resp_rating = client.get('/shop?sort=rating&format=json')
    assert resp_rating.status_code == 200
    data_rating = resp_rating.get_json()['products']
    spons_rating = [p for p in data_rating if p.get('is_sponsored')]
    organic_rating = [p for p in data_rating if not p.get('is_sponsored')]
    assert data_rating[:len(spons_rating)] == spons_rating
    ratings = [
        float(p.get('rating') or p.get('attributes', {}).get('Rating', {}).get('raw_value', 0.0) or 0.0)
        for p in organic_rating
    ]
    assert ratings == sorted(ratings, reverse=True)

def test_sponsored_pinned_at_rank_one(client):
    """Verify that when a product is sponsored, it is guaranteed rank #1 across all sort modes."""
    # In Wireless Earbuds category, Noise Air Buds Pro 2 with ANC is sponsored
    for sort_mode in ['relevant', 'price_asc', 'price_desc', 'rating']:
        resp = client.get(f'/shop?category=Wireless+Earbuds&sort={sort_mode}&format=json')
        assert resp.status_code == 200
        prods = resp.get_json().get('products', [])
        assert len(prods) > 0
        first_item = prods[0]
        assert first_item['is_sponsored'] is True
        assert first_item['display_rank'] == 1
        assert 'Noise Air Buds Pro 2' in first_item['name']

def test_storefront_hides_dynamic_weights(client):
    """Customer storefront must NOT expose dynamic smart weights sliders."""
    resp = client.get('/shop')
    assert resp.status_code == 200
    # Technical slider elements must be absent
    assert b'slider_battery' not in resp.data
    assert b'slider_price' not in resp.data
    assert b'Dynamic Smart Weights' not in resp.data
    # Clean customer controls must be present
    assert b'Relevant' in resp.data
    assert b'Sort Strategy' in resp.data
    assert b'Customer Rating' in resp.data

