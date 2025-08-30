"""
クリップボード操作ユーティリティモジュール

文字起こし結果をクリップボードにコピーする機能を提供します。
"""

import logging
from typing import Optional

import pyperclip
from PySide6.QtCore import QObject, Signal


class ClipboardManager(QObject):
    """クリップボード管理クラス"""
    
    # シグナル定義
    copy_completed = Signal(str)  # コピー完了時にテキストを送信
    copy_failed = Signal(str)     # エラーメッセージを送信
    
    def __init__(self) -> None:
        """クリップボード管理クラスの初期化"""
        super().__init__()
        self.logger = logging.getLogger(__name__)
    
    def copy_to_clipboard(self, text: str) -> bool:
        """
        テキストをクリップボードにコピー
        
        Args:
            text: コピーするテキスト
            
        Returns:
            bool: コピー成功可否
        """
        try:
            if not text:
                self.logger.warning("空のテキストはコピーできません")
                return False
            
            # テキストの前後の空白を除去
            cleaned_text = text.strip()
            
            # クリップボードにコピー
            pyperclip.copy(cleaned_text)
            
            # 実際にコピーされたかを確認
            copied_text = pyperclip.paste()
            if copied_text == cleaned_text:
                self.logger.info(f"クリップボードにコピーしました: {cleaned_text[:50]}...")
                self.copy_completed.emit(cleaned_text)
                return True
            else:
                error_msg = "クリップボードへのコピーを確認できませんでした"
                self.logger.error(error_msg)
                self.copy_failed.emit(error_msg)
                return False
                
        except Exception as e:
            error_msg = f"クリップボードへのコピーに失敗しました: {str(e)}"
            self.logger.error(error_msg)
            self.copy_failed.emit(error_msg)
            return False
    
    def get_clipboard_content(self) -> Optional[str]:
        """
        クリップボードの内容を取得
        
        Returns:
            Optional[str]: クリップボードの内容（取得失敗時はNone）
        """
        try:
            content = pyperclip.paste()
            return content
        except Exception as e:
            self.logger.error(f"クリップボードの内容取得に失敗しました: {str(e)}")
            return None
    
    def clear_clipboard(self) -> bool:
        """
        クリップボードをクリア
        
        Returns:
            bool: クリア成功可否
        """
        try:
            pyperclip.copy("")
            self.logger.info("クリップボードをクリアしました")
            return True
        except Exception as e:
            error_msg = f"クリップボードのクリアに失敗しました: {str(e)}"
            self.logger.error(error_msg)
            self.copy_failed.emit(error_msg)
            return False