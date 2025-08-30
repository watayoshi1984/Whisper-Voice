"""
PyInstallerビルドスクリプト

Whisper Voice MVPアプリケーションを実行ファイル(.exe)にパッケージングします。
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path


def clean_build_directories() -> None:
    """ビルドディレクトリをクリーンアップ"""
    build_dirs = ['build', 'dist', '__pycache__']
    for dir_name in build_dirs:
        if os.path.exists(dir_name):
            print(f"削除中: {dir_name}")
            shutil.rmtree(dir_name)
    
    # .specファイルも削除
    spec_files = list(Path('.').glob('*.spec'))
    for spec_file in spec_files:
        print(f"削除中: {spec_file}")
        spec_file.unlink()


def create_pyinstaller_spec() -> str:
    """PyInstaller用の.specファイルを作成"""
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

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
'''
    
    spec_file = 'whisper_voice_mvp.spec'
    with open(spec_file, 'w', encoding='utf-8') as f:
        f.write(spec_content)
    
    return spec_file


def build_executable() -> bool:
    """実行ファイルをビルド"""
    try:
        print("PyInstallerでビルドを開始します...")
        
        # .specファイルを作成
        spec_file = create_pyinstaller_spec()
        print(f"作成した.specファイル: {spec_file}")
        
        # PyInstallerを実行
        cmd = [
            sys.executable, '-m', 'PyInstaller',
            '--clean',  # 以前のビルドをクリーンアップ
            spec_file
        ]
        
        print(f"実行コマンド: {' '.join(cmd)}")
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        print("ビルドが完了しました！")
        print(f"出力: {result.stdout}")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"ビルドエラー: {e}")
        print(f"stderr: {e.stderr}")
        return False
    except Exception as e:
        print(f"予期しないエラー: {e}")
        return False


def verify_build() -> bool:
    """ビルド結果を確認"""
    exe_path = Path('dist') / 'WhisperVoiceMVP.exe'
    
    if exe_path.exists():
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        print(f"✓ 実行ファイルが作成されました: {exe_path}")
        print(f"  ファイルサイズ: {size_mb:.1f} MB")
        return True
    else:
        print("✗ 実行ファイルが見つかりません")
        return False


def create_distribution_info() -> None:
    """配布用の情報ファイルを作成"""
    readme_content = """# Whisper Voice MVP - 配布版

## 概要
リアルタイム音声文字起こしアプリケーション

## 実行方法
1. WhisperVoiceMVP.exe をダブルクリックして実行
2. デスクトップ右下にマイクアイコンが表示されます
3. アイコンクリック または Ctrl+Shift+S で録音開始/停止
4. 文字起こし結果は自動でクリップボードにコピーされます

## 動作環境
- Windows 10/11 (64bit)
- マイクデバイスが接続されていること

## 注意事項
- 初回起動時はWhisperモデルのダウンロードに時間がかかる場合があります
- 音声認識処理にはCPUパワーが必要です
- インターネット接続は不要です（完全オフライン動作）

## トラブルシューティング
- マイクアイコンが表示されない → マイクデバイスの接続を確認
- 文字起こしができない → しばらく待ってから再試行
- エラーが発生する → アプリを再起動

バージョン: 1.0.0
作成日: 2025年8月28日
"""
    
    dist_path = Path('dist')
    if dist_path.exists():
        readme_path = dist_path / 'README.txt'
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        print(f"配布用README作成: {readme_path}")


def main() -> None:
    """メイン関数"""
    print("=" * 50)
    print("Whisper Voice MVP - 実行ファイルビルド")
    print("=" * 50)
    
    # 1. クリーンアップ
    print("\\n1. ビルドディレクトリをクリーンアップ...")
    clean_build_directories()
    
    # 2. ビルド実行
    print("\\n2. 実行ファイルをビルド...")
    if not build_executable():
        print("ビルドに失敗しました。")
        sys.exit(1)
    
    # 3. 結果確認
    print("\\n3. ビルド結果を確認...")
    if not verify_build():
        print("ビルド結果の確認に失敗しました。")
        sys.exit(1)
    
    # 4. 配布用ファイル作成
    print("\\n4. 配布用ファイルを作成...")
    create_distribution_info()
    
    print("\\n" + "=" * 50)
    print("ビルド完了！")
    print("実行ファイル: dist/WhisperVoiceMVP.exe")
    print("=" * 50)


if __name__ == "__main__":
    main()