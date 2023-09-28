import os
from flask import Flask, render_template
from dotenv import load_dotenv



def create_app():
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
    )
    app.config['CHEESE'] = 'edam'

    load_dotenv()  # take environment variables from .env.
    hosttest=os.getenv("HOSTTEST")

    # a simple page that says hello and some debug stuff.
    @app.route('/hello')
    def hello():
        content = {"brand": "Ford",}
        content['title'] = 'testing...'
        content['hosttest'] = hosttest
        return render_template('basic.html', content = content)
    from . import db
    db.init_app(app)

    from . import stats
    app.register_blueprint(stats.stats)
    stats.init_app(app)

    return app
