import sys
import threading

import webview

from flask_app import init_app

webview_name = "Chat Analyzer"
host = "127.0.0.1"
flask_port = 8080

flask_app = init_app()


def start_web_server():
    flask_app.run(host=host, port=flask_port)


def on_start(window):
    window.maximize()


if __name__ == '__main__':
    web_server_thread = threading.Thread(target=start_web_server)
    web_server_thread.daemon = True
    web_server_thread.start()

    start_url = f"http://{host}:{flask_port}/"

    window = webview.create_window(
        webview_name,
        start_url,
        width=800,
        height=600,
        resizable=True,
    )

    webview.start(on_start, window)

    sys.exit()
