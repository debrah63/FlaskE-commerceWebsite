from datetime import datetime
from flask import Blueprint, render_template, flash, redirect, url_for, request
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
from .forms import ProductForm,FlashSaleForm
from .models import Product
from . import db

seller = Blueprint('seller', __name__)


def seller_required():
    return current_user.role == 'seller' and current_user.is_approved

def is_flash_sale_active(product):
    """Return True if the product has an active Flash Sale."""

    if not product.flash_sale:
        return False

    if not product.flash_sale_price:
        return False

    if not product.flash_sale_ends_at:
        return False

    # SQLite may return a naive datetime, even when UTC was originally used.
    now = datetime.now()

    sale_end = product.flash_sale_ends_at

    # Compare naive datetimes consistently.
    if sale_end.tzinfo is not None:
        sale_end = sale_end.replace(tzinfo=None)

    return sale_end > now


@seller.route('/add-product', methods=['GET', 'POST'])
@login_required
def add_product():
    if not seller_required():
        return render_template('404.html')

    form = ProductForm()

    # DEBUG: Check the request and form validation
    print("DEBUG: Request method:", request.method)

    is_valid = form.validate_on_submit()

    print("DEBUG: Validation result:", is_valid)

    if request.method == "POST":
        print("DEBUG: Form errors:", form.errors)

    if is_valid:
        print("DEBUG: Product form validation passed.")

        file = form.product_picture.data
        file_name = secure_filename(file.filename)

        # Save the uploaded product picture
        upload_path = os.path.join('media', file_name)
        file.save(upload_path)

        # Create the product
        new_product = Product()

        new_product.product_name = form.product_name.data
        new_product.description = form.description.data
        new_product.category = form.category.data
        new_product.product_type = form.product_type.data
        new_product.brand = form.brand.data
        new_product.condition = form.condition.data
        new_product.current_price = form.current_price.data
        new_product.previous_price = form.previous_price.data
        new_product.in_stock = form.in_stock.data

        # Flash Sale settings
        new_product.flash_sale = form.flash_sale.data

        if form.flash_sale.data:
            flash_sale_price = form.flash_sale_price.data
            flash_sale_end_at = form.flash_sale_end_at.data

            # Validate Flash Sale price
            if flash_sale_price is None:
                flash(
                    'Please enter a Flash Sale price.',
                    'danger'
                )
                return render_template(
                    'add_product.html',
                    form=form
                )

            if flash_sale_price >= new_product.current_price:
                flash(
                    'The Flash Sale price must be lower than the regular price.',
                    'danger'
                )
                return render_template(
                    'add_product.html',
                    form=form
                )

            # Validate Flash Sale end time
            if flash_sale_end_at is None:
                flash(
                    'Please select a Flash Sale end time.',
                    'danger'
                )
                return render_template(
                    'add_product.html',
                    form=form
                )

            if flash_sale_end_at <= datetime.now():
                flash(
                    'The Flash Sale end time must be in the future.',
                    'danger'
                )
                return render_template(
                    'add_product.html',
                    form=form
                )

            # Save Flash Sale details
            new_product.flash_sale_price = flash_sale_price
            new_product.flash_sale_ends_at = flash_sale_end_at
            new_product.flash_sale_stock = form.flash_sale_stock.data
            new_product.flash_sale_sold = 0

        else:
            # Clear Flash Sale details if no sale is selected
            new_product.flash_sale = False
            new_product.flash_sale_price = None
            new_product.flash_sale_ends_at = None
            new_product.flash_sale_stock = None
            new_product.flash_sale_sold = 0

        # Save remaining product details
        new_product.product_picture = file_name
        new_product.seller_id = current_user.id

        try:
            db.session.add(new_product)
            db.session.commit()

            print("DEBUG: Product saved successfully.")

            flash(
                f'{new_product.product_name} added successfully.',
                'success'
            )

            return redirect(url_for('seller.my_products'))

        except Exception as e:
            db.session.rollback()

            print("DEBUG: Database error:", repr(e))

            flash(
                'Product could not be added. Please try again.',
                'danger'
            )

    else:
        # This belongs to the outer if, not the Flash Sale if.
        print("DEBUG: Product form validation failed.")

    return render_template('add_product.html', form=form)

@seller.route('/my-products')
@login_required
def my_products():
    if not seller_required():
        return render_template('404.html'), 404

    products = (
        Product.query
        .filter_by(seller_id=current_user.id)
        .order_by(Product.date_added.desc())
        .all()
    )

    now = datetime.now()

    return render_template(
        'my_products.html',
        products=products,
        now=now
    )


@seller.route(
    '/product/<int:product_id>/flash-sale',
    methods=['GET', 'POST']
)
@login_required
def manage_flash_sale(product_id):
    if not seller_required():
        return render_template('404.html'), 404

    product = db.session.get(Product, product_id)

    if not product or product.seller_id != current_user.id:
        flash('Product not found.', 'danger')
        return redirect(url_for('seller.my_products'))

    form = FlashSaleForm()

    if form.validate_on_submit():

        sale_price = form.flash_sale_price.data
        sale_end_at = form.flash_sale_end_at.data
        sale_stock = form.flash_sale_stock.data

        if sale_price >= product.current_price:
            form.flash_sale_price.errors.append(
                'The Flash Sale price must be lower than the regular price.'
            )

        elif sale_end_at <= datetime.now():
            form.flash_sale_end_at.errors.append(
                'The end time must be in the future.'
            )

        elif sale_stock is not None and sale_stock > product.in_stock:
            form.flash_sale_stock.errors.append(
                'The Flash Sale stock limit cannot exceed available stock.'
            )

        else:
            product.flash_sale = True
            product.flash_sale_price = sale_price
            product.flash_sale_ends_at = sale_end_at
            product.flash_sale_stock = sale_stock
            product.flash_sale_sold = 0

            try:
                db.session.commit()

                flash(
                    f'Flash Sale activated for {product.product_name}.',
                    'success'
                )

                return redirect(url_for('seller.my_products'))

            except Exception as e:
                db.session.rollback()
                print(e)

                flash('Could not save the Flash Sale.', 'danger')

    elif request.method == 'GET':
        # Populate the form with the existing promotion when available.
        form.flash_sale_price.data = product.flash_sale_price
        form.flash_sale_end_at.data = product.flash_sale_ends_at
        form.flash_sale_stock.data = product.flash_sale_stock

    return render_template(
        'manage_flash_sale.html',
        product=product,
        form=form
    )


@seller.route('/edit-product/<int:product_id>', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    if not seller_required():
        return render_template('404.html')

    product = db.session.get(Product, product_id)

    if not product or product.seller_id != current_user.id:
        flash('Product not found')
        return redirect(url_for('seller.my_products'))

    form = ProductForm(obj=product)

    if form.validate_on_submit():
        product.product_name = form.product_name.data
        product.description = form.description.data
        product.category = form.category.data
        product.current_price = form.current_price.data
        product.previous_price = form.previous_price.data
        product.in_stock = form.in_stock.data
        product.flash_sale = form.flash_sale.data

        if form.product_picture.data:
            file = form.product_picture.data
            file_name = secure_filename(file.filename)
            file.save(f'./media/{file_name}')
            product.product_picture = file_name

        try:
            db.session.commit()
            flash(f'{product.product_name} updated successfully')
            return redirect(url_for('seller.my_products'))
        except Exception as e:
            db.session.rollback()
            print(e)
            flash('Product could not be updated')

    return render_template('edit_product.html', form=form, product=product)


@seller.route('/delete-product/<int:product_id>', methods=['POST'])
@login_required
def delete_product(product_id):
    if not seller_required():
        return render_template('404.html')

    product = db.session.get(Product, product_id)

    if not product or product.seller_id != current_user.id:
        flash('Product not found')
        return redirect(url_for('seller.my_products'))

    from .models import Cart
    Cart.query.filter_by(product_id=product_id).delete()

    db.session.delete(product)
    db.session.commit()
    flash(f'{product.product_name} deleted')
    return redirect(url_for('seller.my_products'))