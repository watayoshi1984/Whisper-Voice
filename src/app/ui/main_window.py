"""
メインUIウィンドウモジュール

シンプルなマイクアイコンのフローティングウィンドウを提供します。
"""

import logging
from typing import Optional

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QDialog, QTextEdit, QApplication
)
from PySide6.QtCore import Qt, Signal, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import (
    QIcon, QPixmap, QPainter, QPen, QBrush, QColor, 
    QFont, QFontMetrics, QCursor
)


class MicrophoneButton(QPushButton):
    """マイクロフォンボタンウィジェット"""
    
    def __init__(self, parent=None) -> None:
        """マイクロフォンボタンの初期化"""
        super().__init__(parent)
        self.recording = False
        self.processing = False
        
        # ボタンの基本設定
        self.setFixedSize(80, 80)
        self.setStyleSheet(self._get_button_style())
        self.setCursor(QCursor(Qt.PointingHandCursor))
        
        # アニメーション用タイマー
        self.pulse_timer = QTimer()
        self.pulse_timer.timeout.connect(self._pulse_animation)
        self.pulse_state = 0
    
    def _get_button_style(self) -> str:
        """ボタンのスタイルシートを取得"""
        if self.processing:
            return """
                QPushButton {
                    border: 3px solid #FFA500;
                    border-radius: 40px;
                    background-color: #FFE4B5;
                }
                QPushButton:hover {
                    background-color: #FFD700;
                }
            """
        elif self.recording:
            return """
                QPushButton {
                    border: 3px solid #FF4444;
                    border-radius: 40px;
                    background-color: #FFE4E4;
                }
                QPushButton:hover {
                    background-color: #FFAAAA;
                }
            """
        else:
            return """
                QPushButton {
                    border: 3px solid #4CAF50;
                    border-radius: 40px;
                    background-color: #E8F5E8;
                }
                QPushButton:hover {
                    background-color: #C8E6C9;
                }
            """
    
    def paintEvent(self, event) -> None:
        """ボタンの描画イベント"""
        super().paintEvent(event)
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # マイクアイコンを描画
        self._draw_microphone_icon(painter)
    
    def _draw_microphone_icon(self, painter: QPainter) -> None:
        """マイクアイコンを描画"""
        rect = self.rect()
        center_x = rect.width() // 2
        center_y = rect.height() // 2
        
        # 色を設定
        if self.processing:
            color = QColor(255, 165, 0)  # オレンジ
        elif self.recording:
            color = QColor(255, 68, 68)  # 赤
        else:
            color = QColor(76, 175, 80)  # 緑
        
        painter.setPen(QPen(color, 3))
        painter.setBrush(QBrush(color))
        
        # マイク本体（楕円）
        mic_width = 20
        mic_height = 28
        mic_x = center_x - mic_width // 2
        mic_y = center_y - mic_height // 2 - 5
        painter.drawRoundedRect(mic_x, mic_y, mic_width, mic_height, 10, 10)
        
        # マイクスタンド（縦線）
        stand_x = center_x
        stand_y = mic_y + mic_height
        painter.drawLine(stand_x, stand_y, stand_x, stand_y + 15)
        
        # マイクベース（横線）
        base_width = 16
        base_y = stand_y + 15
        painter.drawLine(center_x - base_width // 2, base_y, 
                        center_x + base_width // 2, base_y)
        
        # 録音中の場合、パルス効果を追加
        if self.recording and self.pulse_timer.isActive():
            pulse_color = QColor(255, 68, 68, 100 - self.pulse_state * 10)
            painter.setPen(QPen(pulse_color, 2))
            painter.setBrush(QBrush(pulse_color))
            pulse_radius = 45 + self.pulse_state * 2
            painter.drawEllipse(center_x - pulse_radius // 2, center_y - pulse_radius // 2,
                              pulse_radius, pulse_radius)
    
    def set_recording(self, recording: bool) -> None:
        """録音状態を設定"""
        self.recording = recording
        self.setStyleSheet(self._get_button_style())
        
        if recording:
            self.pulse_timer.start(200)  # 200msごとにパルス
        else:
            self.pulse_timer.stop()
        
        self.update()
    
    def set_processing(self, processing: bool) -> None:
        """処理中状態を設定"""
        self.processing = processing
        self.setStyleSheet(self._get_button_style())
        self.update()
    
    def _pulse_animation(self) -> None:
        """パルスアニメーション"""
        self.pulse_state = (self.pulse_state + 1) % 10
        self.update()


class TranscriptionResultDialog(QDialog):
    """文字起こし結果表示ダイアログ"""
    
    def __init__(self, text: str, parent=None) -> None:
        """
        文字起こし結果ダイアログの初期化
        
        Args:
            text: 表示するテキスト
            parent: 親ウィジェット
        """
        super().__init__(parent)
        self.setWindowTitle("文字起こし結果")
        self.setFixedSize(400, 200)
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.Tool)
        
        # レイアウト設定
        layout = QVBoxLayout()
        
        # テキスト表示エリア
        self.text_edit = QTextEdit()
        self.text_edit.setPlainText(text)
        self.text_edit.setReadOnly(True)
        self.text_edit.setStyleSheet("""
            QTextEdit {
                font-size: 12pt;
                font-family: 'Meiryo UI', sans-serif;
                background-color: #f9f9f9;
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        layout.addWidget(self.text_edit)
        
        # 情報ラベル
        info_label = QLabel("テキストはクリップボードにコピーされました")
        info_label.setStyleSheet("""
            QLabel {
                color: #666;
                font-size: 10pt;
                text-align: center;
            }
        """)
        info_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(info_label)
        
        self.setLayout(layout)
        
        # 3秒後に自動で閉じる
        QTimer.singleShot(3000, self.close)


class MainWindow(QMainWindow):
    """メインウィンドウクラス"""
    
    # シグナル定義
    mic_button_clicked = Signal()
    
    def __init__(self) -> None:
        """メインウィンドウの初期化"""
        super().__init__()
        self.logger = logging.getLogger(__name__)
        
        # ウィンドウ設定
        self.setWindowTitle("Whisper Voice MVP")
        self.setFixedSize(120, 120)
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint | 
            Qt.FramelessWindowHint | 
            Qt.Tool
        )
        
        # 透明度の設定
        self.setWindowOpacity(0.9)
        
        # 中央ウィジェットとレイアウト
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setAlignment(Qt.AlignCenter)
        
        # マイクボタン
        self.mic_button = MicrophoneButton()
        self.mic_button.clicked.connect(self._on_mic_button_clicked)
        layout.addWidget(self.mic_button, alignment=Qt.AlignCenter)
        
        central_widget.setLayout(layout)
        
        # ウィンドウをデスクトップの右下に配置
        self._position_window()
        
        # スタイルシート適用
        self.setStyleSheet("""
            QMainWindow {
                background-color: rgba(255, 255, 255, 240);
                border-radius: 10px;
            }
        """)
    
    def _position_window(self) -> None:
        """ウィンドウを画面右下に配置"""
        screen = QApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        
        # 右下の位置を計算（マージン20px）
        x = screen_geometry.width() - self.width() - 20
        y = screen_geometry.height() - self.height() - 20
        
        self.move(x, y)
    
    def _on_mic_button_clicked(self) -> None:
        """マイクボタンクリック時の処理"""
        self.logger.info("マイクボタンがクリックされました")
        self.mic_button_clicked.emit()
    
    def set_recording_state(self, recording: bool) -> None:
        """録音状態を設定"""
        self.mic_button.set_recording(recording)
        
        # ウィンドウタイトルも更新
        if recording:
            self.setWindowTitle("Whisper Voice MVP - 録音中")
        else:
            self.setWindowTitle("Whisper Voice MVP")
    
    def set_processing_state(self, processing: bool) -> None:
        """処理中状態を設定"""
        self.mic_button.set_processing(processing)
        
        # ウィンドウタイトルも更新
        if processing:
            self.setWindowTitle("Whisper Voice MVP - 処理中")
        else:
            self.setWindowTitle("Whisper Voice MVP")
    
    def show_transcription_result(self, text: str) -> None:
        """
        文字起こし結果を表示
        
        Args:
            text: 表示するテキスト
        """
        dialog = TranscriptionResultDialog(text, self)
        dialog.show()
        
        # ダイアログをメインウィンドウの近くに配置
        dialog_x = self.x() - dialog.width() - 10
        dialog_y = self.y()
        
        # 画面外に出る場合は調整
        screen = QApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        
        if dialog_x < 0:
            dialog_x = self.x() + self.width() + 10
        if dialog_y + dialog.height() > screen_geometry.height():
            dialog_y = screen_geometry.height() - dialog.height() - 20
        
        dialog.move(dialog_x, dialog_y)
    
    def mousePressEvent(self, event) -> None:
        """マウスプレスイベント（ウィンドウドラッグ用）"""
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event) -> None:
        """マウス移動イベント（ウィンドウドラッグ用）"""
        if event.buttons() == Qt.LeftButton and hasattr(self, 'drag_position'):
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()
    
    def closeEvent(self, event) -> None:
        """ウィンドウクローズイベント"""
        self.logger.info("メインウィンドウを閉じています...")
        event.accept()