"""
グローバルホットキーユーティリティモジュール

Ctrl+Shift+S によるグローバルホットキー機能を提供します。
"""

import logging
import threading
from typing import Callable, Optional

import keyboard
from PySide6.QtCore import QObject, Signal


class HotkeyManager(QObject):
    """グローバルホットキー管理クラス"""
    
    # シグナル定義
    hotkey_triggered = Signal()  # ホットキーが押された時に発信
    hotkey_registered = Signal(str)  # ホットキー登録完了時にキー組み合わせを送信
    hotkey_failed = Signal(str)      # エラーメッセージを送信
    
    def __init__(self, hotkey_combination: str = "ctrl+shift+s") -> None:
        """
        グローバルホットキー管理クラスの初期化
        
        Args:
            hotkey_combination: ホットキーの組み合わせ（例: "ctrl+shift+s"）
        """
        super().__init__()
        self.hotkey_combination = hotkey_combination
        self.is_registered = False
        self.logger = logging.getLogger(__name__)
        
        # ホットキーを自動で登録
        self.register_hotkey()
    
    def register_hotkey(self) -> bool:
        """
        グローバルホットキーを登録
        
        Returns:
            bool: 登録成功可否
        """
        try:
            if self.is_registered:
                self.logger.warning("ホットキーは既に登録されています")
                return True
            
            # ホットキーのコールバック関数を登録
            keyboard.add_hotkey(
                self.hotkey_combination,
                self._on_hotkey_triggered,
                suppress=True  # 他のアプリケーションにキーイベントが伝播しないようにする
            )
            
            self.is_registered = True
            self.logger.info(f"グローバルホットキー '{self.hotkey_combination}' を登録しました")
            self.hotkey_registered.emit(self.hotkey_combination)
            return True
            
        except Exception as e:
            error_msg = f"ホットキーの登録に失敗しました: {str(e)}"
            self.logger.error(error_msg)
            self.hotkey_failed.emit(error_msg)
            return False
    
    def unregister_hotkey(self) -> bool:
        """
        グローバルホットキーの登録を解除
        
        Returns:
            bool: 解除成功可否
        """
        try:
            if not self.is_registered:
                self.logger.warning("ホットキーは登録されていません")
                return True
            
            keyboard.remove_hotkey(self.hotkey_combination)
            self.is_registered = False
            self.logger.info(f"グローバルホットキー '{self.hotkey_combination}' の登録を解除しました")
            return True
            
        except Exception as e:
            error_msg = f"ホットキーの登録解除に失敗しました: {str(e)}"
            self.logger.error(error_msg)
            self.hotkey_failed.emit(error_msg)
            return False
    
    def _on_hotkey_triggered(self) -> None:
        """ホットキーが押された時の内部コールバック"""
        self.logger.info(f"ホットキー '{self.hotkey_combination}' が押されました")
        self.hotkey_triggered.emit()
    
    def change_hotkey(self, new_combination: str) -> bool:
        """
        ホットキーの組み合わせを変更
        
        Args:
            new_combination: 新しいホットキーの組み合わせ
            
        Returns:
            bool: 変更成功可否
        """
        try:
            # 現在のホットキーを解除
            if self.is_registered:
                self.unregister_hotkey()
            
            # 新しいホットキーを設定
            self.hotkey_combination = new_combination
            
            # 新しいホットキーを登録
            return self.register_hotkey()
            
        except Exception as e:
            error_msg = f"ホットキーの変更に失敗しました: {str(e)}"
            self.logger.error(error_msg)
            self.hotkey_failed.emit(error_msg)
            return False
    
    def is_hotkey_registered(self) -> bool:
        """
        ホットキーが登録されているかを確認
        
        Returns:
            bool: 登録状態
        """
        return self.is_registered
    
    def get_hotkey_combination(self) -> str:
        """
        現在のホットキー組み合わせを取得
        
        Returns:
            str: ホットキーの組み合わせ
        """
        return self.hotkey_combination
    
    def cleanup(self) -> None:
        """リソースのクリーンアップ"""
        try:
            if self.is_registered:
                self.unregister_hotkey()
            self.logger.info("ホットキーマネージャーをクリーンアップしました")
        except Exception as e:
            self.logger.error(f"クリーンアップ中にエラーが発生しました: {str(e)}")


class HotkeyListener:
    """
    グローバルホットキーリスナー（非QObjectクラス）
    
    keyboardライブラリを使用してバックグラウンドでホットキーを監視します。
    """
    
    def __init__(self) -> None:
        """ホットキーリスナーの初期化"""
        self.logger = logging.getLogger(__name__)
        self.listening = False
        self.listener_thread: Optional[threading.Thread] = None
    
    def start_listening(self) -> None:
        """ホットキーリスナーを開始"""
        if self.listening:
            self.logger.warning("既にリスニング中です")
            return
        
        self.listening = True
        self.listener_thread = threading.Thread(target=self._listen_worker)
        self.listener_thread.daemon = True
        self.listener_thread.start()
        self.logger.info("ホットキーリスナーを開始しました")
    
    def stop_listening(self) -> None:
        """ホットキーリスナーを停止"""
        if not self.listening:
            self.logger.warning("リスニング中ではありません")
            return
        
        self.listening = False
        if self.listener_thread and self.listener_thread.is_alive():
            self.listener_thread.join(timeout=1.0)
        self.logger.info("ホットキーリスナーを停止しました")
    
    def _listen_worker(self) -> None:
        """ホットキーリスナーのワーカースレッド"""
        try:
            # keyboardライブラリのイベントループを実行
            keyboard.wait()  # 無限待機（プログラム終了まで）
        except Exception as e:
            self.logger.error(f"ホットキーリスナーでエラーが発生しました: {str(e)}")
        finally:
            self.listening = False