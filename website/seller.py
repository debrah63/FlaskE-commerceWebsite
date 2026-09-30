from flask import Blueprint, render_template, flash, redirect, url_for
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
from .forms import ProductForm
from .models import Product
from . import db

seller = Blueprint('seller', __name__)


def seller_required():
    return current_user.role == 'seller' and current_user.is_approved


@seller.route('/add-product', methods=['GET', 'POST'])
@login_required
def add_product():
    if not seller_required():
        return render_template('404.html')

    form = ProductForm()

    if form.validate_on_submit():
        file = form.product_picture.data
        file_name = secure_filename(file.filename)

        #file_path = file_name
        #file.save(f'./media/{file_name}')

        upload_path = os.path.join('media', file_name)
        file.save(upload_path)

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

        new_product.flash_sale = form.flash_sale.data

        new_product.product_picture = file_name

        new_product.seller_id = current_user.id

        try:
            db.session.add(new_product)
            db.session.commit()

            flash(f'{new_product.product_name} added successfully.', 'success')

            return redirect('seller.my-products')

        except Exception as e:

            db.session.rollback()
            print(e)

            flash('Product could not be added.','danger')

    return render_template('add_product.html', form=form)


@seller.route('/my-products')
@login_required
def my_products():
    if not seller_required():
        return render_template('404.html')

    products = Product.query.filter_by(seller_id=current_user.id).order_by(Product.date_added.desc()).all()

    return render_template('my_products.html', products=products)

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