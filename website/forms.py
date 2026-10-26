from flask_wtf import FlaskForm
from wtforms import (StringField, PasswordField, EmailField, SubmitField, RadioField, TextAreaField, BooleanField, FloatField, IntegerField, SelectField, DateTimeLocalField)
from wtforms.validators import DataRequired, length, EqualTo, NumberRange, Optional
from flask_wtf. file import FileField, FileRequired, FileAllowed
from .campuses import CAMPUSES




class ProductForm(FlaskForm):
    product_name = StringField('Product Name', validators=[DataRequired(), length(min=5, max=100)])
    description = TextAreaField('Description', validators=[DataRequired(), length(min=10, max=1000)])
    category = SelectField('Category', choices=[('Electronics', 'Electronics'), ('Books', 'Books'), ('Fashion', 'Fashion'),('Hostel', 'Hostel'), ('Food', 'Food') ,('Personal care', 'Personal care'),('Phones', 'Phones'),('Accessories', 'Accessories'), ('Services', 'Services') ], validators=[DataRequired()])
    product_type = StringField('Product Type', validators=[DataRequired(), length(min=5, max=100)])
    brand = StringField('Brand', validators=[Optional(), length(max=100)])
    condition = SelectField('Condition', choices =[('New', 'New'), ('Like New','Like New'), ('Good','Good'),('Fair', 'Fair'),('Used','Used')], validators=[DataRequired()])

    current_price = FloatField('Current Price', validators=[DataRequired(), NumberRange(min=0.01)])
    previous_price = FloatField('Previous Price', validators=[Optional(), NumberRange(min=0)])
    in_stock = IntegerField('In stock', validators=[DataRequired(), NumberRange(min=0)])
    product_picture = FileField('Product Picture', validators=[FileRequired(message='A product picture is required'),FileAllowed(['jpg', 'jpeg', 'png'], message='Images only (jpg, jpeg, png)')])

    flash_sale = BooleanField('Flash Sale')
    flash_sale_price = FloatField('Flash Sale Price', validators=[Optional(), NumberRange(min=0.01)], render_kw={'step': '0.01', 'min': '0.01'})
    flash_sale_end_at = DateTimeLocalField('Flash Sale End Time', format='%Y-%m-%dT%H:%M', validators=[Optional()])
    flash_sale_stock = IntegerField('Flash Sale Stock Limit', validators=[Optional(), NumberRange(min=1)])

    submit =SubmitField('Add Product')



class FlashSaleForm(FlaskForm):
    flash_sale_price = FloatField(
        'Flash Sale Price (GH₵)',
        validators=[
            DataRequired(),
            NumberRange(min=0.01)
        ]
    )

    flash_sale_end_at = DateTimeLocalField(
        'Flash Sale End Time',
        format='%Y-%m-%dT%H:%M',
        validators=[DataRequired()]
    )

    flash_sale_stock = IntegerField(
        'Flash Sale Stock Limit',
        validators=[
            Optional(),
            NumberRange(min=1)
        ]
    )

    submit = SubmitField('Save Flash Sale')



class SignUpForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired()])
    username = StringField('Username', validators=[DataRequired(), length(min=5, max=50)])
    campus = SelectField('Campus / School', choices=CAMPUSES, validators=[DataRequired()])

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