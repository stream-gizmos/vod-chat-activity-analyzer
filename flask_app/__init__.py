from importlib.metadata import entry_points

from flask import Flask, redirect, url_for


# Inspired by https://github.com/ClimenteA/pywebview-flask-boilerplate-for-python-desktop-apps.git
def init_app():
    """Create the app from Blueprints"""

    app = Flask(__name__)

    from flask_app.views.vod_chat import vod_chat_bp
    app.register_blueprint(vod_chat_bp, url_prefix="/vod-chat")

    _load_blueprint_extensions(app)

    @app.route("/")
    def index():
        #vod_chat_bp.ur
        return redirect(url_for("vod_chat.index"))

    return app



def _load_blueprint_extensions(app: Flask) -> None:
    discovered_plugins = entry_points(group="chat_analyzer.v1.blueprints")

    if "inject_blueprint" in discovered_plugins.names:
        inject_blueprint = discovered_plugins["inject_blueprint"].load()
        inject_blueprint(app)
