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

    password_hash = db.Column(db.String(150))

    is_approved = db.Column(db.Boolean, default=False)
    is_verified = db.Column(db.Boolean, default=False)

    verification_status =db.Column(db.String(20), default='unverified', nullable=False)

    reset_token = db.Column(db.String(200), nullable=True)
    reset_token_expiry = db.Column(db.DateTime, nullable=True)

    date_joined = db.Column(db.DateTime,default=lambda: datetime.now(timezone.utc))

    role = db.Column(db.String(50), nullable=False, default='buyer')
    campus = db.Column(db.String(120), nullable=True)



    products = db.relationship('Product',backref=db.backref('seller', lazy=True))

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
    product_type = db.Column(db.String(100), nullable=False)
    brand = db.Column(db.String(100), nullable=True)
    condition = db.Column(db.String(100), nullable=False)


    current_price = db.Column(db.Float, nullable=False)
    previous_price = db.Column(db.Float, nullable=True)

    in_stock = db.Column(db.Integer, default=0)

    product_picture = db.Column(db.String(1000), nullable=False)

    flash_sale = db.Column(db.Boolean, default=False)

    date_added = db.Column(db.DateTime,default=lambda: datetime.now(timezone.utc))

    seller_id = db.Column(db.Integer,db.ForeignKey('customer.id'),nullable=False)


class Wishlist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    date_added = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    customer = db.relationship('Customer', backref=db.backref('wishlist_items', lazy=True))
    product = db.relationship('Product', backref=db.backref('wishlisted_by', lazy=True))


class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    quantity = db.Column(db.Integer, nullable=False)

    customer_id = db.Column(db.Integer,db.ForeignKey('customer.id'),nullable=False)

    product_id = db.Column(db.Integer,db.ForeignKey('product.id'),nullable=False)

    customer = db.relationship('Customer',backref=db.backref('cart_items', lazy=True))

    product = db.relationship('Product',backref=db.backref('cart_entries', lazy=True))


class Order(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    customer_id = db.Column(db.Integer,db.ForeignKey('customer.id',ondelete='RESTRICT'),nullable=False)

    status = db.Column(db.String(50),default='Pending Payment')

    payment_status = db.Column(db.String(50),default='Unpaid')

    payment_reference = db.Column(db.String(200),nullable=True)

    shipping_fee = db.Column(db.Float, nullable=False, default=0.0)

    date_created = db.Column(db.DateTime,default=lambda: datetime.now(timezone.utc))

    customer = db.relationship('Customer',backref=db.backref('orders', lazy=True))

    items = db.relationship('OrderItem',backref='order',cascade='all, delete-orphan',lazy=True)

    @property
    def total_amount(self):
        items_total = sum(item.price_at_purchase * item.quantity for item in self.items)
        return items_total + self.shipping_fee


class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    quantity = db.Column(db.Integer,nullable=False,default=1)

    price_at_purchase = db.Column(db.Float,nullable=False)

    date_added = db.Column(db.DateTime,default=lambda: datetime.now(timezone.utc))

    order_id = db.Column(db.Integer,db.ForeignKey('order.id'),nullable=False)

    product_id = db.Column(db.Integer,db.ForeignKey('product.id'),nullable=False)

    product = db.relationship('Product', backref=db.backref('order_items', lazy=True))


class Conversation(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    buyer_id = db.Column(
        db.Integer,
        db.ForeignKey('customer.id'),
        nullable=False
    )

    seller_id = db.Column(
        db.Integer,
        db.ForeignKey('customer.id'),
        nullable=False
    )

    product_id = db.Column(
        db.Integer,
        db.ForeignKey('product.id'),
        nullable=True
    )

    date_created = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc)
    )

    buyer = db.relationship(
        'Customer',
        foreign_keys=[buyer_id],
        backref=db.backref('buyer_conversations', lazy=True)
    )

    seller = db.relationship(
        'Customer',
        foreign_keys=[seller_id],
        backref=db.backref('seller_conversations', lazy=True)
    )

    product = db.relationship(
        'Product',
        backref=db.backref('conversations', lazy=True)
    )

    messages = db.relationship(
        'Message',
        backref='conversation',
        cascade='all, delete-orphan',
        lazy=True
    )


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    conversation_id = db.Column(
        db.Integer,
        db.ForeignKey('conversation.id'),
        nullable=False
    )

    sender_id = db.Column(
        db.Integer,
        db.ForeignKey('customer.id'),
        nullable=False
    )

    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False, nullable=False)

    date_sent = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc)
    )

    sender = db.relationship(
        'Customer',
        backref=db.backref('sent_messages', lazy=True)
    )