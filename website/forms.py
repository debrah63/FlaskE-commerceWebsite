from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, EmailField, SubmitField, RadioField
from wtforms.validators import DataRequired, length, EqualTo
from flask_wtf. file import FileField, FileRequired, FileAllowed
from wtforms import FloatField, IntegerField, BooleanField
from wtforms.validators import NumberRange


class ProductForm(FlaskForm):
    product_name = StringField('Product Name', validators=[DataRequired()])
    current_price = FloatField('Current Price', validators=[DataRequired()])
    previous_price = FloatField('Previous Price', validators=[DataRequired()])
    in_stock = IntegerField('In stock', validators=[DataRequired(), NumberRange(min=0)])
    product_picture = FileField('Product Picture', validators=[FileRequired(message='A product picture is required'),FileAllowed(['jpg', 'jpeg', 'png'], message='Images only (jpg, jpeg, png)')])
    flash_sale = BooleanField('Flash Sale')
    submit =SubmitField('Add Product')


class SignUpForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired()])
    username = StringField('Username', validators=[DataRequired(), length(min=5)])
    role = RadioField('I want to', choices=[('buyer', 'Buy product'), ('seller', 'Sell product')], default='buyer', validators=[DataRequired()])
    password1 = PasswordField('Enter Your Password', validators=[DataRequired(), length(min=6)])
    password2 = PasswordField('Confirm Your Password', validators=[DataRequired(), length(min=6), EqualTo( 'password1', message= 'Passwords must match')])
    submit = SubmitField('Sign Up')

class LoginForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired()])
    password = PasswordField('Enter Your Password', validators=[DataRequired()])
    submit = SubmitField('Log  In')