"""
音声処理モジュール

マイクからの音声入力を処理し、録音機能を提供します。
"""

import logging
import threading
import time
from typing import Callable, Optional, List
import queue

import numpy as np
import sounddevice as sd
from PySide6.QtCore import QObject, Signal

from utils.logger_config import get_logger, LogLevel, ErrorCode


class AudioProcessor(QObject):
    """音声処理クラス"""
    
    # シグナル定義
    recording_started = Signal()
    recording_stopped = Signal()
    audio_data_ready = Signal(np.ndarray)  # 録音完了時に音声データを送信
    error_occurred = Signal(str)
    
    def __init__(self, sample_rate: int = 16000, channels: int = 1) -> None:
        """
        音声処理クラスの初期化
        
        Args:
            sample_rate: サンプリングレート (Hz)
            channels: チャンネル数（1=モノラル、2=ステレオ）
        """
        super().__init__()
        self.sample_rate = sample_rate
        self.channels = channels
        self.is_recording = False
        self.audio_buffer: List[np.ndarray] = []
        self.audio_queue: queue.Queue = queue.Queue()
        self.recording_thread: Optional[threading.Thread] = None
        
        # 統合ログシステム
        self.app_logger = get_logger()
        
        # 従来のロギング設定（互換性維持）
        self.logger = logging.getLogger(__name__)
        
        # デフォルトマイクデバイスの設定
        self._setup_audio_device()
    
    def _setup_audio_device(self) -> None:
        """音声デバイスのセットアップ"""
        try:
            self.app_logger.debug("AudioProcessor", "音声デバイスの初期化を開始")
            
            # デフォルトの入力デバイスを取得
            try:
                default_device = sd.default.device[0]  # 入力デバイス
                device_info = sd.query_devices(default_device)
            except (OSError, ValueError) as e:
                self.app_logger.error(
                    "AudioProcessor", 
                    "デフォルト音声デバイスの取得に失敗",
                    error_code=ErrorCode.AUDIO_DEVICE_NOT_FOUND,
                    exception=e,
                    context={"sample_rate": self.sample_rate, "channels": self.channels}
                )
                raise
            
            self.app_logger.info(
                "AudioProcessor", 
                f"使用する音声デバイス: {device_info['name']}",
                context={
                    "device_name": device_info['name'],
                    "max_input_channels": device_info['max_input_channels'],
                    "default_samplerate": device_info['default_samplerate']
                }
            )
            
            self.logger.info(f"使用する音声デバイス: {device_info['name']}")
            self.logger.info(f"最大入力チャンネル数: {device_info['max_input_channels']}")
            
            # チャンネル数の調整
            if device_info['max_input_channels'] < self.channels:
                original_channels = self.channels
                self.channels = int(device_info['max_input_channels'])
                self.app_logger.warning(
                    "AudioProcessor", 
                    f"チャンネル数を {original_channels} から {self.channels} に調整しました",
                    context={
                        "original_channels": original_channels,
                        "adjusted_channels": self.channels,
                        "device_max_channels": device_info['max_input_channels']
                    }
                )
                self.logger.warning(f"チャンネル数を {self.channels} に調整しました")
            
            self.app_logger.info("AudioProcessor", "音声デバイスの初期化が完了")
                
        except Exception as e:
            error_msg = f"音声デバイスの設定に失敗しました: {str(e)}"
            self.app_logger.error(
                "AudioProcessor", 
                error_msg,
                error_code=ErrorCode.AUDIO_DEVICE_NOT_FOUND,
                exception=e
            )
            self.logger.error(error_msg)
            self.error_occurred.emit(error_msg)
    
    def verify_microphone_access(self, duration_seconds: float = 0.2) -> bool:
        """
        マイクアクセスの検証を行う
        
        Args:
            duration_seconds: ストリームを開いて確認する時間
        
        Returns:
            bool: アクセス可能かどうか
        """
        try:
            self.app_logger.info(
                "AudioProcessor",
                "マイクアクセス検証を開始",
                context={"sample_rate": self.sample_rate, "channels": self.channels}
            )
            import sounddevice as sd
            import numpy as np
            import time
            
            # 短時間だけ入力ストリームを開いてアクセス権と占有状態を確認
            with sd.InputStream(
                channels=self.channels,
                samplerate=self.sample_rate,
                dtype=np.float32,
                blocksize=1024,
                callback=lambda *args, **kwargs: None
            ):
                time.sleep(max(0.05, duration_seconds))
            
            self.app_logger.info("AudioProcessor", "マイクアクセス検証に成功しました")
            self.logger.info("マイクアクセス検証: 成功")
            return True
        except Exception as e:
            error_text = str(e)
            error_lower = error_text.lower()
            if "denied" in error_lower or "permission" in error_lower or "access" in error_lower:
                error_code = ErrorCode.AUDIO_PERMISSION_DENIED
                user_msg = "マイクへのアクセスが拒否されました。Windowsのマイク権限を確認してください。"
            elif "busy" in error_lower or "in use" in error_lower or "unavailable" in error_lower:
                error_code = ErrorCode.AUDIO_DEVICE_BUSY
                user_msg = "マイクデバイスが使用中です。他のアプリを閉じてください。"
            else:
                error_code = ErrorCode.AUDIO_RECORDING_ERROR
                user_msg = f"マイクアクセス検証に失敗: {error_text}"
            
            self.app_logger.error(
                "AudioProcessor",
                user_msg,
                error_code=error_code,
                exception=e
            )
            self.logger.error(user_msg)
            return False

    def _audio_callback(self, indata: np.ndarray, frames: int, time_info, status) -> None:
        """
        音声入力コールバック関数
        
        Args:
            indata: 入力音声データ
            frames: フレーム数
            time_info: 時間情報
            status: ステータス
        """
        if status:
            self.logger.warning(f"音声入力ステータス: {status}")
        
        if self.is_recording:
            # 音声データをキューに追加
            self.audio_queue.put(indata.copy())
    
    def start_recording(self) -> bool:
        """
        録音開始
        
        Returns:
            bool: 開始成功可否
        """
        if self.is_recording:
            self.app_logger.warning("AudioProcessor", "既に録音中です")
            self.logger.warning("既に録音中です")
            return False
        
        try:
            self.app_logger.info("AudioProcessor", "録音開始を試みます")
            
            self.is_recording = True
            self.audio_buffer.clear()
            
            # 録音用スレッドを開始
            self.recording_thread = threading.Thread(target=self._recording_worker)
            self.recording_thread.daemon = True
            self.recording_thread.start()
            
            self.app_logger.info(
                "AudioProcessor", 
                "録音を開始しました",
                context={
                    "sample_rate": self.sample_rate,
                    "channels": self.channels,
                    "thread_id": self.recording_thread.ident
                }
            )
            self.logger.info("録音を開始しました")
            self.recording_started.emit()
            return True
            
        except Exception as e:
            error_msg = f"録音開始に失敗しました: {str(e)}"
            self.app_logger.error(
                "AudioProcessor", 
                error_msg,
                error_code=ErrorCode.AUDIO_RECORDING_ERROR,
                exception=e
            )
            self.logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            self.is_recording = False
            return False
    
    def stop_recording(self) -> None:
        """録音停止"""
        if not self.is_recording:
            self.logger.warning("録音中ではありません")
            return
        
        self.is_recording = False
        
        # 録音スレッドの終了を待機
        if self.recording_thread and self.recording_thread.is_alive():
            self.recording_thread.join(timeout=2.0)
        
        # バッファにある音声データを結合
        if self.audio_buffer:
            combined_audio = np.concatenate(self.audio_buffer, axis=0)
            self.logger.info(f"録音データ長: {len(combined_audio) / self.sample_rate:.2f}秒")
            self.audio_data_ready.emit(combined_audio)
        else:
            self.logger.warning("録音データがありません")
        
        self.logger.info("録音を停止しました")
        self.recording_stopped.emit()
    
    def _recording_worker(self) -> None:
        """録音処理のワーカースレッド"""
        try:
            with sd.InputStream(
                channels=self.channels,
                samplerate=self.sample_rate,
                callback=self._audio_callback,
                blocksize=1024,
                dtype=np.float32
            ):
                self.logger.info("音声ストリーム開始")
                
                while self.is_recording:
                    try:
                        # キューから音声データを取得
                        audio_chunk = self.audio_queue.get(timeout=0.1)
                        self.audio_buffer.append(audio_chunk)
                    except queue.Empty:
                        continue
                    
        except Exception as e:
            error_msg = f"録音処理でエラーが発生しました: {str(e)}"
            self.logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            self.is_recording = False
    
    def get_audio_devices(self) -> List[dict]:
        """
        利用可能な音声入力デバイスの一覧を取得
        
        Returns:
            List[dict]: デバイス情報のリスト
        """
        devices = []
        try:
            device_list = sd.query_devices()
            for i, device in enumerate(device_list):
                if device['max_input_channels'] > 0:  # 入力可能なデバイスのみ
                    devices.append({
                        'id': i,
                        'name': device['name'],
                        'channels': device['max_input_channels'],
                        'sample_rate': device['default_samplerate']
                    })
        except Exception as e:
            self.logger.error(f"デバイス一覧取得エラー: {str(e)}")
        
        return devices
    
    def is_recording_active(self) -> bool:
        """
        録音状態の確認
        
        Returns:
            bool: 録音中かどうか
        """
        return self.is_recording
    
    def get_sample_rate(self) -> int:
        """
        サンプリングレートを取得
        
        Returns:
            int: サンプリングレート
        """
        return self.sample_rate