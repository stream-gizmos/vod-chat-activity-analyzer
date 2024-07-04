import sys
import threading

import webview

from flask_app import init_app

webview_name = "Chat Analyzer"
host = "127.0.0.1"
port = 8080

flask_app = init_app()


def start_web_server():
    flask_app.run(host=host, port=port)


if __name__ == '__main__':
    web_server_thread = threading.Thread(target=start_web_server)
    web_server_thread.daemon = True
    web_server_thread.start()
    print(f"{web_server_thread=}")

    webview.create_window(webview_name, f"http://{host}:{port}/", width=800, height=600, resizable=True)
    webview.start()

    sys.exit()
