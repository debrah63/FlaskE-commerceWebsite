from flask import Blueprint, render_template, flash, redirect, url_for
from itsdangerous import URLSafeTimedSerializer
from flask_mail import Message
from .forms import LoginForm, SignUpForm, ForgotPasswordForm, ResetPasswordForm
from .models import Customer
from . import db, mail
from flask_login import login_user, login_required, logout_user
import os

auth = Blueprint('auth', __name__)


def get_serializer():
    return URLSafeTimedSerializer(os.environ.get('SECRET_KEY'))


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
            flash('Account Not Created!! An account with this Email already exists')

    for field, errors in  form.errors.items():
        for error in errors:
            if field == 'username':
                flash('Username must be at least 5 characters long.')
            elif field == 'email':
                flash('Enter a valid email address.')
            else:
                flash(f'{field.capitalize()}: {error}.')

    return render_template('signup.html', form=form)


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
            flash('Account does not exist, please Sign Up')
    return render_template('login.html', form=form)


@auth.route('/logout')
@login_required
def log_out():
    logout_user()
    return redirect('/')


@auth.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    form = ForgotPasswordForm()

    if form.validate_on_submit():
        email = form.email.data
        customer = Customer.query.filter_by(email=email).first()

        if customer:
            serializer = get_serializer()
            token = serializer.dumps(email, salt='password-reset')

            customer.reset_token = token
            db.session.commit()

            reset_url = url_for('auth.reset_password', token=token, _external=True)

            msg = Message('Password Reset Request',
                          recipients=[email]
                          )
            msg.body = f'Click this link to reset your password: {reset_url}\nThis link expires in 30 minutes.'



            mail.send(msg)

        flash('If that email exists, a reset link has been sent.')
        return redirect('/login')

    return render_template('forgot_password.html', form=form)


@auth.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):



    serializer = get_serializer()

    try:

        email = serializer.loads(token, salt='password-reset', max_age=1800)



        customer = Customer.query.filter_by(email=email).first()



        if not customer or customer.reset_token != token:

            flash('This reset link is invalid or has already been used.')
            return redirect('/forgot-password')

    except Exception as e:
        flash('This reset link is invalid or has expired.')
        return redirect('/forgot-password')


    form = ResetPasswordForm()

    if form.validate_on_submit():
        customer = Customer.query.filter_by(email=email).first()
        customer.password = form.password2.data
        db.session.commit()
        flash('Your password has been reset. You can now log in.')
        return redirect('/login')

    return render_template('reset_password.html', form=form)