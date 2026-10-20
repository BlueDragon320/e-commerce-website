import uuid
import time
import random
from flask import render_template, request, redirect, url_for, session, jsonify, flash, current_app
from app import db
from app.models import Product, CartItem, Order, OrderItem
from app.engine_client import engine_client
from . import storefront

def get_session_id():
    """Ensure a unique session ID exists for anonymous shopping cart."""
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    return session['session_id']

@storefront.route('/')
def index():
    """
    Homepage displaying hero banners, featured categories,
    and 'Top Ranked by Engine' product grid fetched via engine_client.search().
    """
    engine_res = engine_client.search(limit=6)
    ranked_products = engine_res.get('results', [])
    sponsored = [p for p in ranked_products if p.get('is_sponsored')]
    organic = [p for p in ranked_products if not p.get('is_sponsored')]
    ranked_products = sponsored + organic
    engine_status = engine_res.get('engine_status', 'offline')
    engine_health = engine_client.health_check()

    featured_products = Product.query.filter_by(is_featured=True).limit(8).all()
    categories_raw = db.session.query(Product.category).distinct().all()
    local_cats = {c[0] for c in categories_raw if c[0]}
    engine_cats_data = engine_client.get_categories().get('categories', [])
    engine_cats = {c['name'] for c in engine_cats_data if c.get('name')}
    categories = sorted(list(local_cats.union(engine_cats)))

    return render_template(
        'storefront/index.html',
        ranked_products=ranked_products,
        featured_products=featured_products,
        categories=categories,
        engine_status=engine_status,
        engine_health=engine_health
    )

@storefront.route('/shop', methods=['GET', 'POST'])
def shop():
    """
    Catalog page supporting search 'q', category filter, sorting,
    and dynamic custom_weights (passed via query params or POST).
    """
    q = request.args.get('q', '').strip()
    category = request.args.get('category', '').strip()
    sort_by = request.args.get('sort', 'relevant').strip()
    if not sort_by:
        sort_by = 'relevant'
    
    # Custom weights parameters (optional, e.g. for API/testing)
    w_battery = request.args.get('w_battery') or request.form.get('w_battery')
    w_price = request.args.get('w_price') or request.form.get('w_price')
    w_rating = request.args.get('w_rating') or request.form.get('w_rating')
    w_anc = request.args.get('w_anc') or request.form.get('w_anc')

    custom_weights = None
    if any([w_battery, w_price, w_rating, w_anc]):
        try:
            wb = float(w_battery or 35.0)
            wp = float(w_price or 35.0)
            wr = float(w_rating or 15.0)
            wa = float(w_anc or 15.0)
            custom_weights = {
                'Battery Life (hours)': wb,
                'Price (INR)': wp,
                'Rating': wr,
                'Active Noise Cancelling': wa
            }
        except (ValueError, TypeError):
            custom_weights = None

    # Dynamically determine category_id for engine
    engine_categories_data = engine_client.get_categories().get('categories', [])
    category_name_to_id = {c['name']: c['category_id'] for c in engine_categories_data if 'name' in c and 'category_id' in c}
    cat_id = category_name_to_id.get(category)

    # Execute search via engine_client
    search_res = engine_client.search(
        query=q,
        category_id=cat_id,
        custom_weights=custom_weights,
        limit=50
    )

    products = search_res.get('results', [])
    engine_status = search_res.get('engine_status', 'offline')

    # If a specific category was requested by user, filter precisely
    if category:
        products = [p for p in products if p.get('category_name') == category or p.get('category') == category]

    # Sorting options:
    # 1. 'relevant' (default): engine weighted composite score
    # 2. 'price_asc': low to high price
    # 3. 'price_desc': high to low price
    # 4. 'rating': customer rating (highest rated according to weight on top)
    if sort_by == 'price_asc':
        products = sorted(products, key=lambda p: float(p.get('price') or 0.0))
    elif sort_by == 'price_desc':
        products = sorted(products, key=lambda p: -float(p.get('price') or 0.0))
    elif sort_by == 'rating':
        products = sorted(
            products,
            key=lambda p: (
                -float(p.get('rating') or p.get('attributes', {}).get('Rating', {}).get('raw_value', 0.0) or 0.0),
                -float(p.get('composite_score', 0.0) or 0.0)
            )
        )
    else:
        # Default: 'relevant' / 'rank' -> sorted by engine composite score
        products = sorted(
            products,
            key=lambda p: -float(p.get('composite_score', 0.0) or 0.0)
        )
        sort_by = 'relevant'

    # CRITICAL: Sponsored products ALWAYS come on top (#1 position)
    sponsored_items = [p for p in products if p.get('is_sponsored')]
    organic_items = [p for p in products if not p.get('is_sponsored')]
    products = sponsored_items + organic_items

    # Assign display rank order (Sponsored products lead at #1..k)
    for idx, item in enumerate(products, start=1):
        item['display_rank'] = idx

    if request.headers.get('Accept') == 'application/json' or request.args.get('format') == 'json':
        return jsonify({
            'status': 'success',
            'engine_status': engine_status,
            'total': len(products),
            'products': products
        })

    categories_raw = db.session.query(Product.category).distinct().all()
    local_cats = {c[0] for c in categories_raw if c[0]}
    engine_cats = {c['name'] for c in engine_categories_data if c.get('name')}
    categories = sorted(list(local_cats.union(engine_cats)))

    return render_template(
        'storefront/shop.html',
        products=products,
        q=q,
        selected_category=category,
        sort_by=sort_by,
        categories=categories,
        custom_weights=custom_weights,
        engine_status=engine_status
    )

@storefront.route('/product/<int:product_id>')
def product_detail(product_id):
    """
    Product detail page showing product specs, images, reviews,
    and engine ranking score breakdown ('Why is this ranked #X?').
    """
    product = db.session.get(Product, product_id)
    breakdown_data = engine_client.get_product_breakdown(product_id)

    # Find price attribute by looking through score_breakdown case-insensitively
    engine_price = None
    for item in breakdown_data.get('score_breakdown', []):
        if 'price' in item.get('attribute_name', '').lower():
            try:
                engine_price = float(item.get('raw_value'))
                break
            except (ValueError, TypeError):
                pass

    if not product:
        if breakdown_data.get('status') == 'success':
            # Synthesize display product from engine data and persist to local DB
            price_val = engine_price if (engine_price is not None and engine_price > 0) else 2999.0

            product = Product(
                id=product_id,
                name=breakdown_data.get('name', f"Product #{product_id}"),
                slug=f"product-{product_id}",
                category=breakdown_data.get('category_name', 'Electronics'),
                price=price_val,
                rating=4.2,
                review_count=145,
                image_url='https://images.unsplash.com/photo-1590658268037-6bf12165a8df?w=600',
                description='High performance electronics integrated with Weighted Ranking Engine analytics.',
                in_stock=True
            )
            try:
                db.session.add(product)
                db.session.commit()
            except Exception:
                db.session.rollback()
                product = db.session.get(Product, product_id)
        else:
            flash(f"Product #{product_id} not found.", "warning")
            return redirect(url_for('storefront.shop'))
    else:
        # If product already exists and price in local DB is <= 5.0, sync with engine price attribute
        if engine_price is not None and engine_price > 5.0 and product.price <= 5.0:
            product.price = engine_price
            try:
                db.session.commit()
            except Exception:
                db.session.rollback()

    related_products = Product.query.filter(
        Product.category == product.category,
        Product.id != product.id
    ).limit(4).all()

    return render_template(
        'storefront/product_detail.html',
        product=product,
        breakdown=breakdown_data.get('score_breakdown', []),
        composite_score=breakdown_data.get('composite_score', 0.0),
        score_pct=breakdown_data.get('score_pct', 'N/A'),
        is_sponsored=breakdown_data.get('is_sponsored', False),
        engine_status=breakdown_data.get('engine_status', 'offline'),
        related_products=related_products
    )

@storefront.route('/api/smart-rank', methods=['GET', 'POST'])
def smart_rank():
    """
    JSON endpoint for client-side dynamic weight sliders that calls
    engine_client.search(custom_weights=...) and returns re-ranked products with composite scores.
    """
    data = request.get_json(silent=True) or {}
    if not data and request.args:
        data = request.args.to_dict()

    category_id = data.get('category_id', 4)
    try:
        category_id = int(category_id)
    except (ValueError, TypeError):
        category_id = 4

    custom_weights = data.get('custom_weights')
    q = data.get('q', '')

    # Allow flat params in JSON like {w_battery: 40, w_price: 30, ...}
    if not custom_weights:
        custom_weights = {}
        if 'w_battery' in data or 'Battery Life (hours)' in data:
            custom_weights['Battery Life (hours)'] = float(data.get('w_battery') or data.get('Battery Life (hours)', 35))
        if 'w_price' in data or 'Price (INR)' in data:
            custom_weights['Price (INR)'] = float(data.get('w_price') or data.get('Price (INR)', 35))
        if 'w_rating' in data or 'Rating' in data:
            custom_weights['Rating'] = float(data.get('w_rating') or data.get('Rating', 15))
        if 'w_anc' in data or 'Active Noise Cancelling' in data:
            custom_weights['Active Noise Cancelling'] = float(data.get('w_anc') or data.get('Active Noise Cancelling', 15))

    search_res = engine_client.search(
        query=q,
        category_id=category_id,
        custom_weights=custom_weights,
        limit=data.get('limit', 20)
    )

    return jsonify(search_res)

# -----------------------------------------------------------------------------
# Cart and Simulated Checkout Flow
# -----------------------------------------------------------------------------

def calculate_order_totals(subtotal: float):
    """Calculate subtotal, shipping fee, GST, and total according to app configuration."""
    free_threshold = current_app.config.get('FREE_SHIPPING_THRESHOLD', 999.0)
    shipping_fee = current_app.config.get('SHIPPING_FEE', 99.0)
    gst_percent = current_app.config.get('GST_PERCENT', 18.0)

    shipping = 0.0 if (subtotal >= free_threshold or subtotal == 0) else shipping_fee
    gst = round(subtotal * (gst_percent / 100.0), 2)
    total = round(subtotal + shipping + gst, 2)
    return {
        'subtotal': round(subtotal, 2),
        'shipping': shipping,
        'gst': gst,
        'total': total
    }

@storefront.route('/cart')
def view_cart():
    """Render the user's shopping cart."""
    sid = get_session_id()
    items = CartItem.query.filter_by(session_id=sid).all()
    subtotal = sum(item.subtotal for item in items)
    totals = calculate_order_totals(subtotal)
    shipping = totals['shipping']
    gst = totals['gst']
    total = totals['total']

    if request.headers.get('Accept') == 'application/json' or request.args.get('format') == 'json':
        return jsonify({
            'session_id': sid,
            'items': [item.to_dict() for item in items],
            'subtotal': totals['subtotal'],
            'shipping': shipping,
            'gst': gst,
            'total': total,
            'count': sum(item.quantity for item in items)
        })

    return render_template(
        'storefront/cart.html',
        items=items,
        subtotal=totals['subtotal'],
        shipping=shipping,
        gst=gst,
        total=total
    )

@storefront.route('/cart/add/<int:product_id>', methods=['GET', 'POST'])
def add_to_cart(product_id):
    """Add a product to the user's cart."""
    sid = get_session_id()
    product = db.get_or_404(Product, product_id)

    qty = 1
    if request.is_json:
        qty = int(request.get_json().get('quantity', 1))
    elif request.form.get('quantity'):
        qty = int(request.form.get('quantity', 1))
    elif request.args.get('quantity'):
        qty = int(request.args.get('quantity', 1))

    item = CartItem.query.filter_by(session_id=sid, product_id=product.id).first()
    if item:
        item.quantity += qty
    else:
        item = CartItem(session_id=sid, product_id=product.id, quantity=qty)
        db.session.add(item)
    db.session.commit()

    if request.is_json or request.headers.get('Accept') == 'application/json':
        items = CartItem.query.filter_by(session_id=sid).all()
        return jsonify({
            'status': 'success',
            'message': f"Added {product.name} to cart",
            'cart_count': sum(i.quantity for i in items),
            'cart_total': sum(i.subtotal for i in items)
        })

    flash(f"Added '{product.name}' to cart!", 'success')
    return redirect(request.referrer or url_for('storefront.view_cart'))

@storefront.route('/cart/remove/<int:item_id>', methods=['GET', 'POST'])
def remove_from_cart(item_id):
    """Remove an item from the cart."""
    sid = get_session_id()
    item = CartItem.query.filter_by(id=item_id, session_id=sid).first()
    if item:
        prod_name = item.product.name if item.product else 'Item'
        db.session.delete(item)
        db.session.commit()
        if request.is_json or request.headers.get('Accept') == 'application/json':
            return jsonify({'status': 'success', 'message': f"Removed {prod_name}"})
        flash(f"Removed '{prod_name}' from cart.", 'info')

    return redirect(url_for('storefront.view_cart'))

@storefront.route('/cart/update/<int:item_id>', methods=['POST'])
def update_cart_quantity(item_id):
    """Update item quantity in cart."""
    sid = get_session_id()
    item = CartItem.query.filter_by(id=item_id, session_id=sid).first()
    if not item:
        return jsonify({'status': 'error', 'message': 'Item not found'}), 404

    qty = int(request.form.get('quantity') or request.get_json(silent=True, force=True).get('quantity', 1))
    if qty <= 0:
        db.session.delete(item)
    else:
        item.quantity = qty
    db.session.commit()

    if request.is_json or request.headers.get('Accept') == 'application/json':
        items = CartItem.query.filter_by(session_id=sid).all()
        return jsonify({
            'status': 'success',
            'cart_count': sum(i.quantity for i in items),
            'cart_total': sum(i.subtotal for i in items)
        })

    return redirect(url_for('storefront.view_cart'))

@storefront.route('/checkout', methods=['GET', 'POST'])
def checkout():
    """Checkout page and order creation."""
    sid = get_session_id()
    items = CartItem.query.filter_by(session_id=sid).all()
    if not items:
        flash("Your cart is empty!", "warning")
        return redirect(url_for('storefront.shop'))

    subtotal = sum(item.subtotal for item in items)
    totals = calculate_order_totals(subtotal)
    shipping = totals['shipping']
    gst = totals['gst']
    total = totals['total']

    if request.method == 'POST':
        for item in items:
            if not item.product:
                flash("An item in your cart is no longer available.", "warning")
                return redirect(url_for('storefront.view_cart'))
            if not item.product.in_stock:
                flash(f"Item '{item.product.name}' is currently out of stock.", "warning")
                return redirect(url_for('storefront.view_cart'))

        name = request.form.get('customer_name', 'Valued Customer').strip()
        email = request.form.get('customer_email', 'customer@example.com').strip()
        address = request.form.get('address', '123 Tech Park, Bangalore').strip()

        order_num = f"NOISE-{int(time.time())}-{uuid.uuid4().hex[:6].upper()}"
        order = Order(
            order_number=order_num,
            customer_name=name,
            customer_email=email,
            address=address,
            subtotal=totals['subtotal'],
            shipping_fee=shipping,
            gst_amount=gst,
            total_amount=total,
            status='completed'
        )
        db.session.add(order)
        db.session.flush()

        for item in items:
            order_item = OrderItem(
                order_id=order.id,
                product_id=item.product_id,
                quantity=item.quantity,
                unit_price=item.product.price if item.product else 0.0
            )
            db.session.add(order_item)
            db.session.delete(item)

        db.session.commit()

        if request.is_json or request.headers.get('Accept') == 'application/json':
            return jsonify({
                'status': 'success',
                'order_number': order_num,
                'total_amount': total
            })

        flash(f"Order #{order_num} placed successfully!", "success")
        return redirect(url_for('storefront.order_success', order_number=order_num))

    return render_template(
        'storefront/checkout.html',
        items=items,
        subtotal=totals['subtotal'],
        shipping=shipping,
        gst=gst,
        total=total
    )

@storefront.route('/order-success/<order_number>')
def order_success(order_number):
    """Order confirmation screen."""
    order = db.first_or_404(db.select(Order).filter_by(order_number=order_number))
    return render_template('storefront/order_success.html', order=order)
