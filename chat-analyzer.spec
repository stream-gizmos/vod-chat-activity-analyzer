# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files, collect_entry_point

entry_points = [
    "chat_analyzer.v1.blueprints",
    "chat_analyzer.v1.vod_chat.subplots",
]

hiddenimports = []

datas = [("flask_app/templates", "flask_app/templates"), ("flask_app/static", "flask_app/static")]
datas += collect_data_files("chat_downloader.formatting")

for ep in entry_points:
    datas += collect_entry_point(ep)[0]
    hiddenimports += collect_entry_point(ep)[1]

hiddenimports = list(set(hiddenimports))

for mod in hiddenimports:
    datas += collect_data_files(mod)

datas = list(set(datas))

a = Analysis(
    ["standalone_app.py"],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="chat-analyzer",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
