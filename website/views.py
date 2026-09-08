from flask import Blueprint, render_template, flash, redirect, request, url_for, current_app
from flask_login import login_required, current_user
import requests

from .models import Product, Cart, Order, OrderItem
from . import db


views = Blueprint('views', __name__)

SHIPPING_FEE = 50


@views.route('/')
def home():
    items = Product.query.order_by(Product.date_added.desc()).all()
    return render_template('home.html', items=items)

@views.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user=current_user)


@views.route('/media/<path:filename>')
def get_image(filename):
    from flask import send_from_directory
    return send_from_directory('../media', filename)


@views.route('/add-to-cart/<int:item_id>')
@login_required
def add_to_cart(item_id):

    item_to_add = db.session.get(Product, item_id)

    if item_to_add.in_stock <= 0:
        flash('Sorry, this product is currently out of stock')
        return redirect(request.referrer or url_for('views.home'))

    if not item_to_add:
        flash('Product not found.', 'danger')
        return redirect(request.referrer or url_for('views.home'))

    item_exists = Cart.query.filter_by(product_id=item_id,customer_id=current_user.id).first()


    if item_exists:

        item_exists.quantity += 1
        db.session.commit()

        flash(f'Quantity of {item_exists.product.product_name} updated')

        return redirect(request.referrer or url_for('views.home'))


    new_cart_item = Cart(quantity=1,product_id=item_to_add.id,customer_id=current_user.id)


    db.session.add(new_cart_item)
    db.session.commit()

    flash(f'{item_to_add.product_name} added to cart')

    return redirect(request.referrer or url_for('views.home'))



@views.route('/cart')
@login_required
def show_cart():

    cart = Cart.query.filter_by(customer_id=current_user.id).all()


    amount = sum(item.product.current_price * item.quantity for item in cart if item.product)


    return render_template('cart.html',cart=cart,amount=amount,total=amount + SHIPPING_FEE)



@views.route('/increase-cart/<int:cart_id>')
@login_required
def increase_cart(cart_id):

    cart_item = db.session.get(Cart, cart_id)


    if cart_item and cart_item.customer_id == current_user.id:
        if cart_item.quantity < cart_item.product.in_stock:

            cart_item.quantity += 1
            db.session.commit()
        else:
            flash('Maximum available stock exceeded.', 'danger')



    return redirect(url_for('views.show_cart'))



@views.route('/decrease-cart/<int:cart_id>')
@login_required
def decrease_cart(cart_id):

    cart_item = db.session.get(Cart, cart_id)


    if cart_item and cart_item.customer_id == current_user.id:

        if cart_item.quantity > 1:
            cart_item.quantity -= 1

        else:
            db.session.delete(cart_item)


        db.session.commit()


    return redirect(url_for('views.show_cart'))



@views.route('/remove-from-cart/<int:cart_id>')
@login_required
def remove_from_cart(cart_id):

    cart_item = db.session.get(Cart, cart_id)


    if cart_item and cart_item.customer_id == current_user.id:

        db.session.delete(cart_item)
        db.session.commit()


    return redirect(url_for('views.show_cart'))



@views.route('/checkout')
@login_required
def checkout():

    cart = Cart.query.filter_by(customer_id=current_user.id).all()


    if not cart:

        flash('Your cart is empty')

        return redirect(url_for('views.home'))


    total = sum(item.product.current_price * item.quantity for item in cart if item.product)


    return render_template('checkout.html',cart=cart,total=total + SHIPPING_FEE)



@views.route('/place-order', methods=['POST'])
@login_required
def place_order():

    cart = Cart.query.filter_by(customer_id=current_user.id).all()

    if not cart:
        flash('Your cart is empty')
        return redirect(url_for('views.home'))

    try:
        for item in cart:
            if item.quantity > item.product.in_stock:
                flash(f'Only {item.product.product_name} "{item.product.product_name}" left in stock.')
                return redirect(url_for('views.show_cart'))

        new_order = Order(customer_id=current_user.id, status='Pending Payment')
        db.session.add(new_order)
        db.session.flush()

        for item in cart:
            new_item = OrderItem(order_id=new_order.id,product_id=item.product_id,quantity=item.quantity,price_at_purchase=item.product.current_price)
            db.session.add(new_item)
            db.session.delete(item)

        db.session.commit()

        flash('Order placed successfully! Awaiting payment.')
        return redirect(url_for('views.order_history'))

    except Exception as e:
        db.session.rollback()
        print(e)
        flash('Something went wrong while placing your order')
        return redirect(url_for('views.show_cart'))


@views.route('/orders')
@login_required
def order_history():


    orders = Order.query.filter_by(customer_id=current_user.id).order_by(Order.date_created.desc()).all()


    return render_template('orders.html',orders=orders)


@views.route('/initiate-payment/<int:order_id>')
@login_required
def initiate_payment(order_id):

    order = db.session.get(Order, order_id)

    if not order or order.customer_id != current_user.id:
        flash('Order not found')
        return redirect(url_for('views.order_history'))

    if order.status != 'Pending Payment':
        flash('This order has already been processed')
        return redirect(url_for('views.order_history'))

    secret_key = current_app.config['PAYSTACK_SECRET_KEY']

    amount_in_pesewas = int(order.total_amount * 100)

    headers = {
        'Authorization': f'Bearer {secret_key}',
        'Content-Type': 'application/json'
    }

    payload = {
        'email': current_user.email,
        'amount': amount_in_pesewas,
        'currency': 'GHS',
        'callback_url': url_for(
            'views.verify_payment',
            order_id=order.id,
            _external=True
        )
    }

    try:

        response = requests.post('https://api.paystack.co/transaction/initialize',json=payload,headers=headers,timeout=30)

        data = response.json()

        if data.get('status'):

            order.payment_reference = data['data']['reference']
            db.session.commit()

            return redirect(data['data']['authorization_url'])

        flash('Could not initiate payment. Please try again.')

    except requests.exceptions.RequestException as e:

        print(e)
        flash('Unable to connect to Paystack.')

    return redirect(url_for('views.order_history'))


@views.route('/verify-payment/<int:order_id>')
@login_required
def verify_payment(order_id):

    order = db.session.get(Order, order_id)

    if not order or order.customer_id != current_user.id:
        flash('Order not found')
        return redirect(url_for('views.order_history'))

    if order.status == 'Paid':
        flash('Payment has already been verified.')
        return redirect(url_for('views.order_history'))

    secret_key = current_app.config['PAYSTACK_SECRET_KEY']

    headers = {'Authorization': f'Bearer {secret_key}'}

    try:

        response = requests.get(f'https://api.paystack.co/transaction/verify/{order.payment_reference}',headers=headers,timeout=30)

        data = response.json()

        if data.get('status') and data['data']['status'] == 'success':

            for item in order.items:

                if item.product.in_stock < item.quantity:

                    flash(f'{item.product.product_name} is no longer available.')

                    return redirect(url_for('views.order_history'))

            order.status = 'Paid'

            for item in order.items:
                item.product.in_stock -= item.quantity

            db.session.commit()

            flash('Payment successful! Your order has been confirmed.')

        else:

            flash('Payment was not successful.')

    except requests.exceptions.RequestException as e:

        print(e)
        flash('Unable to verify payment at the moment.')

    return redirect(url_for('views.order_history'))