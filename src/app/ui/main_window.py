"""
メインUIウィンドウモジュール

シンプルなマイクアイコンのフローティングウィンドウを提供します。
"""

import logging
import pyperclip

from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QDialog,
    QApplication,
    QPlainTextEdit,
    QFrame,
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QCursor


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
        """改善されたマイクアイコンを描画"""
        rect = self.rect()
        center_x = rect.width() // 2
        center_y = rect.height() // 2

        # 状態に応じた色設定
        if self.processing:
            primary_color = QColor(255, 165, 0)  # オレンジ
            secondary_color = QColor(255, 215, 0, 150)  # ゴールド（半透明）
        elif self.recording:
            primary_color = QColor(239, 68, 68)  # 現代的な赤
            secondary_color = QColor(255, 107, 107, 150)  # ライトレッド（半透明）
        else:
            primary_color = QColor(34, 197, 94)  # 現代的な緑
            secondary_color = QColor(74, 222, 128, 150)  # ライトグリーン（半透明）

        # アンチエイリアシング設定
        painter.setRenderHint(QPainter.Antialiasing, True)

        # マイク本体（カプセル型）
        mic_width = 24
        mic_height = 32
        mic_x = center_x - mic_width // 2
        mic_y = center_y - mic_height // 2 - 8

        # マイク本体の影（深度効果）
        shadow_color = QColor(0, 0, 0, 30)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(shadow_color))
        painter.drawRoundedRect(mic_x + 2, mic_y + 2, mic_width, mic_height, 12, 12)

        # マイク本体（メイン）
        painter.setPen(QPen(primary_color, 2))
        painter.setBrush(QBrush(primary_color))
        painter.drawRoundedRect(mic_x, mic_y, mic_width, mic_height, 12, 12)

        # マイクグリル（詳細）
        painter.setPen(QPen(QColor(255, 255, 255, 180), 1.5))
        for i in range(3):
            y_offset = mic_y + 8 + i * 6
            painter.drawLine(mic_x + 6, y_offset, mic_x + mic_width - 6, y_offset)

        # マイクスタンド（改善されたデザイン）
        stand_width = 3
        stand_height = 18
        stand_x = center_x - stand_width // 2
        stand_y = mic_y + mic_height

        # スタンド影
        painter.setBrush(QBrush(shadow_color))
        painter.drawRoundedRect(
            stand_x + 1, stand_y + 1, stand_width, stand_height, 1.5, 1.5
        )

        # スタンド本体
        painter.setBrush(QBrush(primary_color))
        painter.drawRoundedRect(stand_x, stand_y, stand_width, stand_height, 1.5, 1.5)

        # マイクベース（円形ベース）
        base_radius = 14
        base_y = stand_y + stand_height
        base_center_y = base_y + 2

        # ベース影
        painter.setBrush(QBrush(shadow_color))
        painter.drawEllipse(
            center_x - base_radius + 1, base_center_y - 2 + 1, base_radius * 2, 4
        )

        # ベース本体
        painter.setBrush(QBrush(primary_color))
        painter.drawEllipse(
            center_x - base_radius, base_center_y - 2, base_radius * 2, 4
        )

        # 録音中のパルス効果（改善）
        if self.recording and self.pulse_timer.isActive():
            pulse_alpha = 80 - self.pulse_state * 8
            pulse_color = QColor(
                primary_color.red(),
                primary_color.green(),
                primary_color.blue(),
                pulse_alpha,
            )
            painter.setPen(QPen(pulse_color, 2))
            painter.setBrush(Qt.NoBrush)

            # 複数のパルス波
            for i in range(2):
                pulse_radius = 35 + self.pulse_state * 3 + i * 8
                painter.drawEllipse(
                    center_x - pulse_radius // 2,
                    center_y - pulse_radius // 2,
                    pulse_radius,
                    pulse_radius,
                )

        # 処理中のスピナー効果
        if self.processing:
            spinner_color = QColor(
                secondary_color.red(),
                secondary_color.green(),
                secondary_color.blue(),
                120,
            )
            painter.setPen(QPen(spinner_color, 3))
            painter.setBrush(Qt.NoBrush)

            # 回転するアーク
            start_angle = (self.pulse_state * 36) * 16  # 16ths of a degree
            span_angle = 120 * 16
            painter.drawArc(
                center_x - 30, center_y - 30, 60, 60, start_angle, span_angle
            )

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


# リアルタイム機能は一時保留 - 全体をコメントアウト
# class RealtimeTranscriptionDialog(QDialog):
#     """リアルタイム文字起こし結果ダイアログ"""
#     
#     def __init__(self, initial_text: str, parent=None):
#         super().__init__(parent)
#         self.setWindowTitle("リアルタイム文字起こし")
#         self.setFixedSize(500, 300)
#         self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.Tool)
#         
#         # レイアウト設定
#         layout = QVBoxLayout()
#         layout.setSpacing(10)
#         layout.setContentsMargins(15, 15, 15, 15)
#         
#         # タイトル
#         title_label = QLabel("リアルタイム文字起こし結果")
#         title_label.setStyleSheet("""
#             QLabel {
#                 font-size: 14px;
#                 font-weight: bold;
#                 color: #2c3e50;
#                 margin-bottom: 10px;
#             }
#         """)
#         layout.addWidget(title_label)
#         
#         # テキストエリア
#         self.text_edit = QPlainTextEdit()
#         self.text_edit.setPlainText(initial_text)
#         self.text_edit.setReadOnly(True)  # リアルタイムは読み取り専用
#         self.text_edit.setStyleSheet("""
#             QPlainTextEdit {
#                 border: 2px solid #bdc3c7;
#                 border-radius: 8px;
#                 padding: 10px;
#                 font-size: 12px;
#                 line-height: 1.4;
#                 background-color: #f8f9fa;
#             }
#         """)
#         layout.addWidget(self.text_edit)
#         
#         # ボタンレイアウト
#         button_layout = QHBoxLayout()
#         button_layout.setSpacing(10)
#         
#         # コピーボタン
#         copy_button = QPushButton("コピー")
#         copy_button.setStyleSheet("""
#             QPushButton {
#                 background-color: #3498db;
#                 color: white;
#                 border: none;
#                 padding: 8px 16px;
#                 border-radius: 6px;
#                 font-weight: bold;
#             }
#             QPushButton:hover {
#                 background-color: #2980b9;
#             }
#             QPushButton:pressed {
#                 background-color: #21618c;
#             }
#         """)
#         copy_button.clicked.connect(self._copy_text)
#         button_layout.addWidget(copy_button)
#         
#         # クリアボタン
#         clear_button = QPushButton("クリア")
#         clear_button.setStyleSheet("""
#             QPushButton {
#                 background-color: #e74c3c;
#                 color: white;
#                 border: none;
#                 padding: 8px 16px;
#                 border-radius: 6px;
#                 font-weight: bold;
#             }
#             QPushButton:hover {
#                 background-color: #c0392b;
#             }
#             QPushButton:pressed {
#                 background-color: #a93226;
#             }
#         """)
#         clear_button.clicked.connect(self._clear_text)
#         button_layout.addWidget(clear_button)
#         
#         # 閉じるボタン
#         close_button = QPushButton("閉じる")
#         close_button.setStyleSheet("""
#             QPushButton {
#                 background-color: #95a5a6;
#                 color: white;
#                 border: none;
#                 padding: 8px 16px;
#                 border-radius: 6px;
#                 font-weight: bold;
#             }
#             QPushButton:hover {
#                 background-color: #7f8c8d;
#             }
#             QPushButton:pressed {
#                 background-color: #6c7b7d;
#             }
#         """)
#         close_button.clicked.connect(self.close)
#         button_layout.addWidget(close_button)
#         
#         layout.addLayout(button_layout)
#         self.setLayout(layout)
#     
#     def append_text(self, text: str) -> None:
#         """テキストを追記"""
#         current_text = self.text_edit.toPlainText()
#         if current_text:
#             new_text = current_text + " " + text
#         else:
#             new_text = text
#         self.text_edit.setPlainText(new_text)
#         
#         # 最後にスクロール
#         cursor = self.text_edit.textCursor()
#         cursor.movePosition(cursor.MoveOperation.End)
#         self.text_edit.setTextCursor(cursor)
#         self.text_edit.ensureCursorVisible()
#     
#     def _copy_text(self) -> None:
#         """テキストをクリップボードにコピー"""
#         text = self.text_edit.toPlainText()
#         if text:
#             pyperclip.copy(text)
#     
#     def _clear_text(self) -> None:
#         """テキストをクリア"""
#         self.text_edit.clear()


class TranscriptionResultDialog(QDialog):
    """改善された文字起こし結果表示・編集ダイアログ"""

    def __init__(self, text: str, parent=None) -> None:
        """
        文字起こし結果ダイアログの初期化

        Args:
            text: 表示するテキスト
            parent: 親ウィジェット
        """
        super().__init__(parent)
        self.setWindowTitle("文字起こし結果 - 編集・コピー可能")
        self.setMinimumSize(480, 320)
        self.resize(480, 320)
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.Tool)

        # メインレイアウト
        main_layout = QVBoxLayout()
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(16, 16, 16, 16)

        # ヘッダー
        header_layout = QHBoxLayout()
        title_label = QLabel("📝 文字起こし結果")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 14pt;
                font-weight: bold;
                color: #2d3748;
                margin-bottom: 8px;
            }
        """)
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        # 自動閉じるタイマー制御
        self.auto_close_enabled = True
        self.remaining_time = 10
        self.timer_label = QLabel(f"⏰ {self.remaining_time}秒後に自動で閉じます")
        self.timer_label.setStyleSheet("""
            QLabel {
                font-size: 9pt;
                color: #718096;
                background-color: #f7fafc;
                padding: 4px 8px;
                border-radius: 4px;
            }
        """)
        header_layout.addWidget(self.timer_label)

        main_layout.addLayout(header_layout)

        # テキスト編集エリア
        self.text_edit = QPlainTextEdit()
        self.text_edit.setPlainText(text)
        self.text_edit.setStyleSheet("""
            QPlainTextEdit {
                font-size: 12pt;
                font-family: 'Yu Gothic UI', 'Meiryo UI', sans-serif;
                background-color: #ffffff;
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                padding: 12px;
                line-height: 1.5;
            }
            QPlainTextEdit:focus {
                border-color: #4299e1;
                outline: none;
            }
        """)

        # テキスト変更時のイベント接続
        self.text_edit.textChanged.connect(self._on_text_changed)

        main_layout.addWidget(self.text_edit)

        # ボタンエリア
        button_frame = QFrame()
        button_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border-radius: 8px;
                padding: 8px;
            }
        """)
        button_layout = QHBoxLayout(button_frame)
        button_layout.setSpacing(8)

        # 情報ラベル
        self.info_label = QLabel("✅ 自動的にクリップボードにコピーされました")
        self.info_label.setStyleSheet("""
            QLabel {
                color: #38a169;
                font-size: 10pt;
                font-weight: 500;
            }
        """)
        button_layout.addWidget(self.info_label)
        button_layout.addStretch()

        # コピーボタン
        self.copy_button = QPushButton("📋 コピー")
        self.copy_button.clicked.connect(self._copy_text)
        self.copy_button.setStyleSheet("""
            QPushButton {
                background-color: #4299e1;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 10pt;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #3182ce;
            }
            QPushButton:pressed {
                background-color: #2c5282;
            }
        """)
        button_layout.addWidget(self.copy_button)

        # クリアボタン
        self.clear_button = QPushButton("🗑️ クリア")
        self.clear_button.clicked.connect(self._clear_text)
        self.clear_button.setStyleSheet("""
            QPushButton {
                background-color: #e53e3e;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 10pt;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #c53030;
            }
            QPushButton:pressed {
                background-color: #9c2626;
            }
        """)
        button_layout.addWidget(self.clear_button)

        # 閉じるボタン
        self.close_button = QPushButton("❌ 閉じる")
        self.close_button.clicked.connect(self.close)
        self.close_button.setStyleSheet("""
            QPushButton {
                background-color: #718096;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 10pt;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #4a5568;
            }
            QPushButton:pressed {
                background-color: #2d3748;
            }
        """)
        button_layout.addWidget(self.close_button)

        main_layout.addWidget(button_frame)
        self.setLayout(main_layout)

        # 自動クローズタイマー
        self.auto_close_timer = QTimer()
        self.auto_close_timer.timeout.connect(self._update_timer)
        self.auto_close_timer.start(1000)  # 1秒間隔

        # 初期フォーカスをテキストエリアに
        self.text_edit.setFocus()

        # テキストを選択状態にする
        self.text_edit.selectAll()

    def _on_text_changed(self) -> None:
        """テキスト変更時の処理"""
        # テキストが編集されたら自動閉じるを無効化
        if self.auto_close_enabled:
            self.auto_close_enabled = False
            self.timer_label.setText("✏️ 編集中 - 自動閉じるを停止")
            self.timer_label.setStyleSheet("""
                QLabel {
                    font-size: 9pt;
                    color: #d69e2e;
                    background-color: #fef5e7;
                    padding: 4px 8px;
                    border-radius: 4px;
                }
            """)

    def _copy_text(self) -> None:
        """テキストをクリップボードにコピー"""
        try:
            text = self.text_edit.toPlainText()
            pyperclip.copy(text)
            self.info_label.setText("✅ クリップボードにコピーしました")
            self.info_label.setStyleSheet("""
                QLabel {
                    color: #38a169;
                    font-size: 10pt;
                    font-weight: 500;
                }
            """)

            # 2秒後に元のメッセージに戻す
            QTimer.singleShot(
                2000, lambda: self.info_label.setText("💡 テキストを編集できます")
            )

        except Exception as e:
            self.info_label.setText(f"❌ コピーに失敗: {str(e)}")
            self.info_label.setStyleSheet("""
                QLabel {
                    color: #e53e3e;
                    font-size: 10pt;
                    font-weight: 500;
                }
            """)

    def _clear_text(self) -> None:
        """テキストをクリア"""
        self.text_edit.clear()
        self.info_label.setText("🗑️ テキストをクリアしました")
        self.info_label.setStyleSheet("""
            QLabel {
                color: #d69e2e;
                font-size: 10pt;
                font-weight: 500;
            }
        """)

    def _update_timer(self) -> None:
        """タイマーを更新"""
        if not self.auto_close_enabled:
            return

        self.remaining_time -= 1
        if self.remaining_time <= 0:
            self.close()
        else:
            self.timer_label.setText(f"⏰ {self.remaining_time}秒後に自動で閉じます")

    def keyPressEvent(self, event) -> None:
        """キーボードイベント処理"""
        # Ctrl+C でコピー
        if event.key() == Qt.Key_C and event.modifiers() == Qt.ControlModifier:
            self._copy_text()
        # Escape で閉じる
        elif event.key() == Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)


class MainWindow(QMainWindow):
    """メインウィンドウクラス"""

    # シグナル定義
    mic_button_clicked = Signal()
    model_changed = Signal(str)  # モデル変更（"large-v3" または "large-v3-turbo"）

    def __init__(self) -> None:
        """メインウィンドウの初期化"""
        super().__init__()
        self.logger = logging.getLogger(__name__)

        # ウィンドウ設定
        self.setWindowTitle("Whisper Voice MVP")
        self.setFixedSize(140, 160)  # 切り替えボタンのためにサイズ拡大
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool)
        
        # 透過背景を有効化
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # ウィンドウ全体の透明度は設定しない（背景のみ透過）

        # 中央ウィジェットとレイアウト
        central_widget = QWidget()
        central_widget.setStyleSheet("background-color: transparent;")  # 背景を透明に
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setAlignment(Qt.AlignCenter)
        
        # モデル切り替えボタン（v3 ⇔ v3-turbo）
        self.model_toggle_button = QPushButton("v3")
        self.model_toggle_button.setFixedSize(80, 25)
        self.model_toggle_button.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                border-radius: 12px;
                font-size: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:pressed {
                background-color: #1e8449;
            }
        """)
        self.model_toggle_button.clicked.connect(self._toggle_model)
        layout.addWidget(self.model_toggle_button, alignment=Qt.AlignCenter)
        
        # 現在のモデル（デフォルトはlarge-v3）
        self.current_model = "large-v3"

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
    
    def _toggle_model(self) -> None:
        """Whisperモデル切り替え（v3 ⇔ v3-turbo）"""
        if self.current_model == "large-v3":
            self.current_model = "large-v3-turbo"
            self.model_toggle_button.setText("turbo")
            self.model_toggle_button.setStyleSheet("""
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
        else:
            self.current_model = "large-v3"
            self.model_toggle_button.setText("v3")
            self.model_toggle_button.setStyleSheet("""
                QPushButton {
                    background-color: #27ae60;
                    color: white;
                    border: none;
                    border-radius: 12px;
                    font-size: 10px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #229954;
                }
                QPushButton:pressed {
                    background-color: #1e8449;
                }
            """)
        
        self.logger.info(f"モデル切り替え: {self.current_model}")
        self.model_changed.emit(self.current_model)

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
    
    # リアルタイム機能は一時保留
    # def show_partial_transcription_result(self, partial_text: str) -> None:
    #     """
    #     部分的な文字起こし結果を表示（リアルタイム用）
    #
    #     Args:
    #         partial_text: 部分的な文字起こし結果のテキスト
    #     """
    #     if not partial_text.strip():
    #         return
    #
    #     # 既存のダイアログがあれば追記、なければ新規作成
    #     if hasattr(self, '_realtime_dialog') and self._realtime_dialog and self._realtime_dialog.isVisible():
    #         self._realtime_dialog.append_text(partial_text)
    #     else:
    #         self._realtime_dialog = RealtimeTranscriptionDialog(partial_text, self)
    #         # ダイアログをメインウィンドウの近くに配置
    #         dialog_x = self.x() - self._realtime_dialog.width() - 10
    #         dialog_y = self.y()
    #         if dialog_x < 0:
    #             dialog_x = self.x() + self.width() + 10
    #         self._realtime_dialog.move(dialog_x, dialog_y)
    #         self._realtime_dialog.show()
    #
    #     # 既存のダイアログがある場合のみ位置調整
    #     if hasattr(self, '_realtime_dialog') and self._realtime_dialog:
    #         # 画面外に出る場合は調整
    #         screen = QApplication.primaryScreen()
    #         screen_geometry = screen.availableGeometry()
    #         
    #         current_x = self._realtime_dialog.x()
    #         current_y = self._realtime_dialog.y()
    #         
    #         if current_x < 0:
    #             current_x = self.x() + self.width() + 10
    #         if current_y + self._realtime_dialog.height() > screen_geometry.height():
    #             current_y = screen_geometry.height() - self._realtime_dialog.height() - 20
    #         
    #         self._realtime_dialog.move(current_x, current_y)

    def mousePressEvent(self, event) -> None:
        """マウスプレスイベント（ウィンドウドラッグ用）"""
        if event.button() == Qt.LeftButton:
            self.drag_position = (
                event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            )
            event.accept()

    def mouseMoveEvent(self, event) -> None:
        """マウス移動イベント（ウィンドウドラッグ用）"""
        if event.buttons() == Qt.LeftButton and hasattr(self, "drag_position"):
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def closeEvent(self, event) -> None:
        """ウィンドウクローズイベント"""
        self.logger.info("メインウィンドウを閉じています...")
        event.accept()
