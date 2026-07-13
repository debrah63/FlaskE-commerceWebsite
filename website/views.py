from flask import Blueprint,render_template
from flask import send_from_directory

views = Blueprint('views',__name__)



@views.route('/media/<path:filename>')
def get_image(filename):
    return send_from_directory('../media', filename)

@views.route('/')
def home():

    return render_template('home.html')