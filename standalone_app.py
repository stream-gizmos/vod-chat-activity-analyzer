import os

import webview
import webview.menu as wm
from dotenv import load_dotenv

from app_context.appmenu import compose_menu
from flask_app import init_app
from flask_app.services.utils import find_free_port


def main():
    webview.settings["OPEN_EXTERNAL_LINKS_IN_BROWSER"] = False

    webview_name = "Chat Analyzer"
    flask_app = init_app()

    window = webview.create_window(
        webview_name,
        flask_app,
        width=800,
        height=600,
        resizable=True,
    )

    menu_items = build_menu()

    http_port = find_free_port()
    webview.start(
        on_start,
        window,
        menu=menu_items,
        private_mode=False,
        ssl=True,
        http_server=True,
        http_port=http_port,
    )


def build_menu():
    menu = compose_menu()

    items = []
    for alias, section in menu.menu.items():
        items.append(wm.MenuAction(section["caption"], navigate_to(section["target_url"])))

    items.extend([
        wm.MenuSeparator(),
        wm.MenuAction("Switch color cheme", switch_theme),
        wm.MenuAction("Log out of all sites", clear_cookies),
        wm.MenuSeparator(),
        wm.MenuAction("Exit", close_window),
    ])

    result = [
        wm.Menu("Menu", items),
    ]

    return result


def on_start(window):
    window.maximize()


def navigate_to(url: str):
    def func():
        window = webview.active_window()
        window.load_url(url)

    return func


def switch_theme():
    print("Switch theme...", flush=True)
    window = webview.active_window()
    window.evaluate_js('siteTheme.setTheme(siteTheme.getOppositeTheme())')


def clear_cookies():
    print("Clearing all cookies...", flush=True)
    window = webview.active_window()
    window.clear_cookies()
    window.evaluate_js('alert("Cookies of all sites have been cleared.")')


def close_window():
    window = webview.active_window()
    window.destroy()


if __name__ == "__main__":
    env_file_path = os.path.abspath(os.path.join(os.getcwd(), ".env"))
    load_dotenv(dotenv_path=env_file_path)

    main()
