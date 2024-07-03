from flask import Flask


# Inspired by https://github.com/ClimenteA/pywebview-flask-boilerplate-for-python-desktop-apps.git
def init_app():
    """Create the app from Blueprints"""

    app = Flask(__name__)

    from flask_app.views.front import front_bp
    app.register_blueprint(front_bp)

    return app
