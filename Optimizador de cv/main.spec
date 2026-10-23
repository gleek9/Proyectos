# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# 1. Archivos estáticos de la interfaz web y recursos
added_files = [
    ('src/ui', 'src/ui'),
    ('assets', 'assets'),
]

# Datos adicionales requeridos por ReportLab y Trafilatura
added_files += collect_data_files('reportlab')
added_files += collect_data_files('trafilatura')

# 2. Módulos importados dinámicamente
hidden_imports = [
    'webview',
    'webview.platforms.winforms',
    'clr',
    'pythonnet',
    'clr_loader',
    'reportlab',
    'reportlab.platypus',
    'reportlab.lib.pagesizes',
    'reportlab.lib.colors',
    'reportlab.lib.styles',
    'reportlab.lib.enums',
    'google.genai',
    'pypdf',
    'docx',
    'trafilatura',
    'bs4',
    'sqlite3',
]

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=added_files,
    hiddenimports=hidden_imports,
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
    name='Cuva',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico'
)
