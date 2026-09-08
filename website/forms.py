from flask_wtf import FlaskForm
from wtforms import (StringField, PasswordField, EmailField, SubmitField, RadioField, TextAreaField,BooleanField,FloatField, IntegerField)
from wtforms.validators import DataRequired, length, EqualTo,NumberRange
from flask_wtf. file import FileField, FileRequired, FileAllowed





class ProductForm(FlaskForm):
    product_name = StringField('Product Name', validators=[DataRequired(), length(min=5, max=100)])
    description = TextAreaField('Description', validators=[DataRequired(), length(min=10, max=1000)])
    category = StringField('Category', validators=[DataRequired(), length(min=5, max=100)])
    current_price = FloatField('Current Price', validators=[DataRequired(), NumberRange(min=0.01)])
    previous_price = FloatField('Previous Price', validators=[DataRequired(), NumberRange(min=0)])
    in_stock = IntegerField('In stock', validators=[DataRequired(), NumberRange(min=0)])
    product_picture = FileField('Product Picture', validators=[FileRequired(message='A product picture is required'),FileAllowed(['jpg', 'jpeg', 'png'], message='Images only (jpg, jpeg, png)')])
    flash_sale = BooleanField('Flash Sale')
    submit =SubmitField('Add Product')


class SignUpForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired()])
    username = StringField('Username', validators=[DataRequired(), length(min=5, max=30)])
    role = RadioField('I want to', choices=[('buyer', 'Buy product'), ('seller', 'Sell product')], default='buyer', validators=[DataRequired()])
    password1 = PasswordField('Enter Your Password', validators=[DataRequired(), length(min=8)])
    password2 = PasswordField('Confirm Your Password', validators=[DataRequired(), length(min=8), EqualTo( 'password1', message= 'Passwords must match')])
    submit = SubmitField('Sign Up')

class LoginForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired()])
    password = PasswordField('Enter Your Password', validators=[DataRequired()])
    submit = SubmitField('Log  In')

class ForgotPasswordForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired()])
    submit = SubmitField('Send Reset Link')


class ResetPasswordForm(FlaskForm):
    password1 = PasswordField('New Password', validators=[DataRequired(), length(min=8)])
    password2 = PasswordField('Confirm New Password', validators=[DataRequired(),length(min=8),EqualTo('password1', message='Passwords must match')])
    submit = SubmitField('Reset Password')


class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Current Password', validators=[DataRequired()])

    new_password = PasswordField('New Password', validators=[DataRequired(),length(min=6)])

    confirm_password = PasswordField('Confirm New Password',validators=[DataRequired(),length(min=6),EqualTo('new_password',message='Passwords must match')])

    submit = SubmitField('Change Password')