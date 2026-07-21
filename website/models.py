from . import db
from flask_login import UserMixin
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash

USER_ROLES = ('buyer', 'seller', 'admin')

class Customer(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True)
    username = db.Column(db.String(120), unique=True)
    password_hash = db.Column(db.String(150))
    reset_token = db.Column(db.String(200),  nullable=True)
    reset_token_expiry = db.Column(db.DateTime, nullable=True)
    date_joined = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    role = db.Column(db.String(50),nullable=False, default='buyer')
    is_approved = db.Column(db.Boolean, default=False)

    products = db.relationship('Product', backref=db.backref('seller', lazy=True))


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
    current_price = db.Column(db.Float, nullable=False)
    previous_price = db.Column(db.Float, nullable=False)
    in_stock = db.Column(db.Integer, default=0)
    product_picture = db.Column(db.String(1000), nullable=False)
    flash_sale = db.Column(db.Boolean, default=False)
    date_added = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    seller_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)