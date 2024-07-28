from importlib.metadata import entry_points

from flask import g

from app_context.appmenu import ApplicationMenu
from flask_app import init_app

app = init_app()


@app.before_request
def init_app_menu():
    menu = ApplicationMenu()

    menu.add_section("vod_chat", "VOD Chat", target_url="/vod-chat/")

    _load_menu_extensions(menu)

    # TODO Cache the value
    g.main_menu = menu


def _load_menu_extensions(menu: ApplicationMenu) -> None:
    discovered_extensions = entry_points(group="chat_analyzer.v1.blueprints", name="inject_menu")

    for extension in sorted(discovered_extensions):
        inject_menu = extension.load()
        inject_menu(menu)


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080, debug=True)
