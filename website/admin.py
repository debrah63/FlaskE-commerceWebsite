from flask import Blueprint, render_template, flash, redirect
from flask_login import login_required, current_user
from .models import Customer
from .import db

admin = Blueprint('admin', __name__)


@admin.route('/pending-sellers')
@login_required
def pending_sellers():
    if current_user.role != 'admin':
        return render_template('404.html')

    sellers = Customer.query.filter_by(role='seller', is_approved=False).all()
    return render_template('pending_sellers.html', sellers=sellers)

@admin.route('/approve-seller/<int:seller_id>')
@login_required
def approve_seller(seller_id):
    if current_user.role != 'admin':
        render_template('404.html')

    seller = Customer.query.get(seller_id)

    if seller and seller.role == 'seller':
        seller.is_approved = True
        db.session.commit()
        flash(f'{seller.username} has been approved as a seller')

    return redirect('/pending-sellers')


@admin.route('/reject-seller/<int:seller_id>')
@login_required
def reject_seller(seller_id):
    if current_user.role != 'admin':
        flash('Access denied!!')
        render_template('404.html')

    seller = Customer.query.get(seller_id)

    if seller and seller.role == 'seller':
        db.session.delete(seller)
        db.session.commit()
        flash(f'{seller.username}\'s seller application has been rejected')

    return redirect('/pending-sellers')

@admin.route('/admin-dashboard')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        return render_template('404.html')
    return render_template('admin_dashboard.html')