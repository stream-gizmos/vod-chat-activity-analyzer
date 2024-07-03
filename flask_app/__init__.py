import sys
import threading

import webview
from flask import Flask


# Inspired by https://github.com/ClimenteA/pywebview-flask-boilerplate-for-python-desktop-apps.git
class AppRunner:
    conf = dict(port=8080)

    def create_flask_app(self):
        """Create the app from Blueprints"""

        app = Flask(__name__)

        from flask_app.views.front import front_bp
        app.register_blueprint(front_bp)

        return app

    def run_application(self, run_in_browser=True, webview_name="App"):
        """Run in browser or in pywebview browser"""

        flask_app = self.create_flask_app()

        if run_in_browser:
            flask_app.run(host="0.0.0.0", port=self.conf["port"], debug=True)
            return

        def start_web_server():
            flask_app.run(host="127.0.0.1", port=self.conf["port"])

        web_server_thread = threading.Thread(target=start_web_server)
        web_server_thread.daemon = True
        web_server_thread.start()

        webview.create_window(
            webview_name,
            "http://127.0.0.1:{}/".format(self.conf["port"]),
            width=800,
            height=600,
            resizable=True,
        )
        webview.start()

        sys.exit()
