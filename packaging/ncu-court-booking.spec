# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_all


ddddocr_datas, ddddocr_binaries, ddddocr_hiddenimports = collect_all("ddddocr")

analysis = Analysis(
    ["run.py"],
    pathex=["."],
    binaries=ddddocr_binaries,
    datas=ddddocr_datas,
    hiddenimports=ddddocr_hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(analysis.pure)

executable = EXE(
    pyz,
    analysis.scripts,
    [],
    exclude_binaries=True,
    name="ncu-court-booking",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
)
collection = COLLECT(
    executable,
    analysis.binaries,
    analysis.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="ncu-court-booking",
)

