from importlib.metadata import entry_points

from flask import Flask


# Inspired by https://github.com/ClimenteA/pywebview-flask-boilerplate-for-python-desktop-apps.git
def init_app():
    """Create the app from Blueprints"""

    app = Flask(__name__)

    from flask_app.views.front import front_bp
    app.register_blueprint(front_bp)

    load_blueprint_extensions(app)

    return app


def load_blueprint_extensions(app: Flask) -> None:
    # Entry point groups
    # chat_analyzer.v1.blueprints
    # chat_analyzer.v1.vod_chat.plots
    # chat_analyzer.v1.vod_chat.widgets

    discovered_plugins = entry_points(group="chat_analyzer.v1.blueprints")
    # from pprint import pprint
    # pprint(discovered_plugins)

    if "inject_blueprint" in discovered_plugins.names:
        inject_blueprint = discovered_plugins["inject_blueprint"].load()
        inject_blueprint(app)
