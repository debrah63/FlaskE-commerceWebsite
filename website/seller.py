from flask import Blueprint, render_template, flash,  redirect
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from .forms import ProductForm
from .models import Product
from . import db

seller = Blueprint('seller', __name__)

def seller_required():
    return current_user.role =='seller' and current_user.is_approved


@seller.route('/add-product', methods=['GET', 'POST'])
@login_required
def add_product():
    if not seller_required():
        return render_template('404.html')

    form = ProductForm()

    if form.validate_on_submit():
        file = form.product_picture.data
        file_name = secure_filename(file.filename)
        file_path = f'./media/{file_name}'
        file.save(file_path)


        new_product = Product()
        new_product.product_name = form.product_name.data
        new_product.current_price = form.current_price.data
        new_product.previous_price = form.previous_price.data
        new_product.in_stock = form.in_stock.data
        new_product.flash_sale = form.flash_sale.data
        new_product.product_picture = file_path
        new_product.seller_id = current_user.id

        try:
            db.session.add(new_product)
            db.session.commit()
            flash(f'{new_product.product_name} added successfully')
            return redirect('/my products')
        except Exception as e:
            print(e)
            flash('Product could not be added')

    return render_template('add_product.html', form=form)

@seller.route('/my-products')
@login_required
def my_products():
    if not seller_required():
        return render_template('404.html')

    products = Product.query.filter_by(seller_id=current_user.id).all()
    return render_template('my_product.html', products=products)