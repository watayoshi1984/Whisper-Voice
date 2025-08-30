"""
開発用実行スクリプト

Poetryを使用してアプリケーションを実行します。
"""

import subprocess
import sys
import os
from pathlib import Path


def check_poetry() -> bool:
    """Poetryがインストールされているかチェック"""
    try:
        result = subprocess.run(['poetry', '--version'], 
                              capture_output=True, text=True, check=True)
        print(f"Poetry バージョン: {result.stdout.strip()}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("エラー: Poetryがインストールされていません")
        print("Poetryをインストールしてください: https://python-poetry.org/docs/")
        return False


def install_dependencies() -> bool:
    """依存関係をインストール"""
    try:
        print("依存関係をインストール中...")
        subprocess.run(['poetry', 'install'], check=True)
        print("依存関係のインストールが完了しました")
        return True
    except subprocess.CalledProcessError as e:
        print(f"依存関係のインストールに失敗しました: {e}")
        return False


def run_application() -> None:
    """アプリケーションを実行"""
    try:
        print("Whisper Voice MVPを開始します...")
        print("終了するには Ctrl+C を押してください")
        print("-" * 50)
        
        # 追加のCLI引数をそのままmainに渡す（例: --model large-v3）
        extra_args = sys.argv[2:] if len(sys.argv) > 2 else []
        cmd = ['poetry', 'run', 'python', 'src/main.py'] + extra_args
        subprocess.run(cmd, check=True)
        
    except KeyboardInterrupt:
        print("\\nアプリケーションを終了しました")
    except subprocess.CalledProcessError as e:
        print(f"アプリケーションの実行に失敗しました: {e}")


def run_tests() -> bool:
    """テストを実行"""
    try:
        print("テストを実行中...")
        result = subprocess.run(['poetry', 'run', 'pytest', 'tests/', '-v'], 
                              check=True, capture_output=True, text=True)
        print(result.stdout)
        print("テストが完了しました")
        return True
    except subprocess.CalledProcessError as e:
        print(f"テストに失敗しました: {e}")
        if e.stdout:
            print(f"stdout: {e.stdout}")
        if e.stderr:
            print(f"stderr: {e.stderr}")
        return False


def main() -> None:
    """メイン関数"""
    print("=" * 50)
    print("Whisper Voice MVP - 開発用実行スクリプト")
    print("=" * 50)
    
    # Poetryの確認
    if not check_poetry():
        sys.exit(1)
    
    # プロジェクトルートに移動
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    # コマンドライン引数の処理
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "install":
            print("\\n依存関係をインストールします...")
            if install_dependencies():
                print("インストール完了！")
            else:
                sys.exit(1)
        
        elif command == "test":
            print("\\nテストを実行します...")
            if not install_dependencies():
                sys.exit(1)
            if run_tests():
                print("テスト完了！")
            else:
                sys.exit(1)
        
        elif command == "run":
            print("\\nアプリケーションを実行します...")
            if not install_dependencies():
                sys.exit(1)
            run_application()
        
        else:
            print(f"不明なコマンド: {command}")
            print("使用方法: python run_dev.py [install|test|run]")
            sys.exit(1)
    
    else:
        # デフォルト: 依存関係インストール → アプリケーション実行
        print("\\n1. 依存関係をインストール...")
        if not install_dependencies():
            sys.exit(1)
        
        print("\\n2. アプリケーションを実行...")
        run_application()


if __name__ == "__main__":
    main()