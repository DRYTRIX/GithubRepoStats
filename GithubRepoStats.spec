# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for GithubRepoStats one-file executable.
# Run from repo root: pyinstaller GithubRepoStats.spec

block_cipher = None

# config.yaml.example is bundled and extracted to sys._MEIPASS at runtime.
# Source paths are relative to the spec file location.
a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('config.yaml.example', '.')],
    hiddenimports=['yaml', 'requests'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['RPLCD', 'RPi.GPIO'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='GithubRepoStats',
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
