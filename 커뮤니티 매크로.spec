# -*- mode: python ; coding: utf-8 -*-


block_cipher = None


a = Analysis(
    ['c:\\Users\\Administrator\\Desktop\\community-auto-write\\커뮤니티 매크로.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['chardet', 'fake-useragent'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    a.zipfiles,
    a.datas,
    [],
    name='커뮤니티 매크로',
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
    icon=['c:\\Users\\Administrator\\Desktop\\community-auto-write\\icon.ico'],
)
