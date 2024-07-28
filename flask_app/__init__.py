from importlib.metadata import entry_points

from flask import Blueprint, Flask, redirect, url_for


def init_app():
    """Create the app from Blueprints"""

    app = Flask(__name__)

    from flask_app.views.vod_chat import vod_chat_bp
    app.register_blueprint(vod_chat_bp, url_prefix="/vod-chat")

    _load_blueprint_extensions(app)

    @app.route("/")
    def index():
        # TODO Make this redirect configurable on the application level.
        return redirect(url_for("vod_chat.index"))

    return app


def _load_blueprint_extensions(app: Flask) -> None:
    discovered_extensions = entry_points(group="chat_analyzer.v1.blueprints", name="inject_blueprint")

    for extension in sorted(discovered_extensions):
        try:
            inject_blueprint = extension.load()
            bp: Blueprint = inject_blueprint(app)

            if bp:
                print(
                    f"Successfully loaded blueprint '{bp.name}' ({bp.import_name}) from '{extension.module}' extension",
                    flush=True,
                )
        except Exception:
            print(f"Failed to load a blueprint from '{extension.module}' extension", flush=True)
            raise
