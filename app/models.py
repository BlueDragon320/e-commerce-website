from datetime import datetime, timezone
import json
from app import db

class Product(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False, index=True)
    category = db.Column(db.String(100), nullable=False, index=True)
    price = db.Column(db.Float, nullable=False)
    original_price = db.Column(db.Float, nullable=True)
    image_url = db.Column(db.String(500), nullable=True)
    description = db.Column(db.Text, nullable=True)
    rating = db.Column(db.Float, default=0.0)
    review_count = db.Column(db.Integer, default=0)
    battery_life = db.Column(db.Float, default=0.0)  # in hours
    anc = db.Column(db.Boolean, default=False)        # Active Noise Cancelling
    specs_json = db.Column(db.Text, nullable=True)
    in_stock = db.Column(db.Boolean, default=True)
    is_featured = db.Column(db.Boolean, default=False)
    is_sponsored = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    @property
    def discount_pct(self):
        if self.original_price and self.original_price > self.price:
            return int(round((1.0 - (self.price / self.original_price)) * 100))
        return 0

    @property
    def specs(self):
        if self.specs_json:
            try:
                return json.loads(self.specs_json)
            except (json.JSONDecodeError, TypeError):
                return {}
        return {}

    @specs.setter
    def specs(self, value):
        if isinstance(value, (dict, list)):
            self.specs_json = json.dumps(value)
        else:
            self.specs_json = value

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'slug': self.slug,
            'category': self.category,
            'price': self.price,
            'original_price': self.original_price,
            'discount_pct': self.discount_pct,
            'image_url': self.image_url,
            'description': self.description,
            'rating': self.rating,
            'review_count': self.review_count,
            'battery_life': self.battery_life,
            'anc': self.anc,
            'specs': self.specs,
            'in_stock': self.in_stock,
            'is_featured': self.is_featured,
            'is_sponsored': self.is_sponsored,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f"<Product id={self.id} name='{self.name}'>"


class CartItem(db.Model):
    __tablename__ = 'cart_items'

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(100), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1, nullable=False)

    product = db.relationship('Product', backref=db.backref('cart_items', lazy='dynamic'))

    @property
    def subtotal(self):
        if self.product:
            return round(self.product.price * self.quantity, 2)
        return 0.0

    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'product_id': self.product_id,
            'quantity': self.quantity,
            'product': self.product.to_dict() if self.product else None,
            'subtotal': self.subtotal
        }


class Order(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    customer_name = db.Column(db.String(100), nullable=False)
    customer_email = db.Column(db.String(120), nullable=False)
    address = db.Column(db.Text, nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), default='completed', nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    items = db.relationship('OrderItem', backref='order', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'order_number': self.order_number,
            'customer_name': self.customer_name,
            'customer_email': self.customer_email,
            'address': self.address,
            'total_amount': self.total_amount,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'items': [item.to_dict() for item in self.items]
        }


class OrderItem(db.Model):
    __tablename__ = 'order_items'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)

    product = db.relationship('Product')

    @property
    def subtotal(self):
        return round(self.unit_price * self.quantity, 2)

    def to_dict(self):
        return {
            'id': self.id,
            'order_id': self.order_id,
            'product_id': self.product_id,
            'quantity': self.quantity,
            'unit_price': self.unit_price,
            'subtotal': self.subtotal,
            'product_name': self.product.name if self.product else 'Unknown Product'
        }
