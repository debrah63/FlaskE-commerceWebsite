from flask import Blueprint, render_template, flash, redirect
from flask_login import login_required, current_user
from .models import Customer, Product, Order
from .import db

admin = Blueprint('admin', __name__)

def admin_required():
    return current_user.is_authenticated and current_user.role == 'admin'


@admin.route('/pending-sellers')
@login_required
def pending_sellers():
    if current_user.role != 'admin':

        return render_template('404.html')

    sellers = Customer.query.filter_by(role='seller', is_approved=False).all()

    return render_template('pending_sellers.html', sellers=sellers)


@admin.route('/approved-sellers')
@login_required
def approved_sellers():
    if current_user.role != 'admin':
        return render_template('404.html')
    sellers = Customer.query.filter_by(role='seller', is_approved=True).all()
    return render_template('approved_sellers.html', sellers=sellers)


@admin.route('/approve-seller/<int:seller_id>')
@login_required
def approve_seller(seller_id):
    if current_user.role != 'admin':

        return  render_template('404.html')

    seller = Customer.query.get(seller_id)

    if seller and seller.role == 'seller':
        seller.is_approved = True
        db.session.commit()

        flash(f'{seller.username} has been approved as a seller.', 'success')

    else:

        flash('Seller not found.', 'danger')

    return redirect('/pending-sellers')


@admin.route('/reject-seller/<int:seller_id>')
@login_required
def reject_seller(seller_id):
    if current_user.role != 'admin':

        flash('Access denied!!')

        return render_template('404.html')

    seller = Customer.query.get(seller_id)

    if seller and seller.role == 'seller':
        db.session.delete(seller)
        db.session.commit()

        flash(f'{seller.username}\'s seller application has been rejected.', 'warning')

    return redirect('/pending-sellers')

@admin.route('/admin-dashboard')
@login_required
def admin_dashboard():

    if current_user.role != 'admin':
        return render_template('404.html')

    total_users = Customer.query.count()

    total_listings = Product.query.count()

    total_orders = Order.query.count()

    pending_sellers = Customer.query.filter_by(
        role='seller',
        is_approved=False
    ).count()

    verification_requests = Customer.query.filter_by(
        verification_status='pending'
    ).count()

    approved_sellers = Customer.query.filter_by(
        role='seller',
        is_approved=True
    ).count()

    return render_template(
        'admin_dashboard.html',
        total_users=total_users,
        total_listings=total_listings,
        total_orders=total_orders,
        pending_sellers=pending_sellers,
        verification_requests=verification_requests,
        approved_sellers=approved_sellers
    )
@admin.route('/pending-verifications')
@login_required
def pending_verifications():
    if not admin_required():
        return render_template('404.html')

    customers = Customer.query.filter_by(
        verification_status='pending'
    ).all()

    return render_template(
        'pending_verifications.html',
        customers=customers
    )

@admin.route('/approve-verification/<int:customer_id>')
@login_required
def approve_verification(customer_id):
    if not admin_required():
        return render_template('404.html')

    customer = db.session.get(Customer, customer_id)

    if customer:
        customer.verification_status = 'verified'
        db.session.commit()
        flash(f'{customer.username} is now Vouch Verified.')

    return redirect('/pending-verifications')


@admin.route('/reject-verification/<int:customer_id>')
@login_required
def reject_verification(customer_id):
    if not admin_required():
        return render_template('404.html')

    customer = db.session.get(Customer, customer_id)

    if customer:
        customer.verification_status = 'rejected'
        db.session.commit()
        flash(f'{customer.username} verification request was rejected.')

    return redirect('/pending-verifications')