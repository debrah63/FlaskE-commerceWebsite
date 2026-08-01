from flask import Blueprint, render_template, flash, redirect, request, url_for
from flask_login import login_required, current_user

from .models import Product, Cart, Order, OrderItem
from . import db


views = Blueprint('views', __name__)

SHIPPING_FEE = 50


@views.route('/')
def home():
    items = Product.query.order_by(Product.date_added.desc()).all()
    return render_template('home.html', items=items)


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

    item_exists = Cart.query.filter_by(
        product_id=item_id,
        customer_id=current_user.id
    ).first()


    if item_exists:

        item_exists.quantity += 1
        db.session.commit()

        flash(
            f'Quantity of {item_exists.product.product_name} updated'
        )

        return redirect(request.referrer or url_for('views.home'))


    new_cart_item = Cart(
        quantity=1,
        product_id=item_to_add.id,
        customer_id=current_user.id
    )


    db.session.add(new_cart_item)
    db.session.commit()

    flash(f'{item_to_add.product_name} added to cart')

    return redirect(request.referrer or url_for('views.home'))



@views.route('/cart')
@login_required
def show_cart():

    cart = Cart.query.filter_by(
        customer_id=current_user.id
    ).all()


    amount = sum(
        item.product.current_price * item.quantity
        for item in cart
        if item.product
    )


    return render_template(
        'cart.html',
        cart=cart,
        amount=amount,
        total=amount + SHIPPING_FEE
    )



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

    cart = Cart.query.filter_by(
        customer_id=current_user.id
    ).all()


    if not cart:

        flash('Your cart is empty')
        return redirect(url_for('views.home'))


    total = sum(
        item.product.current_price * item.quantity
        for item in cart
        if item.product
    )


    return render_template(
        'checkout.html',
        cart=cart,
        total=total + SHIPPING_FEE
    )



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
            new_item = OrderItem(
                order_id=new_order.id,
                product_id=item.product_id,
                quantity=item.quantity,
                price_at_purchase=item.product.current_price
            )
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


    orders = Order.query.filter_by(
        customer_id=current_user.id
    ).order_by(
        Order.date_created.desc()
    ).all()


    return render_template(
        'orders.html',
        orders=orders
    )