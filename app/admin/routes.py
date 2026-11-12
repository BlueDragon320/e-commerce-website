from datetime import datetime, timezone
import hmac
import json
from urllib.parse import urlparse, urljoin
from flask import render_template, request, redirect, url_for, flash, jsonify, current_app, session
from slugify import slugify
from app import db
from app.models import Product, Order, OrderItem
from app.engine_client import engine_client
from . import admin

@admin.context_processor
def inject_admin_data():
    return {
        'engine_url': current_app.config.get('RANKING_ENGINE_URL', 'http://localhost:5000')
    }

def is_safe_url(target):
    if not target:
        return False
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc

@admin.before_request
def require_admin_login():
    if request.endpoint in ('admin.login', 'admin.logout'):
        return None
    if not session.get('admin_logged_in'):
        if request.headers.get('Accept') == 'application/json' or request.args.get('format') == 'json':
            return jsonify({'status': 'error', 'message': 'Unauthorized: Admin authentication required'}), 401
        return redirect(url_for('admin.login', next=request.url))

@admin.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('admin_logged_in'):
        return redirect(url_for('admin.dashboard'))
    
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        expected_user = current_app.config.get('ADMIN_USERNAME', 'admin')
        expected_pass = current_app.config.get('ADMIN_PASSWORD', 'admin123')
        
        is_valid_user = hmac.compare_digest(username, expected_user) or hmac.compare_digest(username, 'admin@noise.com')
        if is_valid_user and hmac.compare_digest(password, expected_pass):
            session['admin_logged_in'] = True
            flash('Logged in successfully.', 'success')
            next_url = request.args.get('next')
            if next_url and is_safe_url(next_url):
                return redirect(next_url)
            return redirect(url_for('admin.dashboard'))
        else:
            error = 'Invalid admin username or password.'

    return render_template('admin/login.html', error=error)

@admin.route('/logout', methods=['GET', 'POST'])
def logout():
    session.pop('admin_logged_in', None)
    flash('Logged out successfully.', 'info')
    return redirect(url_for('admin.login'))

@admin.route('/')
@admin.route('', strict_slashes=False)
def dashboard():
    """
    Store admin dashboard with revenue metrics, order counts, product inventory,
    top ranked products from the engine, and live ranking engine status.
    """
    total_revenue = db.session.query(db.func.sum(Order.total_amount)).scalar() or 0.0
    order_count = Order.query.count()
    product_count = Product.query.count()
    out_of_stock_count = Product.query.filter_by(in_stock=False).count()
    
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(8).all()
    engine_health = engine_client.health_check()

    # Fetch top ranked products from the engine across categories
    try:
        top_res = engine_client.search(limit=6)
        top_ranked_products = top_res.get('results', [])
    except Exception as e:
        current_app.logger.warning(f"Error fetching top ranked products: {e}")
        top_ranked_products = []

    stats = {
        'total_revenue': round(total_revenue, 2),
        'order_count': order_count,
        'product_count': product_count,
        'out_of_stock_count': out_of_stock_count,
        'engine_health': engine_health
    }

    if request.headers.get('Accept') == 'application/json' or request.args.get('format') == 'json':
        return jsonify({
            'status': 'success',
            'stats': stats,
            'recent_orders': [o.to_dict() for o in recent_orders],
            'top_ranked_products': top_ranked_products
        })

    return render_template(
        'admin/dashboard.html',
        stats=stats,
        recent_orders=recent_orders,
        engine_health=engine_health,
        top_ranked_products=top_ranked_products
    )

def get_all_categories():
    """Fetches category names from engine_client.get_categories() and merges with db.session.query(Product.category).distinct()."""
    local_cats_raw = db.session.query(Product.category).distinct().all()
    local_cats = {c[0] for c in local_cats_raw if c[0]}
    engine_cats_data = engine_client.get_categories().get('categories', [])
    engine_cats = {c['name'] for c in engine_cats_data if c.get('name')}
    return sorted(list(local_cats.union(engine_cats)))

@admin.route('/products')
def products():
    """Product catalog listing and inventory management enriched with engine ranks."""
    q = request.args.get('q', '').strip()
    category = request.args.get('category', '').strip()
    query = Product.query

    if q:
        query = query.filter(Product.name.ilike(f"%{q}%"))
    if category:
        query = query.filter_by(category=category)

    prods = query.order_by(Product.id.asc()).all()
    categories = get_all_categories()

    # Enrich each local product with its engine rank and composite score
    rank_lookup = {}
    try:
        search_res = engine_client.search(limit=100)
        for r in search_res.get('results', []):
            pid = r.get('local_product_id') or r.get('product_id')
            pname = r.get('name')
            info = {
                'rank': r.get('rank'),
                'composite_score': r.get('composite_score'),
                'score_pct': r.get('score_pct')
            }
            if pid is not None:
                rank_lookup[pid] = info
            if pname:
                rank_lookup[pname] = info
    except Exception as e:
        current_app.logger.warning(f"Error fetching engine rank info: {e}")

    for p in prods:
        info = rank_lookup.get(p.id) or rank_lookup.get(p.name) or {}
        p.engine_rank = info.get('rank')
        p.composite_score = info.get('composite_score')
        p.score_pct = info.get('score_pct')

    if request.headers.get('Accept') == 'application/json' or request.args.get('format') == 'json':
        products_json = []
        for p in prods:
            d = p.to_dict()
            d['engine_rank'] = getattr(p, 'engine_rank', None)
            d['composite_score'] = getattr(p, 'composite_score', None)
            d['score_pct'] = getattr(p, 'score_pct', None)
            products_json.append(d)
        return jsonify({
            'status': 'success',
            'count': len(prods),
            'products': products_json
        })

    return render_template(
        'admin/products.html',
        products=prods,
        categories=categories,
        selected_category=category,
        q=q
    )

@admin.route('/products/new', methods=['GET', 'POST'])
def new_product():
    """Add a new product to catalog."""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        category = request.form.get('category', '').strip()
        if category == '__new__':
            category = request.form.get('custom_category', '').strip()
        try:
            price = float(request.form.get('price', 0))
        except (ValueError, TypeError):
            price = 0.0

        try:
            orig_val = request.form.get('original_price')
            original_price = float(orig_val) if orig_val else None
        except (ValueError, TypeError):
            original_price = None

        try:
            battery_life = float(request.form.get('battery_life', 0))
        except (ValueError, TypeError):
            battery_life = 0.0

        anc = True if request.form.get('anc') in ['true', 'on', '1'] else False

        try:
            rating = float(request.form.get('rating', 4.0))
            if rating > 5.0 and rating <= 100.0:
                rating = round(rating / 20.0, 2)
        except (ValueError, TypeError):
            rating = 4.0

        try:
            review_count = int(request.form.get('review_count', 0))
        except (ValueError, TypeError):
            review_count = 0

        description = request.form.get('description', '')
        image_url = request.form.get('image_url', '')
        in_stock = True if request.form.get('in_stock', 'on') in ['true', 'on', '1'] else False
        is_featured = True if request.form.get('is_featured') in ['true', 'on', '1'] else False
        is_sponsored = True if request.form.get('is_sponsored') in ['true', 'on', '1'] else False

        slug = slugify(name)
        existing = db.session.scalar(db.select(Product).filter_by(slug=slug))
        if existing:
            slug = f"{slug}-{int(datetime.now(timezone.utc).timestamp())}"

        prod = Product(
            name=name,
            slug=slug,
            category=category,
            price=price,
            original_price=original_price,
            battery_life=battery_life,
            anc=anc,
            rating=rating,
            review_count=review_count,
            description=description,
            image_url=image_url,
            in_stock=in_stock,
            is_featured=is_featured,
            is_sponsored=is_sponsored
        )
        db.session.add(prod)
        db.session.commit()
        try:
            engine_client.sync_product_to_engine(prod)
        except Exception as e:
            current_app.logger.warning(f"Failed to sync product to engine: {e}")
        flash(f"Product '{name}' created successfully!", "success")
        return redirect(url_for('admin.products'))

    return render_template('admin/product_form.html', product=None, categories=get_all_categories())

@admin.route('/products/<int:product_id>/edit', methods=['GET', 'POST'])
def edit_product(product_id):
    """Edit existing product."""
    prod = db.get_or_404(Product, product_id)
    if request.method == 'POST':
        prod.name = request.form.get('name', prod.name).strip()
        category = request.form.get('category', prod.category).strip()
        if category == '__new__':
            category = request.form.get('custom_category', '').strip()
        prod.category = category
        try:
            prod.price = float(request.form.get('price', prod.price))
        except (ValueError, TypeError):
            pass

        orig_price = request.form.get('original_price')
        try:
            prod.original_price = float(orig_price) if orig_price else None
        except (ValueError, TypeError):
            pass

        try:
            prod.battery_life = float(request.form.get('battery_life', prod.battery_life))
        except (ValueError, TypeError):
            pass

        prod.anc = True if request.form.get('anc') in ['true', 'on', '1'] else False

        try:
            rating = float(request.form.get('rating', prod.rating))
            if rating > 5.0 and rating <= 100.0:
                rating = round(rating / 20.0, 2)
            prod.rating = rating
        except (ValueError, TypeError):
            pass

        try:
            prod.review_count = int(request.form.get('review_count', prod.review_count))
        except (ValueError, TypeError):
            pass

        prod.description = request.form.get('description', prod.description)
        prod.image_url = request.form.get('image_url', prod.image_url)
        prod.in_stock = True if request.form.get('in_stock') in ['true', 'on', '1'] else False
        prod.is_featured = True if request.form.get('is_featured') in ['true', 'on', '1'] else False
        prod.is_sponsored = True if request.form.get('is_sponsored') in ['true', 'on', '1'] else False

        db.session.commit()
        try:
            engine_client.sync_product_to_engine(prod)
        except Exception as e:
            current_app.logger.warning(f"Failed to sync product to engine: {e}")
        flash(f"Product '{prod.name}' updated successfully!", "success")
        return redirect(url_for('admin.products'))

    return render_template('admin/product_form.html', product=prod, categories=get_all_categories())

@admin.route('/products/<int:product_id>/toggle-sponsored', methods=['POST'])
def toggle_sponsored(product_id):
    """Toggle a product's sponsored status. When enabled, this product is pinned to the #1 slot."""
    prod = db.get_or_404(Product, product_id)
    prod.is_sponsored = not prod.is_sponsored
    db.session.commit()

    # Log/sync with ranking engine via engine_client
    try:
        health = engine_client.health_check()
        if health.get('status') == 'online':
            current_app.logger.info(
                f"Toggled sponsored status for '{prod.name}' (id={prod.id}) to {prod.is_sponsored}. "
                f"Ranking engine online at {health.get('engine_url')}."
            )
        else:
            current_app.logger.info(
                f"Toggled sponsored status for '{prod.name}' (id={prod.id}) to {prod.is_sponsored}. "
                f"Ranking engine offline."
            )
    except Exception as e:
        current_app.logger.warning(f"Error checking ranking engine status during toggle_sponsored: {e}")

    state = "SPONSORED (now pinned to #1 on top)" if prod.is_sponsored else "Standard"
    flash(f"Product '{prod.name}' is now set to {state}!", "success")
    return redirect(request.referrer or url_for('admin.products'))

@admin.route('/products/<int:product_id>/delete', methods=['POST'])
def delete_product(product_id):
    """Delete a product."""
    prod = db.get_or_404(Product, product_id)
    name = prod.name
    db.session.delete(prod)
    db.session.commit()
    flash(f"Product '{name}' removed from catalog.", "info")
    return redirect(url_for('admin.products'))

@admin.route('/ranking-engine')
def ranking_engine():
    """
    Dedicated Search Engine Admin Panel:
    a) Embedded iframe view of the Weighted Ranking Engine console (http://localhost:5000/admin, /admin/category/1/overview, /insights).
    b) Native status check & schema inspection (connection status, active attributes, weights, weight simulator).
    c) Ranked products per category computed by the engine.
    """
    engine_url = current_app.config.get('RANKING_ENGINE_URL', 'http://localhost:5000')
    company_id = current_app.config.get('RANKING_COMPANY_ID', 1)

    health = engine_client.health_check()
    categories_data = engine_client.get_categories()

    # Fetch ranked products for each category from the ranking engine
    for cat in categories_data.get('categories', []):
        cat_id = cat.get('category_id')
        try:
            search_res = engine_client.search(category_id=cat_id, limit=50)
            cat['ranked_products'] = search_res.get('results', [])
        except Exception as e:
            current_app.logger.warning(f"Error fetching ranked products for category {cat_id}: {e}")
            cat['ranked_products'] = []

    return render_template(
        'admin/ranking_engine.html',
        engine_url=engine_url,
        company_id=company_id,
        health=health,
        categories_data=categories_data,
        categories=categories_data.get('categories', [])
    )

@admin.route('/api/engine-status')
def api_engine_status():
    """
    JSON endpoint returning live health, active attributes, and ranked products from the engine.
    """
    health = engine_client.health_check()
    categories_data = engine_client.get_categories()

    for cat in categories_data.get('categories', []):
        cat_id = cat.get('category_id')
        try:
            search_res = engine_client.search(category_id=cat_id, limit=50)
            cat['ranked_products'] = search_res.get('results', [])
        except Exception as e:
            current_app.logger.warning(f"Error fetching ranked products for category {cat_id}: {e}")
            cat['ranked_products'] = []
    
    return jsonify({
        'status': 'success',
        'health': health,
        'engine_url': current_app.config.get('RANKING_ENGINE_URL', 'http://localhost:5000'),
        'company_id': current_app.config.get('RANKING_COMPANY_ID', 1),
        'engine_data': categories_data
    })
