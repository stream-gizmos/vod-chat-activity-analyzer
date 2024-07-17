import webview
import webview.menu as wm

from flask_app import init_app

webview_name = "Chat Analyzer"

flask_app = init_app()


def main():
    window = webview.create_window(
        webview_name,
        flask_app,
        width=800,
        height=600,
        resizable=True,
    )

    menu_items = build_menu()

    webview.start(
        on_start,
        window,
        menu=menu_items,
        private_mode=False,
        ssl=True,
        http_server=True,
        http_port=13377,
    )


def build_menu():
    return [
        wm.Menu(
            "Options",
            [
                wm.MenuAction("Clear all cookies", clear_cookies),
                wm.MenuSeparator(),
                wm.MenuAction("Exit", close_window),
            ],
        ),
    ]


def on_start(window):
    window.maximize()


def clear_cookies():
    window = webview.active_window()
    window.clear_cookies()


def close_window():
    window = webview.active_window()
    window.destroy()


if __name__ == "__main__":
    main()
