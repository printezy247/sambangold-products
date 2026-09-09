"""Application factory.

One Flask app carries all eighteen products: a page per product on the web
side, a command per product on the bot side, and one Telegram identity linking
the two.
"""

from flask import Flask

from .config import Config


def create_app(config_object=Config):
    app = Flask(__name__)
    app.config.from_object(config_object)
    app.config["MISSING"] = config_object.missing()

    from . import auth, telegram, views
    app.register_blueprint(views.bp)
    app.register_blueprint(auth.bp)
    app.register_blueprint(telegram.bp)

    return app
