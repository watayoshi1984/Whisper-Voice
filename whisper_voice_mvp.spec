# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files

block_cipher = None

# パス設定
project_root = Path.cwd()
src_path = project_root / "src"

faster_whisper_datas = collect_data_files('faster_whisper', includes=['assets/*.onnx'])

a = Analysis(
    ['src/main.py'],
    pathex=[str(project_root), str(src_path)],
    binaries=[],
    datas=faster_whisper_datas,
    hiddenimports=[
        'PySide6.QtCore',
        'PySide6.QtWidgets', 
        'PySide6.QtGui',
        'faster_whisper',
        'ctranslate2',
        'onnxruntime',
        'sounddevice',
        'keyboard',
        'pyperclip',
        'torch',
        'numpy',
        'soundfile',
        'psutil',
        'pkg_resources.extern',
        'pkg_resources._vendor',
        # アプリケーションモジュールを明示的に追加
        'app',
        'app.core',
        'app.audio_processor',
        'app.transcriber',
        'app.ui',
        'app.ui.main_window',
        'app.ui.debug_window',
        'utils',
        'utils.logger_config',
        'utils.hotkey',
        'utils.clipboard',
        'utils.diagnostic_manager',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'scipy',
        'pandas',
        'PIL',
        'tkinter',
        'jupyter',
        'notebook',
        'IPython',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# ファイルの重複を除去
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='WhisperVoiceMVP',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # デバッグのため一時的にコンソールを表示
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # アイコンファイルがあれば指定
)
