from . import view
from flask import render_template
from random import randint
import re


@view.route('/')
def home():
    return render_template('home.html')


@view.route('/dev')
def dev():
    color = ['lightred', 'lightblue', 'lightyellow', 'lightgreen']
    c = color[randint(0, 3)]
    status_file = 'web/app/data/status.txt'

    with open(status_file, 'r') as f:
        s = f.readline()
        is_fire = re.findall('Fire=(.?)xxxx', s)[0]
        is_fire = (is_fire == '1')
        return render_template('dev.html', dynamic_color=c, is_fire=is_fire)


@view.route('/detect')
def detect():
    while True:
        try:
            is_fire, img_name = get_status()
            break
        except IndexError:
            print('index error')

    return render_template('detect.html', img_name=img_name, is_fire=is_fire)


def get_status():
    status_file = 'web/app/data/status.txt'
    with open(status_file, 'r') as f:
        s = f.readlines()

        find_status = re.findall('Fire=(.?)xxxx', s[0])
        if find_status:
            is_fire = find_status[0]

            img_name = re.findall('Name=(.+?)\n', s[1])
            if img_name:
                img_name = img_name[0]

            is_fire = (is_fire == '1')

        return is_fire, img_name
