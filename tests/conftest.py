import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from app import create_app, db
from app.models import Product, Order, OrderItem, CartItem

@pytest.fixture
def app():
    """Create and configure a testing Flask app instance."""
    app = create_app('testing')
    
    with app.app_context():
        db.create_all()
        
        # Seed basic test data
        p1 = Product(
            name="Noise Buds VS102 Test",
            slug="noise-buds-vs102-test",
            category="Wireless Earbuds",
            price=1099.0,
            original_price=2999.0,
            battery_life=50.0,
            anc=False,
            rating=4.2,
            review_count=120,
            image_url="https://images.unsplash.com/photo-1590658268037-6bf12165a8df?w=600",
            description="Test earbuds for unit testing.",
            in_stock=True,
            is_featured=True
        )
        p1.specs = {"Battery": "50 Hours", "Driver": "11mm"}

        p2 = Product(
            name="Noise ColorFit Ultra 3 Test",
            slug="noise-colorfit-ultra-3-test",
            category="Smartwatches",
            price=2999.0,
            original_price=7999.0,
            battery_life=168.0,
            anc=False,
            rating=4.5,
            review_count=350,
            image_url="https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=600",
            description="Test smartwatch with AMOLED.",
            in_stock=True,
            is_featured=True
        )
        p2.specs = {"Display": "1.96 AMOLED", "Battery": "7 days"}

        p3 = Product(
            name="Noise Air Buds Pro 2 ANC Test",
            slug="noise-air-buds-pro-2-anc-test",
            category="Wireless Earbuds",
            price=2499.0,
            original_price=6999.0,
            battery_life=40.0,
            anc=True,
            rating=4.4,
            review_count=210,
            image_url="https://images.unsplash.com/photo-1606220588913-b3aacb4d2f46?w=600",
            description="Test ANC earbuds.",
            in_stock=True,
            is_featured=False,
            is_sponsored=True
        )

        p4 = Product(
            name="Noise Two Wireless Headphones Test",
            slug="noise-two-wireless-headphones-test",
            category="Headphones",
            price=1999.0,
            original_price=4999.0,
            battery_life=50.0,
            anc=False,
            rating=4.3,
            review_count=95,
            image_url="https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=600",
            description="Test on-ear headphones.",
            in_stock=True,
            is_featured=True
        )

        p5 = Product(
            name="Noise Nerve 2 Neckband Test",
            slug="noise-nerve-2-neckband-test",
            category="Neckbands",
            price=999.0,
            original_price=2999.0,
            battery_life=30.0,
            anc=False,
            rating=4.1,
            review_count=80,
            image_url="https://images.unsplash.com/photo-1572536147248-ac59a8abfa4b?w=600",
            description="Test Bluetooth neckband.",
            in_stock=True,
            is_featured=False
        )

        db.session.add_all([p1, p2, p3, p4, p5])
        db.session.commit()

        yield app

        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture
def admin_client(app):
    """A test client authenticated as admin."""
    c = app.test_client()
    with c.session_transaction() as sess:
        sess['admin_logged_in'] = True
    return c

@pytest.fixture
def runner(app):
    """A test CLI runner for the app."""
    return app.test_cli_runner()
