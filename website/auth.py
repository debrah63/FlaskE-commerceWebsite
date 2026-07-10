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
        role = form.role.data
        password2 = form.password2.data

        new_customer = Customer()
        new_customer.email = email
        new_customer.username = username
        new_customer.role = role
        new_customer.password = password2

        if role == 'seller':
            new_customer.is_approved = False
        else:
            new_customer.is_approved = True

        try:
            db.session.add(new_customer)
            db.session.commit()

            if role == 'seller':
                flash('Account Created! Your seller account is pending admin approval before you can list products.')
            else:
                flash('Account Created Successfully, You can now Log In')

            return redirect('/login')
        except Exception as e:
            print(e)
            flash('Account Not Created!! An account with this Email already exits')

    return render_template('signup.html',  form=form)


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
                return redirect('/')
            else:
                flash('Incorrect Email or Password')
        else:
            flash('Account does not exits, please Sign Up')
    return render_template('login.html', form=form)


@auth.route('/logout')
@login_required
def log_out():
    logout_user()
    return redirect('/')
