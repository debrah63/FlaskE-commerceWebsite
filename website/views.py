from flask import Blueprint, render_template, flash, redirect, request, url_for, current_app
from flask_login import login_required, current_user
import requests
from .shipping import shipping_fee
from .models import Product, Cart, Order, OrderItem, Conversation, Message, Customer
from . import db


views = Blueprint('views', __name__)


@views.route('/')
def home():
    from .models import Wishlist

    campus = request.args.get('campus')
    category = request.args.get('category')

    query = Product.query

    # Filter by campus
    if campus:
        query = query.join(
            Customer,
            Product.seller_id == Customer.id
        ).filter(
            Customer.campus == campus
        )

    # Filter by category
    if category:
        query = query.filter(
            Product.category == category
        )

    # Newest products first
    items = query.order_by(
        Product.date_added.desc()
    ).all()

    # Wishlist
    wishlisted_ids = set()

    if current_user.is_authenticated:
        wishlisted_ids = {
            w.product_id
            for w in Wishlist.query.filter_by(
                customer_id=current_user.id
            ).all()
        }

    return render_template(
        'home.html',
        items=items,
        wishlisted_ids=wishlisted_ids,
        selected_campus=campus,
        selected_category=category
    )


@views.route('/product/<int:product_id>')
def product_detail(product_id):
    product = db.session.get(Product, product_id)

    if not product:
        flash('Product not found.')
        return redirect(url_for('views.home'))

    return render_template('product_detail.html', product=product)


@views.route('/toggle-wishlist/<int:product_id>')
@login_required
def toggle_wishlist(product_id):
    from .models import Wishlist

    existing = Wishlist.query.filter_by(customer_id=current_user.id, product_id=product_id).first()

    if existing:
        db.session.delete(existing)
        db.session.commit()
        flash('Removed from wishlist')
    else:
        new_item = Wishlist(customer_id=current_user.id, product_id=product_id)
        db.session.add(new_item)
        db.session.commit()
        flash('Added to wishlist')

    return redirect(request.referrer or url_for('views.home'))

@views.route('/chat/<int:product_id>')
@login_required
def start_chat(product_id):
    product = db.session.get(Product, product_id)

    if not product:
        flash('Product not found')
        return redirect(url_for('views.home'))

    # You cannot chat with yourself
    if product.seller_id == current_user.id:
        flash('You cannot start a chat with yourself.')
        return redirect(
            url_for('views.product_detail', product_id=product.id)
        )

    # Check whether a conversation already exists
    conversation = Conversation.query.filter(
        Conversation.product_id == product.id,
        Conversation.buyer_id == current_user.id,
        Conversation.seller_id == product.seller_id
    ).first()

    # Create one if it doesn't exist
    if not conversation:
        conversation = Conversation(
            buyer_id=current_user.id,
            seller_id=product.seller_id,
            product_id=product.id
        )

        db.session.add(conversation)
        db.session.commit()

    return redirect(
        url_for(
            'views.chat',
            conversation_id=conversation.id
        )
    )


@views.route('/chat/<int:conversation_id>/messages', methods=['GET', 'POST'])
@login_required
def chat(conversation_id):

    conversation = db.session.get(Conversation, conversation_id)

    if not conversation:
        flash('Conversation not found')
        return redirect(url_for('views.home'))

    # Only the buyer or seller can access this conversation
    if current_user.id not in [
        conversation.buyer_id,
        conversation.seller_id
    ]:
        return render_template('404.html')


    # Mark messages from the other person as read
    Message.query.filter(
        Message.conversation_id == conversation.id,
        Message.sender_id != current_user.id,
        Message.is_read == False
    ).update(
        {'is_read': True},
        synchronize_session=False
    )

    db.session.commit()

    if request.method == 'POST':

        message_text = request.form.get('message', '').strip()

        if message_text:
            new_message = Message(
                conversation_id=conversation.id,
                sender_id=current_user.id,
                message=message_text,
                is_read=False
            )

            db.session.add(new_message)
            db.session.commit()

    messages = Message.query.filter_by(
        conversation_id=conversation.id
    ).order_by(Message.date_sent.asc()).all()

    return render_template(
        'chat.html',
        conversation=conversation,
        messages=messages
    )

@views.route('/messages')
@login_required
def messages():
    conversations = Conversation.query.filter(
        (Conversation.buyer_id == current_user.id) |
        (Conversation.seller_id == current_user.id)
    ).order_by(Conversation.date_created.desc()).all()

    unread_count = Message.query.filter(
        Message.sender_id != current_user.id,
        Message.is_read == False,
        Message.conversation_id.in_(
            db.session.query(Conversation.id).filter(
                (Conversation.buyer_id == current_user.id) |
                (Conversation.seller_id == current_user.id)
            )
        )
    ).count()

    return render_template(
        'messages.html',
        conversations=conversations,
        unread_count=unread_count
    )


@views.route('/media/<path:filename>')
def get_image(filename):
    from flask import send_from_directory
    return send_from_directory('../media', filename)


@views.route('/add-to-cart/<int:item_id>')
@login_required
def add_to_cart(item_id):

    item_to_add = db.session.get(Product, item_id)

    if not item_to_add:
        flash('Product not found.', 'danger')
        return redirect(request.referrer or url_for('views.home'))

    if item_to_add.in_stock <= 0:
        flash('Sorry, this product is currently out of stock')
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

    cart = Cart.query.filter_by(
        customer_id=current_user.id
    ).all()

    amount = sum(
        item.product.current_price * item.quantity
        for item in cart
        if item.product
    )

    seller_campuses = {
        item.product.seller.campus
        for item in cart
        if item.product and item.product.seller
    }

    shipping_total = sum(
        shipping_fee(
            current_user.campus,
            campus
        )['fee']
        for campus in seller_campuses
    )

    return render_template(
        'cart.html',
        cart=cart,
        amount=amount,
        shipping=shipping_total,
        total=amount + shipping_total
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

    total_items = sum(
        item.product.current_price * item.quantity
        for item in cart
        if item.product
    )

    seller_campuses = {
        item.product.seller.campus
        for item in cart
        if item.product and item.product.seller
    }

    shipping_total = sum(
        shipping_fee(
            current_user.campus,
            campus
        )['fee']
        for campus in seller_campuses
    )

    return render_template(
        'checkout.html',
        cart=cart,
        shipping=shipping_total,
        total=total_items + shipping_total
    )

@views.route('/place-order', methods=['POST'])
@login_required
def place_order():
    cart = Cart.query.filter_by(
        customer_id=current_user.id
    ).all()
    if not cart:
        flash('Your cart is empty')
        return redirect(url_for('views.home'))
    try:
        # Check stock before creating the order
        for item in cart:
            if item.quantity > item.product.in_stock:
                flash(
                    f'Only {item.product.in_stock} '
                    f'"{item.product.product_name}" left in stock.'
                )
                return redirect(url_for('views.show_cart'))
        # Get the unique campuses of sellers in the cart
        seller_campuses = {
            item.product.seller.campus
            for item in cart
            if item.product and item.product.seller
        }
        # Calculate shipping based on buyer's campus
        shipping_total = sum(
            shipping_fee(
                current_user.campus,
                campus
            )['fee']
            for campus in seller_campuses
        )
        # Create the order
        new_order = Order(
            customer_id=current_user.id,
            status='Pending Payment',
            shipping_fee=shipping_total
        )
        db.session.add(new_order)
        db.session.flush()
        # Move cart items into the order
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
            order.payment_status = 'Paid'

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