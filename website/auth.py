from  flask import Blueprint, render_template, flash,  redirect
from .forms import LoginForm, SignUpForm
from .models import Customer
from . import db
from flask_login import login_user, login_required, logout_user

auth = Blueprint('auth', __name__)

@auth.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    form = SignUpForm()

    if form.validate_on_submit():
        email = form.email.data
        username = form.username.data
        password2 = form.password2.data

        new_customer = Customer()
        new_customer.email = email
        new_customer.username = username
        new_customer.password = password2

        try:
            db.session.add(new_customer)
            db.session.commit()
            flash('Account Created Successfully, You are now to log in')
            return redirect('/login')
        except Exeception as e:
            print(e)
            flash('Account Not Created!! An account with this email already exits')

    return render_template('sigup.html',  form=form)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data

        customer = Customer.query.filter_by(email=email).first()

        if customer:
            if customer.verify_password(password=password):
                login_user(customer, remember=True)
            else:
                flash('Incorrect Email or Password')
        else:
            flash('Account doesnot exits, please Sign Up')
    return render_template('login.html', form=form)


@auth.route('/logout')
@login_required
def log_out():
    logout_user()
    return redirect('/')
