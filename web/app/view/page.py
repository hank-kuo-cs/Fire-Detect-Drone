from . import view
from flask import render_template
from random import randint


@view.route('/')
def home():
    return render_template('home.html')


@view.route('/dev')
def dev():
    color = ['red', 'blue', 'yellow', 'green']
    c = color[randint(0, 3)]
    return render_template('dev.html', dynamic_color=c, is_fire=False)
