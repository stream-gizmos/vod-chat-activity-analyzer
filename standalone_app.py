import webview

from flask_app import init_app

webview_name = "Chat Analyzer"

flask_app = init_app()


def on_start(window):
    window.maximize()


if __name__ == '__main__':
    window = webview.create_window(
        webview_name,
        flask_app,
        width=800,
        height=600,
        resizable=True,
    )

    webview.start(
        on_start,
        window,
        ssl=True,
    )
