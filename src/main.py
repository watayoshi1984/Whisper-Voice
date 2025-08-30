"""
Whisper Voice MVP - アプリケーションエントリーポイント

リアルタイム文字起こしアプリケーションのメイン実行ファイルです。
"""

import sys
import os
import argparse
import signal
import logging
from pathlib import Path
from typing import Optional

# PyInstaller環境でのパス設定
if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    # PyInstallerでパッケージされた場合
    bundle_dir = Path(sys._MEIPASS)
    # PyInstallerではモジュールは既にパッケージ内に含まれているため、
    # srcパスではなくbundle_dirを使用
    if str(bundle_dir) not in sys.path:
        sys.path.insert(0, str(bundle_dir))
    
    # PyInstaller環境では、appモジュールは既に適切にパッケージされている
    print(f"PyInstaller環境で実行中: {bundle_dir}")
else:
    # 開発環境の場合
    bundle_dir = Path(__file__).parent
    # 開発環境では、現在のsrcディレクトリをパスに追加
    if str(bundle_dir) not in sys.path:
        sys.path.insert(0, str(bundle_dir))
    print(f"開発環境で実行中: {bundle_dir}")

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QCoreApplication

try:
    from app.core import WhisperVoiceApp
except ImportError as e:
    print(f"Import error: {e}")
    print(f"sys.path: {sys.path}")
    print(f"bundle_dir: {bundle_dir}")
    raise


def setup_signal_handlers(app: Optional[WhisperVoiceApp]) -> None:
    """シグナルハンドラーの設定"""
    def signal_handler(signum, frame):
        logging.info(f"シグナル {signum} を受信しました。アプリケーションを終了します...")
        if app:
            app.shutdown()
        QCoreApplication.quit()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


def main() -> int:
    """メイン関数"""
    # ロギング設定（統合ロガーと標準ロガーの両方を初期化）
    from utils.logger_config import get_logger, setup_debug_logging
    logger = logging.getLogger(__name__)
    
    try:
        # CLI引数の解析と環境変数からのモデル選択
        parser = argparse.ArgumentParser(description="Whisper Voice MVP")
        parser.add_argument(
            "--model",
            dest="model",
            choices=["large-v3-turbo", "large-v3", "medium", "small", "base"],
            help="使用するWhisperモデル（デフォルト: large-v3-turbo）",
            default=None,
        )
        parser.add_argument(
            "--debug",
            action="store_true",
            help="デバッグログを有効化（パッケージ版はデフォルトで有効）",
        )
        args, _ = parser.parse_known_args()
        model_from_env = os.environ.get("WHISPER_MODEL")
        selected_model = args.model or model_from_env or "large-v3-turbo"

        # デバッグモード判定
        env_debug = os.environ.get("WHISPER_DEBUG", "").lower() in ("1", "true", "yes")
        is_packaged = getattr(sys, "frozen", False)
        debug_mode = bool(args.debug or env_debug or is_packaged)

        # 統合ロガー初期化（できるだけ早く）
        if debug_mode:
            setup_debug_logging()
        else:
            get_logger()

        # QApplicationの初期化
        qt_app = QApplication(sys.argv)
        qt_app.setApplicationName("Whisper Voice MVP")
        qt_app.setApplicationVersion("1.0.0")
        qt_app.setOrganizationName("Qoder AI")
        
        # 起動情報ログ
        logging.getLogger("startup").info(
            "アプリ起動: model=%s, debug=%s, packaged=%s, python=%s",
            selected_model,
            debug_mode,
            is_packaged,
            sys.version.split(" ")[0],
        )
        logging.getLogger("startup").info("作業ディレクトリ: %s", os.getcwd())

        # アプリケーションの作成
        app = WhisperVoiceApp(qt_app, debug_mode=debug_mode, model_size=selected_model)
        
        # シグナルハンドラーの設定
        setup_signal_handlers(app)
        
        # アプリケーション終了時のクリーンアップ設定
        qt_app.aboutToQuit.connect(app.shutdown)
        
        # アプリケーションの実行
        app.run()
        
        logger.info("Whisper Voice MVP が開始されました")
        logger.info("Ctrl+Shift+S またはマイクアイコンクリックで録音開始/停止")
        
        # イベントループの開始
        return qt_app.exec()
        
    except KeyboardInterrupt:
        logger.info("Ctrl+C が押されました。アプリケーションを終了します...")
        return 0
    except Exception as e:
        logger.error(f"予期しないエラーが発生しました: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())