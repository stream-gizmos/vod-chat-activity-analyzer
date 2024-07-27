from flask import g

from app_context.appmenu import ApplicationMenu
from flask_app import init_app

app = init_app()


@app.before_request
def init_app_menu():
    menu = ApplicationMenu()

    menu.add_section("vod_chat", "VOD Chat", target_url="/vod-chat/")

    g.main_menu = menu


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080, debug=True)
