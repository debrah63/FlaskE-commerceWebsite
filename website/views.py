from itertools import product

from flask import Blueprint, render_template, flash, redirect, request, jsonify
from flask_login import login_required, current_user
from .models import Product, Cart
from . import db

views = Blueprint('views', __name__)


@views.route('/')
def home():
    products = Product.query.all()
    return render_template('home.html', products=products)


@views.route('/media/<path:filename>')
def get_image(filename):
    from flask import send_from_directory
    return send_from_directory('../media', filename)


@views.route('/add-to-cart/<int:item_id>')
@login_required
def add_to_cart(item_id):
    item_to_add = Product.query.get(item_id)

    if not item_to_add:
        flash('Product not found')
        return redirect(request.referrer or '/')

    item_exists = Cart.query.filter_by(product_link=item_id, customer_link=current_user.id).first()

    if item_exists:
        item_exists.quantity += 1
        db.session.commit()
        flash(f'Quantity of {item_exists.product.product_name} updated')
        return redirect(request.referrer or '/')

    new_cart_item = Cart()
    new_cart_item.quantity = 1
    new_cart_item.product_link = item_to_add.id
    new_cart_item.customer_link = current_user.id

    db.session.add(new_cart_item)
    db.session.commit()
    flash(f'{item_to_add.product_name} added to cart')

    return redirect(request.referrer or '/')


@views.route('/cart')
@login_required
def show_cart():
    cart = Cart.query.filter_by(customer_link=current_user.id).all()

    amount = 0
    for item in cart:
        amount += item.product.current_price * item.quantity

    return render_template('cart.html', cart=cart, amount=amount, total=amount + 50)


@views.route('/increase-cart/<int:cart_id>')
@login_required
def increase_cart(cart_id):
    cart_item = Cart.query.get(cart_id)

    if cart_item and cart_item.customer_link == current_user.id:
        cart_item.quantity += 1
        db.session.commit()

    return redirect('/cart')


@views.route('/decrease-cart/<int:cart_id>')
@login_required
def decrease_cart(cart_id):
    cart_item = Cart.query.get(cart_id)

    if cart_item and cart_item.customer_link == current_user.id:
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
        else:
            db.session.delete(cart_item)
        db.session.commit()

    return redirect('/cart')


@views.route('/remove-from-cart/<int:cart_id>')
@login_required
def remove_from_cart(cart_id):
    cart_item = Cart.query.get(cart_id)

    if cart_item and cart_item.customer_link == current_user.id:
        db.session.delete(cart_item)
        db.session.commit()

    return redirect('/cart')