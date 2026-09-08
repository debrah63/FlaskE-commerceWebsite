from flask import Blueprint, render_template, flash, redirect, url_for, current_app
from itsdangerous import URLSafeTimedSerializer
from flask_mail import Message
from .forms import LoginForm, SignUpForm, ForgotPasswordForm, ResetPasswordForm, ChangePasswordForm
from .models import Customer
from . import db, mail
from flask_login import login_user, login_required, logout_user, current_user
import os

auth = Blueprint('auth', __name__)


def get_serializer():
    return URLSafeTimedSerializer(os.environ.get('SECRET_KEY'))


@auth.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    form = SignUpForm()

    if form.validate_on_submit():
        role = form.role.data
        email = form.email.data.strip().lower()
        username = form.username.data.strip()

        new_customer = Customer()
        new_customer.email = email
        new_customer.username = username
        new_customer.role = role
        new_customer.password = form.password2.data
        new_customer.is_approved = (role != 'seller')

        try:
            db.session.add(new_customer)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(e)
            flash('Account Not Created!! An account with this email already exists.', 'danger')
            return render_template('signup.html', form=form)

        try:
            serializer = get_serializer()
            token = serializer.dumps(email, salt='email-verification')
            verify_url = url_for('auth.verify_email', token=token, _external=True)

            msg = Message('Verify Your Email', sender=os.environ.get('MAIL_USERNAME'), recipients=[email])
            msg.body = (
                f'Welcome!\n\n'
                f'Click the link below to verify your email:\n\n'
                f'{verify_url}\n\n'
                f'This link expires in 30 minutes.'
            )
            mail.send(msg)
        except Exception as e:
            print(e)
            flash('Account created, but we could not send a verification email right now. You can request a new one from your profile.', 'warning')
            return redirect(url_for('auth.login'))

        if role == 'seller':
            flash('Account created! Your seller account is pending admin approval.', 'info')
        else:
            flash('Account Created Successfully. You can now Log In.', 'success')

        return redirect(url_for('auth.login'))

    return render_template('signup.html', form=form)

@auth.route('/verify-email/<token>')
def verify_email(token):
    serializer = get_serializer()

    try:
        email = serializer.loads(token, salt='email-verification', max_age=1800)
    except Exception:
        flash('This verification link is invalid or has expired.', 'danger')
        return redirect(url_for('auth.login'))

    customer = Customer.query.filter_by(email=email).first()

    if not customer:
        flash('Account not found.', 'danger')
        return redirect(url_for('auth.login'))

    if customer.is_verified:
        flash('Your email is already verified. You can log in.', 'info')
        return redirect(url_for('auth.login'))

    customer.is_verified = True
    db.session.commit()

    flash('Email verified successfully! You can now log in.', 'success')
    return redirect(url_for('auth.login'))

@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        customer = Customer.query.filter_by(email=form.email.data).first()

        if customer:
            if customer.verify_password(password=form.password.data):

                if (current_app.config['REQUIRE_EMAIL_VERIFICATION'] and not customer.is_verified):
                    flash('Please verify your email before logging in.', 'warning')

                    return redirect(url_for('auth.resend_verification', email=customer.email))

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

    flash('You have been logged out.','info')

    return redirect(url_for('views.home'))


@auth.route('/resend-verification/<email>')
def resend_verification(email):
    customer = Customer.query.filter_by(email=email).first()

    if not customer:
        flash('Account not found.', 'danger')
        return redirect(url_for('auth.login'))

    if customer.is_verified:
        flash('This account is already verified.', 'info')
        return redirect(url_for('auth.login'))

    try:
        serializer = get_serializer()
        token = serializer.dumps(email, salt='email-verification')
        verify_url = url_for('auth.verify_email', token=token, _external=True)

        msg = Message('Verify Your Email', sender=os.environ.get('MAIL_USERNAME'), recipients=[email])
        msg.body = f'Click the link below to verify your email:\n\n{verify_url}\n\nThis link expires in 30 minutes.'
        mail.send(msg)

        flash('Verification email sent. Please check your inbox.', 'success')
        return render_template( url_for('auth.login'))

    except Exception as e:
        print(e)
        flash('Could not send verification email right now. Please try again later.', 'danger')

    return render_template('resend_verification.html', email=email)


@auth.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():

    form = ForgotPasswordForm()

    if form.validate_on_submit():

        email = form.email.data.strip().lower()

        customer = Customer.query.filter_by(email=email).first()

        if customer:

            serializer = get_serializer()

            token = serializer.dumps(email,salt='password-reset')

            reset_url = url_for('auth.reset_password',token=token,_external=True)

            msg = Message('Password Reset Request',sender=os.environ.get('MAIL_USERNAME'),recipients=[email])

            msg.body = (f'Click this link to reset your password:\n\n'
                f'{reset_url}\n\n'
                f'This link expires in 30 minutes.')

            mail.send(msg)

        flash('If that email exists, a reset link has been sent.','info')

        return redirect(url_for('auth.login'))

    return render_template('forgot_password.html',form=form)


@auth.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):

    serializer = get_serializer()

    try:

        email = serializer.loads(token,salt='password-reset',max_age=1800)

    except Exception:

        flash('This reset link is invalid or has expired.','danger')

        return redirect(url_for('auth.forgot_password'))

    form = ResetPasswordForm()

    if form.validate_on_submit():

        customer = Customer.query.filter_by(email=email).first()

        if not customer:

            flash('User not found.','danger')

            return redirect(url_for('auth.login'))

        customer.password = form.password2.data
        customer.reset_token = None
        customer.reset_token_expiry = None

        db.session.commit()

        flash('Your password has been reset successfully. You can now log in.','success')

        return redirect(url_for('auth.login'))

    return render_template('reset_password.html',form=form)


@auth.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():

    form = ChangePasswordForm()

    if form.validate_on_submit():

        if not current_user.verify_password(form.current_password.data):
            flash('Your current password is incorrect.')
            return render_template('change_password.html',form=form)

        current_user.password = form.new_password.data

        db.session.commit()

        flash('Your password has been changed successfully.')

        return redirect(url_for('auth.profile',customer_id=current_user.id))

    return render_template('change_password.html',form=form)

@auth.route('/profile/<int:customer_id>')
@login_required
def profile(customer_id):
    if customer_id != current_user.id:
        return render_template('404.html')

    from .models import Product, Order

    listings_count = Product.query.filter_by(seller_id=current_user.id).count()
    bought_count = Order.query.filter_by(customer_id=current_user.id).count()

    return render_template('profile.html', customer=current_user, listings_count=listings_count, bought_count=bought_count)

