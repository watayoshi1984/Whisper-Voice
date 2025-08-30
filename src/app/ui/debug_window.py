"""
デバッグウィンドウモジュール

アプリケーションのデバッグ情報を表示するウィンドウを提供します。
"""

import logging
import sys
import threading
import time
from datetime import datetime
from logging import LogRecord
from typing import Dict, List, Optional, Tuple

import psutil
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTabWidget,
    QTextEdit,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QGroupBox,
    QProgressBar,
    QSplitter,
    QFrame,
    QScrollArea,
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QFont, QColor, QPalette

from src.utils.logger_config import WhisperVoiceLogger


def get_system_info() -> List[Tuple[str, str, str]]:
    """システム情報を取得"""
    results = []
    
    try:
        # CPU情報
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        results.append(("CPU使用率", "INFO", f"{cpu_percent}%"))
        results.append(("CPUコア数", "INFO", f"{cpu_count}"))
        
        # メモリ情報
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_available = memory.available / (1024**3)  # GB
        results.append(("メモリ使用率", "INFO", f"{memory_percent}%"))
        results.append(("利用可能メモリ", "INFO", f"{memory_available:.1f} GB"))
        
    except Exception as e:
        results.append(("システム情報", "ERROR", f"取得エラー: {e}"))
    
    try:
        # ディスク情報
        disk = psutil.disk_usage('/')
        disk_percent = (disk.used / disk.total) * 100
        disk_free = disk.free / (1024**3)  # GB
        results.append(("ディスク使用率", "INFO", f"{disk_percent:.1f}%"))
        results.append(("空き容量", "INFO", f"{disk_free:.1f} GB"))
        
    except Exception as e:
        results.append(("ディスク情報", "ERROR", f"取得エラー: {e}"))
    
    try:
        # メモリ詳細情報
        memory = psutil.virtual_memory()
        results.append(("総メモリ", "INFO", f"{memory.total / (1024**3):.1f} GB"))
        results.append(("使用中メモリ", "INFO", f"{memory.used / (1024**3):.1f} GB"))
        
    except Exception as e:
        results.append(("メモリ情報", "ERROR", f"取得エラー: {e}"))
    
    return results


class DebugWindow(QMainWindow):
    """デバッグウィンドウメインクラス"""
    
    def __init__(self, logger: WhisperVoiceLogger, parent=None) -> None:
        super().__init__(parent)
        self.logger = logger
        self.setup_ui()
        self.connect_signals()
        
        # ログ更新タイマー
        self.log_update_timer = QTimer()
        self.log_update_timer.timeout.connect(self.update_display)
        self.log_update_timer.start(1000)  # 1秒間隔
    
    def setup_ui(self) -> None:
        """UI初期化"""
        self.setWindowTitle("Whisper Voice - デバッグウィンドウ")
        self.setGeometry(100, 100, 1200, 800)
        
        # 中央ウィジェット
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # メインレイアウト
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        
        # 制御パネル
        control_panel = self.create_control_panel()
        layout.addWidget(control_panel)
        
        # タブウィジェット
        self.tab_widget = QTabWidget()
        
        # リアルタイムログタブ
        self.log_viewer = LogViewerWidget()
        self.tab_widget.addTab(self.log_viewer, "リアルタイムログ")
        
        # エラー統計タブ
        self.error_stats = ErrorStatisticsWidget()
        self.tab_widget.addTab(self.error_stats, "エラー統計")
        
        # システム診断タブ
        self.system_diagnostics = SystemDiagnosticsWidget()
        self.tab_widget.addTab(self.system_diagnostics, "システム診断")
        
        layout.addWidget(self.tab_widget)
        
        # ステータスバー
        self.statusBar().showMessage("デバッグウィンドウ準備完了")
    
    def create_control_panel(self) -> QWidget:
        """制御パネル作成"""
        panel = QFrame()
        panel.setFrameStyle(QFrame.StyledPanel)
        layout = QHBoxLayout()
        
        # ログレベルフィルター
        layout.addWidget(QLabel("ログレベル:"))
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["ALL", "TRACE", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        self.log_level_combo.setCurrentText("DEBUG")
        layout.addWidget(self.log_level_combo)
        
        # ログクリアボタン
        clear_button = QPushButton("ログクリア")
        clear_button.clicked.connect(self.clear_logs)
        layout.addWidget(clear_button)
        
        # ログエクスポートボタン
        export_button = QPushButton("ログエクスポート")
        export_button.clicked.connect(self.export_logs)
        layout.addWidget(export_button)
        
        # 自動スクロール
        self.auto_scroll_checkbox = QCheckBox("自動スクロール")
        self.auto_scroll_checkbox.setChecked(True)
        layout.addWidget(self.auto_scroll_checkbox)
        
        # スペーサー
        layout.addStretch()
        
        # 統計リセット
        reset_stats_button = QPushButton("統計リセット")
        reset_stats_button.clicked.connect(self.reset_statistics)
        layout.addWidget(reset_stats_button)
        
        panel.setLayout(layout)
        return panel
    
    def connect_signals(self) -> None:
        """シグナル接続"""
        self.logger.log_recorded.connect(self.on_log_recorded)
        self.logger.error_occurred.connect(self.on_error_occurred)
    
    def on_log_recorded(self, record: LogRecord) -> None:
        """新しいログレコード受信時の処理"""
        # ログレベルフィルタリング
        selected_level = self.log_level_combo.currentText()
        if selected_level != "ALL":
            if record.level.name != selected_level:
                return
        
        # ログビューアーに追加
        self.log_viewer.append_log_record(record)
        
        # エラー統計更新
        if record.error_code:
            self.error_stats.update_error_count(record.error_code)
    
    def on_error_occurred(self, error_code: str, message: str) -> None:
        """エラー発生時の処理"""
        self.statusBar().showMessage(f"エラー発生: [{error_code}] {message}", 5000)
    
    def clear_logs(self) -> None:
        """ログクリア"""
        self.log_viewer.clear_logs()
        self.logger.clear_logs()
        self.statusBar().showMessage("ログをクリアしました", 2000)
    
    def export_logs(self) -> None:
        """ログエクスポート"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "ログエクスポート", 
            f"whisper_voice_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            "JSON Files (*.json);;Text Files (*.txt)"
        )
        
        if file_path:
            format_type = "json" if file_path.endswith(".json") else "text"
            if self.logger.export_logs(Path(file_path), format_type):
                QMessageBox.information(self, "成功", f"ログを {file_path} にエクスポートしました")
            else:
                QMessageBox.warning(self, "エラー", "ログのエクスポートに失敗しました")
    
    def reset_statistics(self) -> None:
        """統計リセット"""
        self.error_stats.clear_statistics()
        self.statusBar().showMessage("統計をリセットしました", 2000)
    
    def update_display(self) -> None:
        """表示更新（定期実行）"""
        # メモリ使用量などの更新
        try:
            import psutil
            memory_percent = psutil.virtual_memory().percent
            cpu_percent = psutil.cpu_percent()
            self.setWindowTitle(f"Whisper Voice - デバッグウィンドウ (CPU: {cpu_percent:.1f}%, MEM: {memory_percent:.1f}%)")
        except:
            pass
    
    def closeEvent(self, event) -> None:
        """ウィンドウクローズイベント"""
        self.log_update_timer.stop()
        event.accept()