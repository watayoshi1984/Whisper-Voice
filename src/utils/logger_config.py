"""
統合ログシステム設定

アプリケーション全体のログ管理、デバッグモード対応、ファイル出力機能を提供します。
"""

import logging
import logging.handlers
import sys
import os
import traceback
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, TextIO
from enum import Enum
import json

from PySide6.QtCore import QObject, Signal


class LogLevel(Enum):
    """ログレベル定義"""
    TRACE = 5
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


class ErrorCode(Enum):
    """エラーコード定義"""
    # システム系エラー (1000-1999)
    SYSTEM_STARTUP_ERROR = 1001
    SYSTEM_SHUTDOWN_ERROR = 1002
    SYSTEM_MEMORY_ERROR = 1003
    SYSTEM_PERMISSION_ERROR = 1004
    
    # 音声系エラー (2000-2999)
    AUDIO_DEVICE_NOT_FOUND = 2001
    AUDIO_DEVICE_BUSY = 2002
    AUDIO_PERMISSION_DENIED = 2003
    AUDIO_RECORDING_ERROR = 2004
    AUDIO_FORMAT_ERROR = 2005
    AUDIO_INPUT_ERROR = 2006
    
    # Whisper/AI系エラー (3000-3999)
    WHISPER_MODEL_LOAD_ERROR = 3001
    WHISPER_MODEL_NOT_FOUND = 3002
    WHISPER_TRANSCRIPTION_ERROR = 3003
    WHISPER_OUT_OF_MEMORY = 3004
    TRANSCRIPTION_PROCESSING_ERROR = 3005
    
    # UI系エラー (4000-4999)
    UI_INITIALIZATION_ERROR = 4001
    UI_DISPLAY_ERROR = 4002
    UI_INTERACTION_ERROR = 4003
    
    # ユーティリティ系エラー (5000-5999)
    CLIPBOARD_ERROR = 5001
    HOTKEY_REGISTRATION_ERROR = 5002
    FILE_IO_ERROR = 5003
    
    # ネットワーク系エラー (6000-6999)
    NETWORK_CONNECTION_ERROR = 6001
    NETWORK_TIMEOUT_ERROR = 6002


class LogRecord:
    """ログレコードクラス"""
    
    def __init__(
        self,
        timestamp: datetime,
        level: LogLevel,
        component: str,
        message: str,
        error_code: Optional[ErrorCode] = None,
        exception: Optional[Exception] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        self.timestamp = timestamp
        self.level = level
        self.component = component
        self.message = message
        self.error_code = error_code
        self.exception = exception
        self.context = context or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'level': self.level.name,
            'component': self.component,
            'message': self.message,
            'error_code': self.error_code.value if self.error_code else None,
            'exception': str(self.exception) if self.exception else None,
            'traceback': traceback.format_exception(type(self.exception), self.exception, self.exception.__traceback__) if self.exception else None,
            'context': self.context
        }
    
    def to_json(self) -> str:
        """JSON形式に変換"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


class ColoredFormatter(logging.Formatter):
    """カラー付きログフォーマッター"""
    
    # ANSI カラーコード
    COLORS = {
        'TRACE': '\033[90m',      # グレー
        'DEBUG': '\033[36m',      # シアン
        'INFO': '\033[32m',       # 緑
        'WARNING': '\033[33m',    # 黄色
        'ERROR': '\033[31m',      # 赤
        'CRITICAL': '\033[35m',   # マゼンタ
        'RESET': '\033[0m'        # リセット
    }
    
    def format(self, record: logging.LogRecord) -> str:
        """ログレコードをカラー付きでフォーマット（PyInstaller対応）"""
        try:
            # 時刻フォーマット（PyInstaller環境での安全な処理）
            if not hasattr(record, 'asctime'):
                record.asctime = self.formatTime(record, self.datefmt)
            
            # エラーコードがある場合は表示
            error_code = getattr(record, 'error_code', None)
            error_code_str = f"[{error_code.value}]" if error_code else ""
            
            # カラー付きフォーマット
            color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
            reset = self.COLORS['RESET']
            
            # ログメッセージのフォーマット
            log_message = (
                f"{color}[{record.asctime}] "
                f"{record.levelname:8} "
                f"| {record.name:20} "
                f"{error_code_str:8} "
                f"| {record.getMessage()}{reset}"
            )
            
            # 例外情報がある場合は追加
            if record.exc_info:
                log_message += f"\n{self.formatException(record.exc_info)}"
            
            return log_message
            
        except Exception as e:
            # フォーマットエラーが発生した場合のフォールバック
            return f"[LOGGING_ERROR] {record.levelname} | {record.name} | {record.getMessage()}"


class WhisperVoiceLogger(QObject):
    """Whisper Voice専用ログシステム"""
    
    # シグナル定義
    log_recorded = Signal(object)  # LogRecordオブジェクトを送信
    error_occurred = Signal(str, str)  # (エラーコード, メッセージ)
    
    def __init__(self, debug_mode: bool = False) -> None:
        super().__init__()
        self.debug_mode = debug_mode
        self.log_records: list[LogRecord] = []
        self.log_handlers: Dict[str, logging.Handler] = {}
        
        # ログディレクトリの作成
        self.log_dir = Path("logs")
        self.log_dir.mkdir(exist_ok=True)
        
        # ロガーの設定
        self._setup_loggers()
    
    def _setup_loggers(self) -> None:
        """ロガーの初期設定"""
        # ルートロガーの設定
        root_logger = logging.getLogger()
        root_logger.setLevel(LogLevel.TRACE.value if self.debug_mode else LogLevel.INFO.value)
        
        # 既存のハンドラーを削除
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # コンソールハンドラー
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(ColoredFormatter(
            fmt='%(asctime)s',
            datefmt='%H:%M:%S'
        ))
        root_logger.addHandler(console_handler)
        self.log_handlers['console'] = console_handler
        
        # ファイルハンドラー（回転式）
        file_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / f"whisper_voice_{datetime.now().strftime('%Y%m%d')}.log",
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        ))
        root_logger.addHandler(file_handler)
        self.log_handlers['file'] = file_handler
        
        if self.debug_mode:
            # デバッグモード時のJSON出力ハンドラー
            json_handler = logging.FileHandler(
                self.log_dir / f"debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                encoding='utf-8'
            )
            json_handler.setFormatter(logging.Formatter('%(message)s'))
            root_logger.addHandler(json_handler)
            self.log_handlers['json'] = json_handler
    
    def log(
        self,
        level: LogLevel,
        component: str,
        message: str,
        error_code: Optional[ErrorCode] = None,
        exception: Optional[Exception] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """統合ログ出力"""
        # ログレコードの作成
        log_record = LogRecord(
            timestamp=datetime.now(),
            level=level,
            component=component,
            message=message,
            error_code=error_code,
            exception=exception,
            context=context
        )
        
        # ログレコードを保存
        self.log_records.append(log_record)
        
        # シグナル送信
        self.log_recorded.emit(log_record)
        
        if error_code:
            self.error_occurred.emit(str(error_code.value), message)
        
        # 標準ログシステムへの出力
        logger = logging.getLogger(component)
        
        # エラーコード情報を追加
        extra = {'error_code': error_code} if error_code else {}
        
        if level == LogLevel.TRACE:
            logger.debug(message, extra=extra)
        elif level == LogLevel.DEBUG:
            logger.debug(message, extra=extra)
        elif level == LogLevel.INFO:
            logger.info(message, extra=extra)
        elif level == LogLevel.WARNING:
            logger.warning(message, extra=extra)
        elif level == LogLevel.ERROR:
            if exception:
                logger.error(message, exc_info=exception, extra=extra)
            else:
                logger.error(message, extra=extra)
        elif level == LogLevel.CRITICAL:
            if exception:
                logger.critical(message, exc_info=exception, extra=extra)
            else:
                logger.critical(message, extra=extra)
        
        # デバッグモード時のJSON出力
        if self.debug_mode and 'json' in self.log_handlers:
            json_handler = self.log_handlers['json']
            json_handler.emit(logging.LogRecord(
                name=component,
                level=level.value,
                pathname="",
                lineno=0,
                msg=log_record.to_json(),
                args=(),
                exc_info=None
            ))
    
    def trace(self, component: str, message: str, **kwargs) -> None:
        """TRACEレベルログ"""
        self.log(LogLevel.TRACE, component, message, **kwargs)
    
    def debug(self, component: str, message: str, **kwargs) -> None:
        """DEBUGレベルログ"""
        self.log(LogLevel.DEBUG, component, message, **kwargs)
    
    def info(self, component: str, message: str, **kwargs) -> None:
        """INFOレベルログ"""
        self.log(LogLevel.INFO, component, message, **kwargs)
    
    def warning(self, component: str, message: str, **kwargs) -> None:
        """WARNINGレベルログ"""
        self.log(LogLevel.WARNING, component, message, **kwargs)
    
    def error(self, component: str, message: str, **kwargs) -> None:
        """ERRORレベルログ"""
        self.log(LogLevel.ERROR, component, message, **kwargs)
    
    def critical(self, component: str, message: str, **kwargs) -> None:
        """CRITICALレベルログ"""
        self.log(LogLevel.CRITICAL, component, message, **kwargs)
    
    def get_recent_logs(self, count: int = 100) -> list[LogRecord]:
        """最新のログレコードを取得"""
        return self.log_records[-count:] if len(self.log_records) > count else self.log_records
    
    def get_error_logs(self) -> list[LogRecord]:
        """エラーログのみを取得"""
        return [record for record in self.log_records 
               if record.level in [LogLevel.ERROR, LogLevel.CRITICAL]]
    
    def export_logs(self, file_path: Path, format_type: str = 'json') -> bool:
        """ログをファイルにエクスポート"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                if format_type == 'json':
                    data = [record.to_dict() for record in self.log_records]
                    json.dump(data, f, ensure_ascii=False, indent=2)
                elif format_type == 'text':
                    for record in self.log_records:
                        f.write(f"[{record.timestamp}] {record.level.name} | {record.component} | {record.message}\n")
                        if record.exception:
                            f.write(f"  Exception: {record.exception}\n")
            return True
        except Exception as e:
            self.error("LogSystem", f"ログエクスポートエラー: {e}", exception=e)
            return False
    
    def clear_logs(self) -> None:
        """ログをクリア"""
        self.log_records.clear()
        self.info("LogSystem", "ログをクリアしました")


# グローバルロガーインスタンス
_logger_instance: Optional[WhisperVoiceLogger] = None


def get_logger(debug_mode: bool = False) -> WhisperVoiceLogger:
    """グローバルロガーインスタンスを取得"""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = WhisperVoiceLogger(debug_mode=debug_mode)
    return _logger_instance


def setup_debug_logging() -> WhisperVoiceLogger:
    """デバッグログシステムを初期化"""
    global _logger_instance
    _logger_instance = WhisperVoiceLogger(debug_mode=True)
    _logger_instance.info("LogSystem", "デバッグログシステムが初期化されました")
    return _logger_instance