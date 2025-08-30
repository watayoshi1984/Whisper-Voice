"""
メインアプリケーション制御ロジック

全てのコンポーネントを統合し、アプリケーション全体の動作を制御します。
"""

import logging
import sys
from typing import Optional

from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import QObject, Signal, QTimer

from app.audio_processor import AudioProcessor
from app.transcriber import TranscriptionEngine
from app.ui.main_window import MainWindow

# debug_windowは条件付きインポート
try:
    from app.ui.debug_window import DebugWindow
    DEBUG_WINDOW_AVAILABLE = True
except ImportError:
    DebugWindow = None
    DEBUG_WINDOW_AVAILABLE = False

from utils.clipboard import ClipboardManager
from utils.hotkey import HotkeyManager
from utils.logger_config import get_logger, setup_debug_logging, LogLevel, ErrorCode

# diagnostic_managerも条件付きインポート
try:
    from utils.diagnostic_manager import SystemDiagnosticManager
    DIAGNOSTIC_MANAGER_AVAILABLE = True
except ImportError:
    SystemDiagnosticManager = None
    DIAGNOSTIC_MANAGER_AVAILABLE = False


class WhisperVoiceApp(QObject):
    """Whisper Voice MVPアプリケーションクラス"""
    
    # シグナル定義
    app_started = Signal()
    app_shutting_down = Signal()
    
    def __init__(self, app: QApplication, debug_mode: bool = False, model_size: Optional[str] = None) -> None:
        """
        アプリケーションの初期化
        
        Args:
            app: QApplicationインスタンス
            debug_mode: デバッグモードの有効/無効
            model_size: Whisperモデルのサイズ
        """
        super().__init__()
        self.qt_app = app
        self.debug_mode = debug_mode
        self.model_size = model_size or "large-v3-turbo"
        
        # ログシステムの初期化
        if debug_mode:
            self.app_logger = setup_debug_logging()
        else:
            self.app_logger = get_logger()
        
        self.logger = self._setup_logging()
        
        # アプリケーションの状態
        self.is_recording = False
        self.is_processing = False
        self.is_shutting_down = False
        
        # コンポーネントの初期化
        self.main_window: Optional[MainWindow] = None
        self.debug_window: Optional[DebugWindow] = None
        self.audio_processor: Optional[AudioProcessor] = None
        self.transcription_engine: Optional[TranscriptionEngine] = None
        self.clipboard_manager: Optional[ClipboardManager] = None
        self.hotkey_manager: Optional[HotkeyManager] = None
        self.diagnostic_manager: Optional[SystemDiagnosticManager] = None
        
        # 初期化
        self._initialize_components()
        self._connect_signals()
        
        # デバッグモードでの追加初期化
        if debug_mode:
            self._initialize_debug_features()
        
        self.app_logger.info("WhisperVoiceApp", "Whisper Voice MVPアプリケーションを初期化しました")
        self.logger.info("Whisper Voice MVPアプリケーションを初期化しました")
    
    def _setup_logging(self) -> logging.Logger:
        """ロギング設定"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout)
            ]
        )
        return logging.getLogger(__name__)
    
    def _initialize_components(self) -> None:
        """アプリケーションコンポーネントの初期化"""
        try:
            self.app_logger.debug("WhisperVoiceApp", "コンポーネントの初期化を開始")
            
            # メインウィンドウ
            self.main_window = MainWindow()
            
            # コマンドライン引数のモデルをUIに反映
            if self.model_size == "large-v3-turbo":
                self.main_window.current_model = "large-v3-turbo"
                self.main_window.model_toggle_button.setText("turbo")
                self.main_window.model_toggle_button.setStyleSheet("""
                    QPushButton {
                        background-color: #3498db;
                        color: white;
                        border: none;
                        border-radius: 12px;
                        font-size: 9px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #2980b9;
                    }
                    QPushButton:pressed {
                        background-color: #21618c;
                    }
                """)
            
            # 音声処理
            self.audio_processor = AudioProcessor(sample_rate=16000, channels=1)

            # 音声デバイスの検証と列挙
            try:
                devices = self.audio_processor.get_audio_devices()
                device_names = [d.get('name') for d in devices]
                self.app_logger.info(
                    "WhisperVoiceApp",
                    f"入力音声デバイス検出数: {len(devices)}",
                    context={"devices": device_names}
                )
                self.logger.info(f"入力音声デバイス検出数: {len(devices)}")
            except Exception as dev_err:
                self.app_logger.warning(
                    "WhisperVoiceApp",
                    f"音声デバイス列挙で警告: {dev_err}"
                )
            
            mic_ok = self.audio_processor.verify_microphone_access()
            if mic_ok:
                self.app_logger.info("WhisperVoiceApp", "マイクアクセス検証に成功")
                self.logger.info("マイクアクセス検証に成功")
            else:
                self.app_logger.warning(
                    "WhisperVoiceApp",
                    "マイクアクセス検証に失敗。権限または占有状態を確認してください",
                    error_code=ErrorCode.AUDIO_PERMISSION_DENIED
                )
                self.logger.warning("マイクアクセス検証に失敗。権限または占有状態を確認してください")
            
            # 文字起こしエンジン（選択されたモデルで初期化）
            self.app_logger.info("WhisperVoiceApp", f"文字起こしモデルを初期化: {self.model_size}")
            self.transcription_engine = TranscriptionEngine(
                model_size=self.model_size, 
                device="cpu"
            )
            
            # クリップボード管理
            self.clipboard_manager = ClipboardManager()
            
            # ホットキー管理
            self.hotkey_manager = HotkeyManager(hotkey_combination="ctrl+shift+s")
            
            # 診断マネージャー（利用可能な場合のみ）
            if DIAGNOSTIC_MANAGER_AVAILABLE and SystemDiagnosticManager:
                self.diagnostic_manager = SystemDiagnosticManager()
                self.app_logger.info("WhisperVoiceApp", "診断マネージャーを初期化しました")
            else:
                self.diagnostic_manager = None
                self.app_logger.warning("WhisperVoiceApp", "診断マネージャーは利用できません")
            
            self.app_logger.info("WhisperVoiceApp", "全コンポーネントの初期化が完了しました")
            self.logger.info("全コンポーネントの初期化が完了しました")
            
        except Exception as e:
            error_msg = f"コンポーネントの初期化に失敗しました: {str(e)}"
            self.app_logger.critical(
                "WhisperVoiceApp", 
                error_msg,
                error_code=ErrorCode.SYSTEM_STARTUP_ERROR,
                exception=e
            )
            self.logger.error(error_msg)
            self._show_error_dialog("初期化エラー", error_msg)
            sys.exit(1)
    
    def _connect_signals(self) -> None:
        """シグナルとスロットの接続"""
        if not all([self.main_window, self.audio_processor, self.transcription_engine, 
                   self.clipboard_manager, self.hotkey_manager]):
            self.logger.error("コンポーネントが初期化されていません")
            return
        
        # メインウィンドウ
        self.main_window.mic_button_clicked.connect(self._toggle_recording)
        self.main_window.model_changed.connect(self._on_model_changed)
        
        # 音声処理
        self.audio_processor.recording_started.connect(self._on_recording_started)
        self.audio_processor.recording_stopped.connect(self._on_recording_stopped)
        self.audio_processor.audio_data_ready.connect(self._on_audio_data_ready)
        self.audio_processor.error_occurred.connect(self._on_audio_error)
        
        # 文字起こしエンジン
        self.transcription_engine.transcription_started.connect(self._on_transcription_started)
        self.transcription_engine.transcription_completed.connect(self._on_transcription_completed)
        self.transcription_engine.transcription_failed.connect(self._on_transcription_failed)
        self.transcription_engine.model_loading_started.connect(self._on_model_loading_started)
        self.transcription_engine.model_loading_completed.connect(self._on_model_loading_completed)
        # リアルタイム処理用シグナル（一時保留）
        # self.transcription_engine.partial_transcription.connect(self._on_partial_transcription)
        
        # クリップボード管理
        self.clipboard_manager.copy_completed.connect(self._on_clipboard_copy_completed)
        self.clipboard_manager.copy_failed.connect(self._on_clipboard_copy_failed)
        
        # ホットキー管理
        self.hotkey_manager.hotkey_triggered.connect(self._toggle_recording)
        self.hotkey_manager.hotkey_registered.connect(self._on_hotkey_registered)
        self.hotkey_manager.hotkey_failed.connect(self._on_hotkey_failed)
        
        self.logger.info("シグナル接続が完了しました")
    
    def _initialize_debug_features(self) -> None:
        """デバッグ機能の初期化"""
        try:
            self.app_logger.debug("WhisperVoiceApp", "デバッグ機能を初期化中...")
            
            # デバッグウィンドウ（利用可能な場合のみ）
            if DEBUG_WINDOW_AVAILABLE and DebugWindow:
                self.debug_window = DebugWindow(self.app_logger)
                self.app_logger.info("WhisperVoiceApp", "デバッグウィンドウを初期化しました")
            else:
                self.app_logger.warning("WhisperVoiceApp", "デバッグウィンドウは利用できません")
            
            # 診断マネージャーのシグナル接続
            if self.diagnostic_manager:
                self.diagnostic_manager.issue_detected.connect(self._on_diagnostic_issue_detected)
                self.diagnostic_manager.auto_fix_completed.connect(self._on_auto_fix_completed)
                
                # 定期診断を開始（5分間隔）
                self.diagnostic_manager.start_periodic_diagnostics(interval_minutes=5)
            
            self.app_logger.info("WhisperVoiceApp", "デバッグ機能の初期化が完了しました")
            
        except Exception as e:
            self.app_logger.error(
                "WhisperVoiceApp", 
                f"デバッグ機能の初期化に失敗: {e}",
                exception=e
            )
    
    def run(self) -> None:
        """アプリケーションの実行"""
        if not self.main_window:
            self.logger.error("メインウィンドウが初期化されていません")
            return
        
        try:
            # メインウィンドウを表示
            self.main_window.show()
            
            # アプリケーション開始シグナルを発信
            self.app_started.emit()
            
            self.logger.info("アプリケーションを開始しました")
            
        except Exception as e:
            error_msg = f"アプリケーションの開始に失敗しました: {str(e)}"
            self.logger.error(error_msg)
            self._show_error_dialog("開始エラー", error_msg)
    
    def _toggle_recording(self) -> None:
        """録音の開始/停止をトグル"""
        if self.is_shutting_down:
            return
        
        if self.is_processing:
            self.logger.warning("文字起こし処理中は録音の切り替えはできません")
            return
        
        if not self.transcription_engine.is_model_ready():
            self.logger.warning("Whisperモデルがまだロード中です")
            self._show_info_dialog("お待ちください", "Whisperモデルをロード中です。しばらくお待ちください。")
            return
        
        if self.is_recording:
            self._stop_recording()
        else:
            self._start_recording()
    
    def _start_recording(self) -> None:
        """録音開始"""
        if self.is_recording:
            return
        
        if self.audio_processor and self.audio_processor.start_recording():
            self.is_recording = True
            self.logger.info("録音を開始しました")
        else:
            self.logger.error("録音の開始に失敗しました")
    
    def _stop_recording(self) -> None:
        """録音停止"""
        if not self.is_recording:
            return
        
        if self.audio_processor:
            self.audio_processor.stop_recording()
            self.is_recording = False
            self.logger.info("録音を停止しました")
    
    def _on_recording_started(self) -> None:
        """録音開始時の処理"""
        if self.main_window:
            self.main_window.set_recording_state(True)
        self.logger.info("録音状態: 開始")
    
    def _on_recording_stopped(self) -> None:
        """録音停止時の処理"""
        if self.main_window:
            self.main_window.set_recording_state(False)
        self.logger.info("録音状態: 停止")
    
    def _on_audio_data_ready(self, audio_data) -> None:
        """音声データ準備完了時の処理"""
        if self.transcription_engine and not self.is_processing:
            self.logger.info("音声データを文字起こしエンジンに送信します")
            # 通常の文字起こし処理
            self.transcription_engine.transcribe_audio(audio_data, 16000)
        else:
            self.logger.warning("文字起こしエンジンが利用できないか、既に処理中です")
    
    def _on_audio_error(self, error_message: str) -> None:
        """音声処理エラー時の処理"""
        self.logger.error(f"音声処理エラー: {error_message}")
        self._show_error_dialog("音声エラー", error_message)
    
    def _on_transcription_started(self) -> None:
        """文字起こし開始時の処理"""
        self.is_processing = True
        if self.main_window:
            self.main_window.set_processing_state(True)
        self.logger.info("文字起こし処理: 開始")
    
    def _on_transcription_completed(self, text: str) -> None:
        """文字起こし完了時の処理"""
        self.is_processing = False
        if self.main_window:
            self.main_window.set_processing_state(False)
        
        self.logger.info(f"文字起こし完了: {text[:50]}...")
        
        # クリップボードにコピー
        if self.clipboard_manager:
            self.clipboard_manager.copy_to_clipboard(text)
        
        # 結果をUIに表示
        if self.main_window:
            self.main_window.show_transcription_result(text)
    
    def _on_transcription_failed(self, error_message: str) -> None:
        """文字起こし失敗時の処理"""
        self.is_processing = False
        if self.main_window:
            self.main_window.set_processing_state(False)
        
        self.logger.error(f"文字起こしエラー: {error_message}")
        self._show_error_dialog("文字起こしエラー", error_message)
    
    # リアルタイム機能は一時保留
    # def _on_partial_transcription(self, partial_text: str) -> None:
    #     """部分的な文字起こし結果の処理（リアルタイム用）"""
    #     self.logger.info(f"部分的な文字起こし結果: {partial_text[:50]}...")
    #     
    #     # UIからの現在のモード状態を取得
    #     current_realtime_mode = self.main_window.realtime_mode if self.main_window else self.realtime_mode
    #     
    #     # リアルタイムモードでは部分的な結果も表示
    #     if current_realtime_mode and self.main_window:
    #         # 既存のダイアログに追記するか、新しいダイアログを表示
    #         self.main_window.show_partial_transcription_result(partial_text)
    
    def _on_model_changed(self, model_name: str) -> None:
        """モデル変更時の処理"""
        self.logger.info(f"Whisperモデルが変更されました: {model_name}")
        
        # 録音中の場合は警告
        if self.is_recording:
            self.logger.warning("録音中のモデル変更は次回の録音から有効になります")
            return
        
        # 新しいモデルでTranscriptionEngineを再初期化
        if self.transcription_engine:
            self.logger.info(f"モデル '{model_name}' をロード中...")
            self.transcription_engine = TranscriptionEngine(
                model_size=model_name, 
                device="cpu"
            )
            
            # シグナルを再接続
            self.transcription_engine.transcription_started.connect(self._on_transcription_started)
            self.transcription_engine.transcription_completed.connect(self._on_transcription_completed)
            self.transcription_engine.transcription_failed.connect(self._on_transcription_failed)
            self.transcription_engine.model_loading_started.connect(self._on_model_loading_started)
            self.transcription_engine.model_loading_completed.connect(self._on_model_loading_completed)
    
    def _on_model_loading_started(self) -> None:
        """モデルロード開始時の処理"""
        self.app_logger.info("WhisperVoiceApp", "Whisperモデルのダウンロード/ロードを開始しました")
        self.logger.info("Whisperモデルのダウンロード/ロードを開始しました")
        
        # メインウィンドウにロード中状態を表示
        if self.main_window:
            self.main_window.setWindowTitle("Whisper Voice MVP - モデルロード中...")
        
        # インフォメーションダイアログを表示（モーダルではない）
        try:
            from PySide6.QtWidgets import QMessageBox
            from PySide6.QtCore import Qt
            
            if hasattr(self, '_loading_dialog'):
                return  # 既に表示中
            
            self._loading_dialog = QMessageBox(self.main_window)
            self._loading_dialog.setWindowTitle("モデルロード中")
            self._loading_dialog.setText(
                "Whisperモデルをダウンロード/ロード中です...\n\n"
                "初回実行時は数分かかる場合があります。\n"
                "しばらくお待ちください。"
            )
            self._loading_dialog.setStandardButtons(QMessageBox.NoButton)
            self._loading_dialog.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
            self._loading_dialog.show()
            
        except Exception as e:
            self.logger.warning(f"ロード中ダイアログの表示に失敗: {e}")
    
    def _on_model_loading_completed(self) -> None:
        """モデルロード完了時の処理"""
        self.app_logger.info("WhisperVoiceApp", "Whisperモデルのロードが完了しました")
        self.logger.info("Whisperモデルのロードが完了しました")
        
        # メインウィンドウのタイトルを元に戻す
        if self.main_window:
            self.main_window.setWindowTitle("Whisper Voice MVP")
        
        # ロード中ダイアログを閉じる
        if hasattr(self, '_loading_dialog'):
            try:
                self._loading_dialog.close()
                delattr(self, '_loading_dialog')
            except Exception as e:
                self.logger.warning(f"ロード中ダイアログの閉じる処理でエラー: {e}")
    
    def _on_clipboard_copy_completed(self, text: str) -> None:
        """クリップボードコピー完了時の処理"""
        self.logger.info("クリップボードへのコピーが完了しました")
    
    def _on_clipboard_copy_failed(self, error_message: str) -> None:
        """クリップボードコピー失敗時の処理"""
        self.logger.error(f"クリップボードエラー: {error_message}")
    
    def _on_hotkey_registered(self, combination: str) -> None:
        """ホットキー登録完了時の処理"""
        self.logger.info(f"ホットキー '{combination}' が登録されました")
    
    def _on_hotkey_failed(self, error_message: str) -> None:
        """ホットキーエラー時の処理"""
        self.logger.error(f"ホットキーエラー: {error_message}")
    
    def _show_error_dialog(self, title: str, message: str) -> None:
        """エラーダイアログを表示"""
        if self.main_window:
            QMessageBox.critical(self.main_window, title, message)
    
    def _show_info_dialog(self, title: str, message: str) -> None:
        """情報ダイアログを表示"""
        if self.main_window:
            QMessageBox.information(self.main_window, title, message)
    
    def shutdown(self) -> None:
        """アプリケーションのシャットダウン"""
        if self.is_shutting_down:
            return
        
        self.is_shutting_down = True
        self.app_shutting_down.emit()
        
        self.logger.info("アプリケーションをシャットダウンしています...")
        
        # 録音中の場合は停止
        if self.is_recording and self.audio_processor:
            self.audio_processor.stop_recording()
        
        # ホットキーの解除
        if self.hotkey_manager:
            self.hotkey_manager.cleanup()
        
        # メインウィンドウを閉じる
        if self.main_window:
            self.main_window.close()
        
        self.logger.info("シャットダウンが完了しました")
    
    def _on_diagnostic_issue_detected(self, diagnostic_result) -> None:
        """診断で問題が検出された時の処理"""
        self.app_logger.warning(
            "DiagnosticMonitor",
            f"問題を検出: {diagnostic_result.component} - {diagnostic_result.message}",
            context={
                "component": diagnostic_result.component,
                "status": diagnostic_result.status.value,
                "fix_available": diagnostic_result.fix_available
            }
        )
        
        # 自動修復が利用可能な場合は実行
        if diagnostic_result.fix_available and self.diagnostic_manager:
            self.diagnostic_manager.auto_fix_issue(diagnostic_result)
    
    def _on_auto_fix_completed(self, component: str, success: bool) -> None:
        """自動修復完了時の処理"""
        if success:
            self.app_logger.info(
                "AutoFix", 
                f"{component}の自動修復が成功しました"
            )
        else:
            self.app_logger.error(
                "AutoFix", 
                f"{component}の自動修復に失敗しました"
            )
    
    def show_debug_window(self) -> None:
        """デバッグウィンドウを表示"""
        if self.debug_window:
            self.debug_window.show()
            self.debug_window.raise_()
            self.debug_window.activateWindow()
    
    def run_diagnostics(self) -> None:
        """システム診断を実行"""
        if self.diagnostic_manager:
            self.diagnostic_manager.run_full_diagnostics()
    
    def get_app_status(self) -> dict:
        """アプリケーションの状態を取得"""
        return {
            "is_recording": self.is_recording,
            "is_processing": self.is_processing,
            "is_shutting_down": self.is_shutting_down,
            "model_ready": self.transcription_engine.is_model_ready() if self.transcription_engine else False,
            "hotkey_registered": self.hotkey_manager.is_hotkey_registered() if self.hotkey_manager else False
        }