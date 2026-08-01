from . import db
from flask_login import UserMixin
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash

USER_ROLES = ('buyer', 'seller', 'admin')


class Customer(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)

    email = db.Column(db.String(120), unique=True)
    username = db.Column(db.String(120), unique=True)

    email_verified = db.Column(db.Boolean, default=False)
    is_approved = db.Column(db.Boolean, default=False)

    password_hash = db.Column(db.String(150))

    reset_token = db.Column(db.String(200), nullable=True)
    reset_token_expiry = db.Column(db.DateTime, nullable=True)

    date_joined = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc)
    )

    role = db.Column(db.String(50), nullable=False, default='buyer')
    is_approved = db.Column(db.Boolean, default=False)

    products = db.relationship(
        'Product',
        backref=db.backref('seller', lazy=True)
    )

    @property
    def password(self):
        raise AttributeError('Password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password=password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password=password)


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    product_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(100), nullable=True)

    current_price = db.Column(db.Float, nullable=False)
    previous_price = db.Column(db.Float, nullable=True)

    in_stock = db.Column(db.Integer, default=0)

    product_picture = db.Column(db.String(1000), nullable=False)

    flash_sale = db.Column(db.Boolean, default=False)

    date_added = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc)
    )

    seller_id = db.Column(
        db.Integer,
        db.ForeignKey('customer.id'),
        nullable=False
    )


class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    quantity = db.Column(db.Integer, nullable=False)

    customer_id = db.Column(
        db.Integer,
        db.ForeignKey('customer.id'),
        nullable=False
    )

    product_id = db.Column(
        db.Integer,
        db.ForeignKey('product.id'),
        nullable=False
    )

    customer = db.relationship(
        'Customer',
        backref=db.backref('cart_items', lazy=True)
    )

    product = db.relationship(
        'Product',
        backref=db.backref('cart_entries', lazy=True)
    )


class Order(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    customer_id = db.Column(
        db.Integer,
        db.ForeignKey('customer.id',ondelete='RESTRICT'),
        nullable=False
    )

    status = db.Column(
        db.String(50),
        default='Pending Payment'
    )

    payment_status = db.Column(
        db.String(50),
        default='Unpaid'
    )

    payment_reference = db.Column(
        db.String(200),
        nullable=True
    )

    date_created = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc)
    )

    customer = db.relationship(
        'Customer',
        backref=db.backref('orders', lazy=True)
    )

    items = db.relationship(
        'OrderItem',
        backref='order',
        cascade='all, delete-orphan',
        lazy=True
    )

    @property
    def total_amount(self):
        return sum(item.price_at_purchase * item.quatity for item in self.items)


class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    quantity = db.Column(
        db.Integer,
        nullable=False,
        default=1
    )

    price_at_purchase = db.Column(
        db.Float,
        nullable=False
    )

    date_added = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc)
    )

    order_id = db.Column(
        db.Integer,
        db.ForeignKey('order.id'),
        nullable=False
    )

    product_id = db.Column(
        db.Integer,
        db.ForeignKey('product.id'),
        nullable=False
    )

    product = db.relationship(
        'Product',
        backref=db.backref('order_items', lazy=True)
    )