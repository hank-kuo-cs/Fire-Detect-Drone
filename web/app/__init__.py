import logging
from flask import Flask


def create_app():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s : %(message)s', datefmt='%m-%d %H:%M')
    app = Flask(__name__, static_folder='data', static_url_path='/data')

    app.secret_key = '71c88f17-91a8-4481-8919-8392b2e72fc7'
    app.config['JSON_AS_ASCII'] = False
    app.templates_auto_reload = True
    app.env = 'production'

    from web.app.view import view as view_blueprint
    app.register_blueprint(view_blueprint)

    from web.app.api import api as api_blueprint
    app.register_blueprint(api_blueprint, url_prefix='/api')

    return app
