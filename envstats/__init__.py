import os

from flask import Flask
from dotenv import load_dotenv


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite'),
    )

    load_dotenv()  # take environment variables from .env.

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # a simple page that says hello
    @app.route('/hello')
    def hello():
        return 'this is a factory'
    
    from . import db
    db.init_app(app)

    from . import stats
    app.register_blueprint(stats.bp)
    stats.init_app(app)


    return app