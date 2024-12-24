import os
from flask import Flask, render_template
from dotenv import load_dotenv



def create_app():
    # create and configure the app
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY='dev',
    )

    load_dotenv()  # take environment variables from .env.
    hosttest=os.getenv("HOSTTEST")
    from . import db
    db.init_app(app)

    from . import stats
    app.register_blueprint(stats.stats)
    stats.init_app(app)

    return app
