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

            serializer = get_serializer()

            token = serializer.dumps(
                email,
                salt='email-verification'
            )

            verify_url = url_for(
                'auth.verify_email',
                token=token,
                _external=True
            )

            msg = Message(
                'Verify Your Email',
                sender=os.environ.get('MAIL_USERNAME'),
                recipients=[email]
            )

            msg.body = (
                f'Welcome!\n\n'
                f'Click the link below to verify your email:\n\n'
                f'{verify_url}\n\n'
                f'This link expires in 30 minutes.'
            )

            mail.send(msg)


            if role == 'seller':
                flash(
                    'Account created! Your seller account is pending admin approval.',
                    'info'
                )
            else:
                flash(
                    'Account Created Successfully. You can now Log In.',
                    'success'
                )

            return redirect(url_for('auth.login'))

        except Exception as e:

            db.session.rollback()

            print(e)

            flash(
                'Account Not Created!! An account with this email already exists.',
                'danger'
            )

    return render_template(
        'signup.html',
        form=form
    )

@auth.route('/verify-email/<token>')
def verify_email(token):

    serializer = get_serializer()

    try:
        email = serializer.loads(
            token,
            salt='email-verification',
            max_age=1800
        )

    except Exception:

        flash(
            'Verification link is invalid or has expired.',
            'danger'
        )

        return redirect(url_for('auth.login'))

    customer = Customer.query.filter_by(
        email=email
    ).first()

    if not customer:

        flash(
            'Account not found.',
            'danger'
        )

        return redirect(url_for('auth.sign_up'))

    if customer.email_verified:

        flash(
            'Your email has already been verified.',
            'info'
        )

        return redirect(url_for('auth.login'))

    customer.email_verified = True

    db.session.commit()

    flash(
        'Email verified successfully! You can now log in.',
        'success'
    )

    return redirect(url_for('auth.login'))


@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():

        email = form.email.data.strip().lower()

        customer = Customer.query.filter_by(
            email=email
        ).first()

        if customer:

            if customer.verify_password(
                    password=form.password.data
            ):


                if not customer.email_verified:

                    flash(
                        'Please verify your email before logging in.',
                        'warning'
                    )

                    return render_template(
                        'login.html',
                        form=form
                    )

                if (
                        customer.role == 'seller'
                        and
                        not customer.is_approved
                ):
                    flash(
                        'Your seller account is still waiting for admin approval.',
                        'warning'
                    )

                    return render_template(
                        'login.html',
                        form=form
                    )

                login_user(
                    customer,
                    remember=True
                )

                flash(
                    f'Welcome back, {customer.username}!',
                    'success'
                )

                return redirect(
                    url_for('views.home')
                )

            else:

                flash(
                    'Incorrect Email or Password.',
                    'danger'
                )

        else:

            flash(
                'Account does not exist. Please Sign Up.',
                'warning'
            )

    return render_template(
        'login.html',
        form=form
    )

@auth.route('/logout')
@login_required
def log_out():

    logout_user()

    flash(
        'You have been logged out.',
        'info'
    )

    return redirect(
        url_for('views.home')
    )


@auth.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():

    form = ForgotPasswordForm()

    if form.validate_on_submit():

        email = form.email.data.strip().lower()

        customer = Customer.query.filter_by(
            email=email
        ).first()

        if customer:

            serializer = get_serializer()

            token = serializer.dumps(
                email,
                salt='password-reset'
            )

            reset_url = url_for(
                'auth.reset_password',
                token=token,
                _external=True
            )

            msg = Message(
                'Password Reset Request',
                sender=os.environ.get('MAIL_USERNAME'),
                recipients=[email]
            )

            msg.body = (
                f'Click this link to reset your password:\n\n'
                f'{reset_url}\n\n'
                f'This link expires in 30 minutes.'
            )

            mail.send(msg)

        flash(
            'If that email exists, a reset link has been sent.',
            'info'
        )

        return redirect(
            url_for('auth.login')
        )

    return render_template(
        'forgot_password.html',
        form=form
    )


@auth.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):

    serializer = get_serializer()

    try:

        email = serializer.loads(
            token,
            salt='password-reset',
            max_age=1800
        )

    except Exception:

        flash(
            'This reset link is invalid or has expired.',
            'danger'
        )

        return redirect(
            url_for('auth.forgot_password')
        )

    form = ResetPasswordForm()

    if form.validate_on_submit():

        customer = Customer.query.filter_by(
            email=email
        ).first()

        if not customer:

            flash(
                'User not found.',
                'danger'
            )

            return redirect(
                url_for('auth.login')
            )

        customer.password = form.password2.data
        customer.reset_token = None
        customer.reset_token_expiry = None

        db.session.commit()

        flash(
            'Your password has been reset successfully. You can now log in.',
            'success'
        )

        return redirect(
            url_for('auth.login')
        )

    return render_template(
        'reset_password.html',
        form=form
    )