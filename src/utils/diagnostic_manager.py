"""
診断マネージャーモジュール

システムの健全性診断と問題の自動修復を提供します。
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple

import psutil
from PySide6.QtCore import QObject, Signal

from src.utils.logger_config import get_logger


class DiagnosticStatus(Enum):
    """診断ステータス"""
    HEALTHY = "healthy"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class DiagnosticResult:
    """診断結果"""
    component: str
    status: DiagnosticStatus
    message: str
    details: Optional[Dict] = None


class SystemDiagnosticManager(QObject):
    """システム診断マネージャー"""
    
    # シグナル定義
    diagnostic_completed = Signal(list)
    issue_detected = Signal(object)
    
    def __init__(self) -> None:
        """診断マネージャーの初期化"""
        super().__init__()
        self.app_logger = get_logger()
        self.logger = logging.getLogger(__name__)
        self.diagnostic_results: List[DiagnosticResult] = []
        self.is_running_diagnostics = False
    
    def run_full_diagnostics(self) -> List[DiagnosticResult]:
        """完全診断を実行"""
        if self.is_running_diagnostics:
            return self.diagnostic_results
        
        self.is_running_diagnostics = True
        self.diagnostic_results.clear()
        
        try:
            # 各種診断を実行
            self.diagnostic_results.extend(self._diagnose_system_resources())
            self.diagnostic_results.extend(self._diagnose_audio_devices())
            self.diagnostic_results.extend(self._diagnose_dependencies())
            
            self.diagnostic_completed.emit(self.diagnostic_results)
            return self.diagnostic_results
            
        finally:
            self.is_running_diagnostics = False
    
    def _diagnose_system_resources(self) -> List[DiagnosticResult]:
        """システムリソース診断"""
        results = []
        
        try:
            # CPU使用率チェック
            cpu_percent = psutil.cpu_percent(interval=0.1)
            if cpu_percent < 70:
                results.append(DiagnosticResult(
                    "CPU", DiagnosticStatus.HEALTHY, 
                    f"CPU使用率正常: {cpu_percent:.1f}%"
                ))
            else:
                results.append(DiagnosticResult(
                    "CPU", DiagnosticStatus.WARNING, 
                    f"CPU使用率: {cpu_percent:.1f}%"
                ))
            
            # メモリ使用率チェック
            memory = psutil.virtual_memory()
            if memory.percent < 80:
                results.append(DiagnosticResult(
                    "Memory", DiagnosticStatus.HEALTHY, 
                    f"メモリ使用率正常: {memory.percent:.1f}%"
                ))
            else:
                results.append(DiagnosticResult(
                    "Memory", DiagnosticStatus.WARNING, 
                    f"メモリ使用率: {memory.percent:.1f}%"
                ))
        
        except Exception as e:
            results.append(DiagnosticResult(
                "SystemResources", DiagnosticStatus.ERROR, 
                f"システムリソース情報の取得に失敗: {e}"
            ))
        
        return results
    
    def _diagnose_audio_devices(self) -> List[DiagnosticResult]:
        """音声デバイス診断"""
        results = []
        
        try:
            import sounddevice as sd
            
            devices = sd.query_devices()
            input_devices = [d for d in devices if d['max_input_channels'] > 0]
            
            if len(input_devices) == 0:
                results.append(DiagnosticResult(
                    "AudioDevices", DiagnosticStatus.CRITICAL,
                    "利用可能な音声入力デバイスが見つかりません"
                ))
            else:
                results.append(DiagnosticResult(
                    "AudioDevices", DiagnosticStatus.HEALTHY,
                    f"{len(input_devices)}個の音声入力デバイスが利用可能"
                ))
                
        except Exception as e:
            results.append(DiagnosticResult(
                "AudioSystem", DiagnosticStatus.ERROR,
                f"音声システムの診断に失敗: {e}"
            ))
        
        return results
    
    def _diagnose_dependencies(self) -> List[DiagnosticResult]:
        """依存関係診断"""
        results = []
        
        required_packages = {
            "PySide6": "PySide6",
            "faster-whisper": "faster_whisper",
            "sounddevice": "sounddevice"
        }
        
        for package_name, import_name in required_packages.items():
            try:
                __import__(import_name)
                results.append(DiagnosticResult(
                    f"Package-{package_name}", DiagnosticStatus.HEALTHY,
                    f"パッケージが正常にインストールされています: {package_name}"
                ))
            except ImportError:
                results.append(DiagnosticResult(
                    f"Package-{package_name}", DiagnosticStatus.ERROR,
                    f"必要なパッケージがインストールされていません: {package_name}"
                ))
        
        return results
    
    def get_health_score(self) -> Tuple[float, Dict[str, int]]:
        """システムの健全性スコアを計算"""
        if not self.diagnostic_results:
            return 0.0, {}
        
        status_counts = {status: 0 for status in DiagnosticStatus}
        for result in self.diagnostic_results:
            status_counts[result.status] += 1
        
        # スコア計算
        total_points = (
            status_counts[DiagnosticStatus.HEALTHY] * 4 +
            status_counts[DiagnosticStatus.WARNING] * 2 +
            status_counts[DiagnosticStatus.ERROR] * 1 +
            status_counts[DiagnosticStatus.CRITICAL] * 0 +
            status_counts[DiagnosticStatus.UNKNOWN] * 1
        )
        
        max_points = len(self.diagnostic_results) * 4
        health_score = (total_points / max_points) * 100 if max_points > 0 else 0
        
        return health_score, {status.value: count for status, count in status_counts.items()}
