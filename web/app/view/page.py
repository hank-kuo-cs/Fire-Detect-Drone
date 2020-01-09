from . import view
from flask import render_template


@view.route('/')
def home():
    return render_template('home.html')


@view.route('/dev')
def dev():
    return render_template('dev.html')
