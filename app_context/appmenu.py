from importlib.metadata import entry_points


class ApplicationMenu:
    def __init__(self):
        self._menu: dict[str, dict] = {}

    @property
    def menu(self):
        return self._menu

    def add_section(self, alias: str, caption: str, target_url: str | None):
        if alias in self.menu:
            raise Exception(f"Menu section '{alias}' already exists")

        self.menu[alias] = {
            "caption": caption,
            "target_url": target_url,
            "sub_elements": [],
        }

    def add_section_element(self, section_alias: str, element_caption: str, target_url: str | None):
        if section_alias not in self.menu:
            raise Exception(f"Menu section '{section_alias}' does not exist")

        self.menu[section_alias]["sub_elements"].append({
            "caption": element_caption,
            "target_url": target_url,
        })


def compose_menu() -> ApplicationMenu:
    menu = ApplicationMenu()
    menu.add_section("vod_chat", "VOD Chat", target_url="/vod-chat/")

    _load_menu_extensions(menu)

    return menu


def _load_menu_extensions(menu: ApplicationMenu) -> None:
    discovered_extensions = entry_points(group="chat_analyzer.v1.blueprints", name="inject_menu")

    for extension in sorted(discovered_extensions):
        try:
            inject_menu = extension.load()
            inject_menu(menu)
        except Exception:
            print(f"Failed to update main manu by '{extension.module}' extension", flush=True)
            raise
