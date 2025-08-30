"""
Whisper文字起こしエンジンモジュール

faster-whisperを使用してローカルでの音声文字起こしを実行します。
"""

import logging
import threading
import tempfile
import os
from typing import Optional, Generator, Tuple
import time

import numpy as np
from faster_whisper import WhisperModel
from PySide6.QtCore import QObject, Signal
import soundfile as sf

from utils.logger_config import get_logger, LogLevel, ErrorCode


class TranscriptionEngine(QObject):
    """Whisper文字起こしエンジンクラス"""
    
    # シグナル定義
    transcription_started = Signal()
    transcription_completed = Signal(str)  # 文字起こし結果を送信
    transcription_failed = Signal(str)     # エラーメッセージを送信
    model_loading_started = Signal()
    model_loading_completed = Signal()
    # リアルタイム文字起こし用シグナル（一時保留）
    # partial_transcription = Signal(str)    # 部分的な文字起こし結果
    
    def __init__(self, model_size: str = "large-v3-turbo", device: str = "cpu", fallback_models: list = None) -> None:
        """
        文字起こしエンジンの初期化
        
        Args:
            model_size: Whisperモデルのサイズ ("large-v3", "medium", "small" など)
            device: 実行デバイス ("cpu", "cuda")
            fallback_models: メインモデルが失敗した場合の代替モデルリスト
        """
        super().__init__()
        self.model_size = model_size
        self.device = device
        # フォールバックモデル（未指定時はデフォルトの順序を採用）
        if fallback_models is None:
            if model_size == "large-v3-turbo":
                # デフォルトは turbo。ロードに失敗した場合は精度重視の large-v3 を試し、その後に軽量モデルへフォールバック
                self.fallback_models = ["large-v3", "medium", "small", "base"]
            else:
                self.fallback_models = ["medium", "small", "base"]
        else:
            self.fallback_models = fallback_models
        self.current_model_size = model_size  # 実際にロードされたモデルサイズ
        self.model: Optional[WhisperModel] = None
        self.is_loading = False
        self.is_processing = False
        
        # リアルタイム処理設定（一時保留）
        # self.realtime_mode = realtime_mode
        # self.chunk_duration = 3.0  # チャンクの長さ（秒）
        # self.overlap_duration = 0.5  # オーバーラップの長さ（秒）
        
        # 統合ログシステム
        self.app_logger = get_logger()
        
        # 従来のロギング設定（互換性維持）
        self.logger = logging.getLogger(__name__)
        
        # モデルの初期化（バックグラウンドで実行）
        self._initialize_model_async()
    
    def _initialize_model_async(self) -> None:
        """モデルの非同期初期化"""
        def load_model():
            model_to_try = [self.model_size] + self.fallback_models
            
            for attempt, model_size in enumerate(model_to_try):
                try:
                    self.is_loading = True
                    self.model_loading_started.emit()
                    
                    if attempt > 0:
                        self.app_logger.warning(
                            "TranscriptionEngine", 
                            f"メインモデル '{self.model_size}' のロードに失敗。代替モデル '{model_size}' を試行",
                            context={"original_model": self.model_size, "fallback_model": model_size, "attempt": attempt}
                        )
                        self.logger.warning(f"メインモデル '{self.model_size}' のロードに失敗。代替モデル '{model_size}' を試行中...")
                    
                    self.app_logger.info(
                        "TranscriptionEngine", 
                        f"Whisperモデル '{model_size}' のロードを開始",
                        context={"model_size": model_size, "device": self.device, "attempt": attempt + 1}
                    )
                    self.logger.info(f"Whisperモデル '{model_size}' をロード中...")
                    
                    # モデルダウンロードのタイムアウト設定
                    import socket
                    socket.setdefaulttimeout(60)  # 60秒タイムアウト
                    
                    start_time = time.time()
                    
                    # faster-whisperモデルの初期化
                    self.app_logger.debug("TranscriptionEngine", f"WhisperModel '{model_size}' を初期化中...")
                    
                    self.model = WhisperModel(
                        model_size,
                        device=self.device,
                        compute_type="float32" if self.device == "cpu" else "float16",
                        download_root=None,  # デフォルトのキャッシュディレクトリを使用
                    )
                    
                    # 成功した場合の処理
                    self.current_model_size = model_size
                    load_time = time.time() - start_time
                    
                    success_msg = f"Whisperモデル '{model_size}' のロードが完了 (時間: {load_time:.2f}秒)"
                    if attempt > 0:
                        success_msg += f" (代替モデルとして使用)"
                    
                    self.app_logger.info(
                        "TranscriptionEngine", 
                        success_msg,
                        context={
                            "load_time_seconds": load_time, 
                            "model_size": model_size,
                            "original_model": self.model_size,
                            "is_fallback": attempt > 0
                        }
                    )
                    self.logger.info(success_msg)
                    self.model_loading_completed.emit()
                    return  # 成功したので終了
                    
                except Exception as model_error:
                    # モデルロード固有のエラー処理
                    if "timeout" in str(model_error).lower():
                        error_msg = f"モデル '{model_size}' のダウンロードがタイムアウトしました"
                        error_code = ErrorCode.NETWORK_TIMEOUT_ERROR
                    elif "connection" in str(model_error).lower():
                        error_msg = f"モデル '{model_size}' のダウンロードでネットワーク接続エラー"
                        error_code = ErrorCode.NETWORK_CONNECTION_ERROR
                    else:
                        error_msg = f"モデル '{model_size}' のロードに失敗: {str(model_error)}"
                        error_code = ErrorCode.WHISPER_MODEL_LOAD_ERROR
                    
                    self.app_logger.warning(
                        "TranscriptionEngine", 
                        error_msg,
                        error_code=error_code,
                        exception=model_error,
                        context={"model_size": model_size, "attempt": attempt + 1}
                    )
                    self.logger.warning(error_msg)
                    
                    # 最後の試行の場合はエラーを発生
                    if attempt == len(model_to_try) - 1:
                        final_error_msg = f"すべてのモデル ({', '.join(model_to_try)}) のロードに失敗しました。インターネット接続を確認してください。"
                        self.app_logger.critical(
                            "TranscriptionEngine", 
                            final_error_msg,
                            error_code=ErrorCode.WHISPER_MODEL_LOAD_ERROR,
                            exception=model_error
                        )
                        self.logger.error(final_error_msg)
                        self.transcription_failed.emit(final_error_msg)
                    
                    # 次のモデルを試す
                    continue
                finally:
                    self.is_loading = False
        
        # バックグラウンドスレッドでモデルをロード
        thread = threading.Thread(target=load_model)
        thread.daemon = True
        thread.start()
    
    def transcribe_audio(self, audio_data: np.ndarray, sample_rate: int = 16000) -> None:
        """
        音声データの文字起こしを実行（非同期）
        
        Args:
            audio_data: 音声データ（numpy配列）
            sample_rate: サンプリングレート
        """
        if self.is_processing:
            self.logger.warning("既に文字起こし処理中です")
            return
        
        if self.is_loading:
            self.logger.warning("モデルロード中です。しばらくお待ちください")
            return
        
        if self.model is None:
            error_msg = "Whisperモデルが初期化されていません"
            self.logger.error(error_msg)
            self.transcription_failed.emit(error_msg)
            return
        
        # バックグラウンドで文字起こしを実行
        thread = threading.Thread(
            target=self._transcribe_worker,
            args=(audio_data, sample_rate)
        )
        thread.daemon = True
        thread.start()
    
    # リアルタイム機能は一時保留 - 全体をコメントアウト
    # def transcribe_audio_realtime(self, audio_data: np.ndarray, sample_rate: int = 16000) -> None:
    #     """
    #     リアルタイム音声データの文字起こしを実行（チャンク分割処理）
    #     
    #     Args:
    #         audio_data: 音声データ（numpy配列）
    #         sample_rate: サンプリングレート
    #     """
    #     if self.is_processing:
    #         self.app_logger.warning("TranscriptionEngine", "既に文字起こし処理中です")
    #         return
    #     
    #     if self.model is None:
    #         self.app_logger.error("TranscriptionEngine", "Whisperモデルがロードされていません")
    #         self.transcription_failed.emit("モデルが初期化されていません")
    #         return
    #     
    #     # バックグラウンドでリアルタイム処理を実行
    #     def realtime_worker():
    #         self._transcribe_realtime_worker(audio_data, sample_rate)
    #     
    #     thread = threading.Thread(target=realtime_worker)
    #     thread.daemon = True
    #     thread.start()
    # 
    # def _transcribe_realtime_worker(self, audio_data: np.ndarray, sample_rate: int) -> None:
    #     """
    #     リアルタイム文字起こしのワーカー（チャンク分割処理）
    #     
    #     Args:
    #         audio_data: 音声データ
    #         sample_rate: サンプリングレート
    #     """
    #     self.is_processing = True
    #     self.transcription_started.emit()
    #     
    #     try:
    #         chunk_samples = int(self.chunk_duration * sample_rate)
    #         overlap_samples = int(self.overlap_duration * sample_rate)
    #         
    #         # 音声データをチャンクに分割
    #         chunks = []
    #         for i in range(0, len(audio_data), chunk_samples - overlap_samples):
    #             chunk = audio_data[i:i + chunk_samples]
    #             if len(chunk) > overlap_samples:  # 最小チャンクサイズ
    #                 chunks.append(chunk)
    #         
    #         self.app_logger.info("TranscriptionEngine", f"音声を{len(chunks)}個のチャンクに分割しました")
    #         
    #         # 各チャンクを並列処理
    #         full_transcription = ""
    #         for i, chunk in enumerate(chunks):
    #             try:
    #                 # 一時ファイルに保存
    #                 with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
    #                     temp_path = temp_file.name
    #                     sf.write(temp_path, chunk, sample_rate)
    #                 
    #                 # Whisperで文字起こし（高速設定）
    #                 segments, info = self.model.transcribe(
    #                     temp_path,
    #                     language="ja",
    #                     beam_size=1,  # リアルタイム用に高速化
    #                     best_of=1,    # リアルタイム用に高速化
    #                     temperature=0.0,
    #                     vad_filter=True,
    #                     vad_parameters=dict(min_silence_duration_ms=300)  # より短い無音期間
    #                 )
    #                 
    #                 # セグメントからテキストを抽出
    #                 chunk_text = ""
    #                 for segment in segments:
    #                     chunk_text += segment.text.strip() + " "
    #                 
    #                 chunk_text = chunk_text.strip()
    #                 if chunk_text:
    #                     full_transcription += chunk_text + " "
    #                     # 部分的な結果を送信
    #                     self.partial_transcription.emit(chunk_text)
    #                     self.app_logger.info("TranscriptionEngine", f"チャンク {i+1}/{len(chunks)}: {chunk_text[:50]}...")
    #                 
    #                 # 一時ファイルを削除
    #                 os.unlink(temp_path)
    #                 
    #             except Exception as e:
    #                 self.app_logger.error("TranscriptionEngine", f"チャンク {i+1} の処理に失敗: {e}")
    #                 continue
    #         
    #         # 最終結果を送信
    #         final_text = full_transcription.strip()
    #         if final_text:
    #             self.app_logger.info("TranscriptionEngine", f"リアルタイム文字起こし完了: {final_text[:100]}...")
    #             self.transcription_completed.emit(final_text)
    #         else:
    #             self.app_logger.warning("TranscriptionEngine", "音声を認識できませんでした")
    #             self.transcription_completed.emit("[音声を認識できませんでした]")
    #         
    #     except Exception as e:
    #         error_msg = f"リアルタイム文字起こし処理でエラーが発生しました: {str(e)}"
    #         self.app_logger.error("TranscriptionEngine", error_msg, exception=e)
    #         self.transcription_failed.emit(error_msg)
    #     finally:
    #         self.is_processing = False
    
    def _transcribe_worker(self, audio_data: np.ndarray, sample_rate: int) -> None:
        """文字起こし処理のワーカースレッド"""
        try:
            self.is_processing = True
            self.transcription_started.emit()
            self.logger.info("文字起こし処理を開始します")
            
            start_time = time.time()
            
            # 音声データの前処理
            processed_audio = self._preprocess_audio(audio_data, sample_rate)
            
            # 一時ファイルとして保存
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_path = temp_file.name
                sf.write(temp_path, processed_audio, sample_rate)
            
            try:
                # Whisperによる文字起こし
                segments, info = self.model.transcribe(
                    temp_path,
                    language="ja",  # 日本語
                    beam_size=5,
                    best_of=5,
                    temperature=0.0,
                    vad_filter=True,  # 音声活動検出
                    vad_parameters=dict(min_silence_duration_ms=500)
                )
                
                # セグメントからテキストを抽出
                transcribed_text = ""
                for segment in segments:
                    transcribed_text += segment.text.strip() + " "
                
                transcribed_text = transcribed_text.strip()
                
                # 処理時間を計算
                processing_time = time.time() - start_time
                self.logger.info(f"文字起こし完了 (処理時間: {processing_time:.2f}秒)")
                self.logger.info(f"認識言語: {info.language} (確度: {info.language_probability:.2f})")
                
                if transcribed_text:
                    self.logger.info(f"文字起こし結果: {transcribed_text[:100]}...")
                    self.transcription_completed.emit(transcribed_text)
                else:
                    self.logger.warning("音声を認識できませんでした")
                    self.transcription_completed.emit("[音声を認識できませんでした]")
                    
            finally:
                # 一時ファイルを削除
                try:
                    os.unlink(temp_path)
                except OSError:
                    pass
                    
        except Exception as e:
            # エラーの詳細分析
            error_type = type(e).__name__
            error_str = str(e)
            
            # ONNXファイル関連エラー
            if "silero_encoder" in error_str or "silero_decoder" in error_str:
                error_msg = (
                    "文字起こしエンジンのONNXファイルが見つかりません。\n"
                    "アプリケーションの再インストールが必要です。\n"
                    f"エラー詳細: {error_str}"
                )
                error_code = ErrorCode.WHISPER_MODEL_LOAD_ERROR
            # 音声データの問題
            elif len(processed_audio) == 0:
                error_msg = (
                    "音声データが空です。\n"
                    "マイクが正しく接続されているか、音声が入力されているか確認してください。"
                )
                error_code = ErrorCode.AUDIO_INPUT_ERROR
            # ファイルI/Oエラー
            elif "permission" in error_str.lower() or "access" in error_str.lower():
                error_msg = (
                    "一時ファイルの作成に失敗しました。\n"
                    "アプリケーションを管理者権限で実行してください。"
                )
                error_code = ErrorCode.SYSTEM_PERMISSION_ERROR
            # メモリ不足
            elif "memory" in error_str.lower() or "allocation" in error_str.lower():
                error_msg = (
                    "メモリ不足のため文字起こしに失敗しました。\n"
                    "他のアプリケーションを終了して再試行してください。"
                )
                error_code = ErrorCode.SYSTEM_MEMORY_ERROR
            # その他のエラー
            else:
                error_msg = (
                    f"文字起こし処理で予期しないエラーが発生しました。\n"
                    f"エラータイプ: {error_type}\n"
                    f"エラー詳細: {error_str}\n\n"
                    "解決策:\n"
                    "1. アプリケーションを再起動してください\n"
                    "2. マイクの接続を確認してください\n"
                    "3. 音声が十分な音量で入力されているか確認してください"
                )
                error_code = ErrorCode.TRANSCRIPTION_PROCESSING_ERROR
            
            # ログ出力
            self.app_logger.error(
                "TranscriptionEngine", 
                error_msg,
                error_code=error_code,
                exception=e,
                context={
                    "audio_length": len(audio_data),
                    "sample_rate": sample_rate,
                    "processed_audio_length": len(processed_audio) if 'processed_audio' in locals() else 0,
                    "error_type": error_type
                }
            )
            self.logger.error(error_msg)
            self.transcription_failed.emit(error_msg)
        finally:
            self.is_processing = False
    
    def _preprocess_audio(self, audio_data: np.ndarray, sample_rate: int) -> np.ndarray:
        """
        音声データの前処理
        
        Args:
            audio_data: 入力音声データ
            sample_rate: サンプリングレート
            
        Returns:
            np.ndarray: 前処理済み音声データ
        """
        # ステレオからモノラルに変換（必要に応じて）
        if len(audio_data.shape) > 1 and audio_data.shape[1] > 1:
            audio_data = np.mean(audio_data, axis=1)
        
        # 音量の正規化
        if np.max(np.abs(audio_data)) > 0:
            audio_data = audio_data / np.max(np.abs(audio_data)) * 0.8
        
        # 無音部分のトリミング
        audio_data = self._trim_silence(audio_data, sample_rate)
        
        return audio_data
    
    def _trim_silence(self, audio_data: np.ndarray, sample_rate: int, 
                     threshold: float = 0.01, margin_seconds: float = 0.1) -> np.ndarray:
        """
        音声データから無音部分をトリミング
        
        Args:
            audio_data: 音声データ
            sample_rate: サンプリングレート
            threshold: 無音判定のしきい値
            margin_seconds: 前後に残すマージン（秒）
            
        Returns:
            np.ndarray: トリミング済み音声データ
        """
        # 音声レベルの絶対値を計算
        audio_level = np.abs(audio_data)
        
        # しきい値を超える部分を検出
        above_threshold = audio_level > threshold
        
        if not np.any(above_threshold):
            # 全て無音の場合は元データを返す
            return audio_data
        
        # 音声がある部分の開始・終了インデックス
        start_idx = np.argmax(above_threshold)
        end_idx = len(audio_data) - np.argmax(above_threshold[::-1]) - 1
        
        # マージンを追加
        margin_samples = int(margin_seconds * sample_rate)
        start_idx = max(0, start_idx - margin_samples)
        end_idx = min(len(audio_data), end_idx + margin_samples)
        
        return audio_data[start_idx:end_idx]
    
    def is_model_ready(self) -> bool:
        """
        モデルが利用可能かどうかを確認
        
        Returns:
            bool: モデルが準備完了かどうか
        """
        return self.model is not None and not self.is_loading
    
    def is_transcribing(self) -> bool:
        """
        文字起こし処理中かどうかを確認
        
        Returns:
            bool: 処理中かどうか
        """
        return self.is_processing
    
    def get_model_info(self) -> dict:
        """
        モデル情報を取得
        
        Returns:
            dict: モデル情報
        """
        return {
            "model_size": self.model_size,
            "device": self.device,
            "is_ready": self.is_model_ready(),
            "is_loading": self.is_loading,
            "is_processing": self.is_processing
        }