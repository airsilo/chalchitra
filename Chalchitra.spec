# Chalchitra.spec
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries=[
        ('libs/libmpv-2.dll', 'libs'),
    ],
    datas=[
        ('assets/fonts', 'assets/fonts'),
        ('assets/icon.ico', 'assets'),
    ],
    hiddenimports=[
        'PySide6.QtSvg',
        'PySide6.QtOpenGL',
        'PySide6.QtOpenGLWidgets',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Trim unused Qt modules to shrink the bundle
        'PySide6.QtWebEngineCore',
        'PySide6.QtWebEngineWidgets',
        'PySide6.QtWebEngineQuick',
        'PySide6.QtQuick',
        'PySide6.QtQml',
        'PySide6.QtNetwork',
        'PySide6.QtSql',
        'PySide6.QtTest',
        'PySide6.QtCharts',
        'PySide6.QtDataVisualization',
        'PySide6.QtPdf',
        'PySide6.QtPdfWidgets',
        'tkinter',
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Chalchitra',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,               # UPX can break Qt DLLs; leave off for now
    console=False,            # TRUE for first build — flip to False later
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='Chalchitra',
)