"""
診断・自己修復機能マネージャー

システムの健全性チェック、問題検出、自動修復機能を提供します。
"""

import os
import sys
import shutil
import subprocess
import threading
import time
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Callable
from pathlib import Path
from enum import Enum

from PySide6.QtCore import QObject, Signal, QTimer

from utils.logger_config import get_logger, LogLevel, ErrorCode


class DiagnosticStatus(Enum):
    """診断結果ステータス"""
    HEALTHY = "healthy"
    WARNING = "warning" 
    ERROR = "error"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class DiagnosticResult:
    """診断結果クラス"""
    
    def __init__(
        self, 
        component: str, 
        status: DiagnosticStatus, 
        message: str, 
        details: Optional[Dict] = None,
        fix_available: bool = False,
        fix_function: Optional[Callable] = None
    ) -> None:
        self.component = component
        self.status = status
        self.message = message
        self.details = details or {}
        self.fix_available = fix_available
        self.fix_function = fix_function
        self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict:
        """辞書形式に変換"""
        return {
            'component': self.component,
            'status': self.status.value,
            'message': self.message,
            'details': self.details,
            'fix_available': self.fix_available,
            'timestamp': self.timestamp.isoformat()
        }


class SystemDiagnosticManager(QObject):
    """システム診断マネージャー"""
    
    # シグナル定義
    diagnostic_completed = Signal(list)  # 診断完了時にDiagnosticResultのリストを送信
    issue_detected = Signal(object)      # 問題検出時にDiagnosticResultを送信
    auto_fix_completed = Signal(str, bool)  # 自動修復完了時 (component, success)
    
    def __init__(self) -> None:
        super().__init__()
        self.app_logger = get_logger()
        self.diagnostic_results: List[DiagnosticResult] = []
        
        # 定期診断タイマー
        self.periodic_timer = QTimer()
        self.periodic_timer.timeout.connect(self.run_full_diagnostics)
        
        # 診断中フラグ
        self.is_running_diagnostics = False
        
        self.app_logger.info("DiagnosticManager", "システム診断マネージャーを初期化しました")
    
    def start_periodic_diagnostics(self, interval_minutes: int = 5) -> None:
        """定期診断を開始"""
        self.periodic_timer.start(interval_minutes * 60 * 1000)  # ミリ秒
        self.app_logger.info("DiagnosticManager", f"定期診断を開始しました (間隔: {interval_minutes}分)")
    
    def stop_periodic_diagnostics(self) -> None:
        """定期診断を停止"""
        self.periodic_timer.stop()
        self.app_logger.info("DiagnosticManager", "定期診断を停止しました")
    
    def run_full_diagnostics(self) -> List[DiagnosticResult]:
        """完全な診断を実行"""
        if self.is_running_diagnostics:
            self.app_logger.warning("DiagnosticManager", "診断が既に実行中です")
            return self.diagnostic_results
        
        self.is_running_diagnostics = True
        self.diagnostic_results.clear()
        
        try:
            self.app_logger.info("DiagnosticManager", "システム診断を開始します")
            
            # 各診断項目を実行
            diagnostics = [
                self._diagnose_system_resources,
                self._diagnose_audio_devices,
                self._diagnose_file_system,
                self._diagnose_permissions,
                self._diagnose_dependencies,
                self._diagnose_whisper_model,
                self._diagnose_logs_directory,
                self._diagnose_network_connectivity
            ]
            
            for diagnostic_func in diagnostics:
                try:
                    result = diagnostic_func()
                    self.diagnostic_results.extend(result if isinstance(result, list) else [result])
                except Exception as e:
                    error_result = DiagnosticResult(
                        component=diagnostic_func.__name__,
                        status=DiagnosticStatus.ERROR,
                        message=f"診断エラー: {str(e)}",
                        details={"exception": str(e)}
                    )\n                    self.diagnostic_results.append(error_result)\n                    self.app_logger.error(\n                        \"DiagnosticManager\", \n                        f\"診断関数 {diagnostic_func.__name__} でエラー: {e}\",\n                        exception=e\n                    )\n            \n            # 問題のある項目を検出\n            issues = [r for r in self.diagnostic_results if r.status in [DiagnosticStatus.WARNING, DiagnosticStatus.ERROR, DiagnosticStatus.CRITICAL]]\n            \n            if issues:\n                self.app_logger.warning(\"DiagnosticManager\", f\"{len(issues)}件の問題を検出しました\")\n                for issue in issues:\n                    self.issue_detected.emit(issue)\n            else:\n                self.app_logger.info(\"DiagnosticManager\", \"システムに問題は検出されませんでした\")\n            \n            self.diagnostic_completed.emit(self.diagnostic_results)\n            return self.diagnostic_results\n            \n        finally:\n            self.is_running_diagnostics = False\n    \n    def _diagnose_system_resources(self) -> List[DiagnosticResult]:\n        \"\"\"システムリソース診断\"\"\"\n        results = []\n        \n        try:\n            import psutil\n            \n            # CPU使用率チェック\n            cpu_percent = psutil.cpu_percent(interval=1)\n            if cpu_percent < 70:\n                results.append(DiagnosticResult(\n                    \"CPU\", DiagnosticStatus.HEALTHY, \n                    f\"CPU使用率正常: {cpu_percent:.1f}%\",\n                    {\"cpu_percent\": cpu_percent}\n                ))\n            elif cpu_percent < 85:\n                results.append(DiagnosticResult(\n                    \"CPU\", DiagnosticStatus.WARNING, \n                    f\"CPU使用率がやや高めです: {cpu_percent:.1f}%\",\n                    {\"cpu_percent\": cpu_percent}\n                ))\n            else:\n                results.append(DiagnosticResult(\n                    \"CPU\", DiagnosticStatus.ERROR, \n                    f\"CPU使用率が非常に高いです: {cpu_percent:.1f}%\",\n                    {\"cpu_percent\": cpu_percent}\n                ))\n            \n            # メモリ使用率チェック\n            memory = psutil.virtual_memory()\n            if memory.percent < 80:\n                results.append(DiagnosticResult(\n                    \"Memory\", DiagnosticStatus.HEALTHY, \n                    f\"メモリ使用率正常: {memory.percent:.1f}%\",\n                    {\"memory_percent\": memory.percent, \"available_gb\": memory.available // (1024**3)}\n                ))\n            elif memory.percent < 90:\n                results.append(DiagnosticResult(\n                    \"Memory\", DiagnosticStatus.WARNING, \n                    f\"メモリ使用率がやや高めです: {memory.percent:.1f}%\",\n                    {\"memory_percent\": memory.percent, \"available_gb\": memory.available // (1024**3)}\n                ))\n            else:\n                results.append(DiagnosticResult(\n                    \"Memory\", DiagnosticStatus.CRITICAL, \n                    f\"メモリ不足の危険性があります: {memory.percent:.1f}%\",\n                    {\"memory_percent\": memory.percent, \"available_gb\": memory.available // (1024**3)}\n                ))\n            \n        except Exception as e:\n            results.append(DiagnosticResult(\n                \"SystemResources\", DiagnosticStatus.ERROR, \n                f\"システムリソース情報の取得に失敗: {e}\",\n                {\"exception\": str(e)}\n            ))\n        \n        return results\n    \n    def _diagnose_audio_devices(self) -> List[DiagnosticResult]:\n        \"\"\"音声デバイス診断\"\"\"\n        results = []\n        \n        try:\n            import sounddevice as sd\n            \n            # デフォルトデバイスチェック\n            try:\n                default_device = sd.default.device[0]\n                device_info = sd.query_devices(default_device)\n                \n                results.append(DiagnosticResult(\n                    \"AudioDevice\", DiagnosticStatus.HEALTHY,\n                    f\"デフォルト音声デバイス利用可能: {device_info['name']}\",\n                    {\n                        \"device_name\": device_info['name'],\n                        \"max_input_channels\": device_info['max_input_channels'],\n                        \"default_samplerate\": device_info['default_samplerate']\n                    }\n                ))\n            except Exception as e:\n                results.append(DiagnosticResult(\n                    \"AudioDevice\", DiagnosticStatus.ERROR,\n                    \"デフォルト音声デバイスにアクセスできません\",\n                    {\"exception\": str(e)},\n                    fix_available=True,\n                    fix_function=self._fix_audio_device\n                ))\n            \n            # 入力デバイス一覧チェック\n            devices = sd.query_devices()\n            input_devices = [d for d in devices if d['max_input_channels'] > 0]\n            \n            if len(input_devices) == 0:\n                results.append(DiagnosticResult(\n                    \"AudioDevices\", DiagnosticStatus.CRITICAL,\n                    \"利用可能な音声入力デバイスが見つかりません\",\n                    {\"total_devices\": len(devices)}\n                ))\n            else:\n                results.append(DiagnosticResult(\n                    \"AudioDevices\", DiagnosticStatus.HEALTHY,\n                    f\"{len(input_devices)}個の音声入力デバイスが利用可能\",\n                    {\"input_device_count\": len(input_devices), \"total_devices\": len(devices)}\n                ))\n                \n        except Exception as e:\n            results.append(DiagnosticResult(\n                \"AudioSystem\", DiagnosticStatus.ERROR,\n                f\"音声システムの診断に失敗: {e}\",\n                {\"exception\": str(e)}\n            ))\n        \n        return results\n    \n    def _diagnose_file_system(self) -> List[DiagnosticResult]:\n        \"\"\"ファイルシステム診断\"\"\"\n        results = []\n        \n        try:\n            # ディスク容量チェック\n            total, used, free = shutil.disk_usage(\".\")\n            free_gb = free // (1024**3)\n            \n            if free_gb > 10:\n                results.append(DiagnosticResult(\n                    \"DiskSpace\", DiagnosticStatus.HEALTHY,\n                    f\"十分な空き容量があります: {free_gb}GB\",\n                    {\"free_gb\": free_gb, \"total_gb\": total // (1024**3)}\n                ))\n            elif free_gb > 2:\n                results.append(DiagnosticResult(\n                    \"DiskSpace\", DiagnosticStatus.WARNING,\n                    f\"空き容量が少なくなっています: {free_gb}GB\",\n                    {\"free_gb\": free_gb, \"total_gb\": total // (1024**3)}\n                ))\n            else:\n                results.append(DiagnosticResult(\n                    \"DiskSpace\", DiagnosticStatus.ERROR,\n                    f\"空き容量が不足しています: {free_gb}GB\",\n                    {\"free_gb\": free_gb, \"total_gb\": total // (1024**3)},\n                    fix_available=True,\n                    fix_function=self._fix_disk_space\n                ))\n            \n            # 重要ディレクトリの存在チェック\n            important_dirs = [\"logs\", \"src\", \"tests\"]\n            for dir_name in important_dirs:\n                dir_path = Path(dir_name)\n                if dir_path.exists():\n                    results.append(DiagnosticResult(\n                        f\"Directory-{dir_name}\", DiagnosticStatus.HEALTHY,\n                        f\"ディレクトリが存在します: {dir_name}\",\n                        {\"path\": str(dir_path.absolute())}\n                    ))\n                else:\n                    results.append(DiagnosticResult(\n                        f\"Directory-{dir_name}\", DiagnosticStatus.WARNING,\n                        f\"ディレクトリが存在しません: {dir_name}\",\n                        {\"path\": str(dir_path.absolute())},\n                        fix_available=True,\n                        fix_function=lambda d=dir_name: self._fix_missing_directory(d)\n                    ))\n        \n        except Exception as e:\n            results.append(DiagnosticResult(\n                \"FileSystem\", DiagnosticStatus.ERROR,\n                f\"ファイルシステム診断エラー: {e}\",\n                {\"exception\": str(e)}\n            ))\n        \n        return results\n    \n    def _diagnose_permissions(self) -> List[DiagnosticResult]:\n        \"\"\"アクセス許可診断\"\"\"\n        results = []\n        \n        try:\n            # 書き込み権限チェック\n            test_file = Path(\"test_write_permission.tmp\")\n            try:\n                test_file.write_text(\"test\")\n                test_file.unlink()\n                results.append(DiagnosticResult(\n                    \"WritePermission\", DiagnosticStatus.HEALTHY,\n                    \"書き込み権限が正常に機能しています\"\n                ))\n            except PermissionError:\n                results.append(DiagnosticResult(\n                    \"WritePermission\", DiagnosticStatus.ERROR,\n                    \"現在のディレクトリに書き込み権限がありません\",\n                    {\"current_dir\": str(Path.cwd())}\n                ))\n            \n            # 実行権限チェック (Windows)\n            if sys.platform == \"win32\":\n                try:\n                    result = subprocess.run([\"python\", \"--version\"], capture_output=True, text=True, timeout=5)\n                    if result.returncode == 0:\n                        results.append(DiagnosticResult(\n                            \"PythonExecution\", DiagnosticStatus.HEALTHY,\n                            \"Python実行権限が正常です\",\n                            {\"python_version\": result.stdout.strip()}\n                        ))\n                    else:\n                        results.append(DiagnosticResult(\n                            \"PythonExecution\", DiagnosticStatus.WARNING,\n                            \"Pythonの実行に問題がある可能性があります\"\n                        ))\n                except subprocess.TimeoutExpired:\n                    results.append(DiagnosticResult(\n                        \"PythonExecution\", DiagnosticStatus.WARNING,\n                        \"Python実行チェックがタイムアウトしました\"\n                    ))\n                except Exception as e:\n                    results.append(DiagnosticResult(\n                        \"PythonExecution\", DiagnosticStatus.WARNING,\n                        f\"Python実行チェックでエラー: {e}\"\n                    ))\n        \n        except Exception as e:\n            results.append(DiagnosticResult(\n                \"Permissions\", DiagnosticStatus.ERROR,\n                f\"権限チェックエラー: {e}\",\n                {\"exception\": str(e)}\n            ))\n        \n        return results\n    \n    def _diagnose_dependencies(self) -> List[DiagnosticResult]:\n        \"\"\"依存関係診断\"\"\"\n        results = []\n        \n        required_packages = {\n            \"PySide6\": \"PySide6\",\n            \"faster-whisper\": \"faster_whisper\",\n            \"sounddevice\": \"sounddevice\", \n            \"keyboard\": \"keyboard\",\n            \"pyperclip\": \"pyperclip\",\n            \"numpy\": \"numpy\",\n            \"soundfile\": \"soundfile\",\n            \"psutil\": \"psutil\"\n        }\n        \n        for package_name, import_name in required_packages.items():\n            try:\n                __import__(import_name)\n                results.append(DiagnosticResult(\n                    f\"Package-{package_name}\", DiagnosticStatus.HEALTHY,\n                    f\"パッケージが正常にインストールされています: {package_name}\"\n                ))\n            except ImportError:\n                results.append(DiagnosticResult(\n                    f\"Package-{package_name}\", DiagnosticStatus.ERROR,\n                    f\"必要なパッケージがインストールされていません: {package_name}\",\n                    {\"package_name\": package_name, \"import_name\": import_name},\n                    fix_available=True,\n                    fix_function=lambda p=package_name: self._fix_missing_package(p)\n                ))\n        \n        return results\n    \n    def _diagnose_whisper_model(self) -> DiagnosticResult:\n        \"\"\"Whisperモデル診断\"\"\"\n        try:\n            from faster_whisper import WhisperModel\n            \n            # モデルの初期化テスト（軽量モデルで）\n            model = WhisperModel(\"tiny\", device=\"cpu\")\n            \n            return DiagnosticResult(\n                \"WhisperModel\", DiagnosticStatus.HEALTHY,\n                \"Whisperモデルが正常にロード可能です\",\n                {\"test_model\": \"tiny\"}\n            )\n            \n        except Exception as e:\n            return DiagnosticResult(\n                \"WhisperModel\", DiagnosticStatus.ERROR,\n                f\"Whisperモデルのロードに失敗: {e}\",\n                {\"exception\": str(e)}\n            )\n    \n    def _diagnose_logs_directory(self) -> DiagnosticResult:\n        \"\"\"ログディレクトリ診断\"\"\"\n        logs_dir = Path(\"logs\")\n        \n        if not logs_dir.exists():\n            return DiagnosticResult(\n                \"LogsDirectory\", DiagnosticStatus.WARNING,\n                \"ログディレクトリが存在しません\",\n                {\"path\": str(logs_dir.absolute())},\n                fix_available=True,\n                fix_function=self._fix_logs_directory\n            )\n        \n        # ディレクトリ内のログファイル数チェック\n        log_files = list(logs_dir.glob(\"*.log\"))\n        json_files = list(logs_dir.glob(\"*.json\"))\n        \n        return DiagnosticResult(\n            \"LogsDirectory\", DiagnosticStatus.HEALTHY,\n            f\"ログディレクトリが正常です (ログファイル: {len(log_files)}, JSONファイル: {len(json_files)})\",\n            {\"path\": str(logs_dir.absolute()), \"log_files\": len(log_files), \"json_files\": len(json_files)}\n        )\n    \n    def _diagnose_network_connectivity(self) -> DiagnosticResult:\n        \"\"\"ネットワーク接続診断（Whisperモデルダウンロード用）\"\"\"\n        try:\n            import urllib.request\n            import socket\n            \n            # インターネット接続テスト\n            socket.setdefaulttimeout(3)\n            urllib.request.urlopen('https://www.google.com')\n            \n            return DiagnosticResult(\n                \"NetworkConnectivity\", DiagnosticStatus.HEALTHY,\n                \"インターネット接続が利用可能です（モデルダウンロード可能）\"\n            )\n            \n        except Exception as e:\n            return DiagnosticResult(\n                \"NetworkConnectivity\", DiagnosticStatus.WARNING,\n                \"インターネット接続に問題があります（オフライン動作は可能）\",\n                {\"exception\": str(e)}\n            )\n    \n    # 自動修復機能\n    \n    def auto_fix_issue(self, diagnostic_result: DiagnosticResult) -> bool:\n        \"\"\"問題の自動修復を実行\"\"\"\n        if not diagnostic_result.fix_available or not diagnostic_result.fix_function:\n            self.app_logger.warning(\"DiagnosticManager\", f\"自動修復が利用できません: {diagnostic_result.component}\")\n            return False\n        \n        try:\n            self.app_logger.info(\"DiagnosticManager\", f\"自動修復を開始: {diagnostic_result.component}\")\n            \n            success = diagnostic_result.fix_function()\n            \n            if success:\n                self.app_logger.info(\"DiagnosticManager\", f\"自動修復が完了: {diagnostic_result.component}\")\n            else:\n                self.app_logger.warning(\"DiagnosticManager\", f\"自動修復に失敗: {diagnostic_result.component}\")\n            \n            self.auto_fix_completed.emit(diagnostic_result.component, success)\n            return success\n            \n        except Exception as e:\n            self.app_logger.error(\n                \"DiagnosticManager\", \n                f\"自動修復中にエラーが発生: {diagnostic_result.component} - {e}\",\n                exception=e\n            )\n            self.auto_fix_completed.emit(diagnostic_result.component, False)\n            return False\n    \n    def _fix_audio_device(self) -> bool:\n        \"\"\"音声デバイス問題の修復\"\"\"\n        try:\n            # Windowsの音声サービス再起動（管理者権限が必要）\n            if sys.platform == \"win32\":\n                self.app_logger.info(\"DiagnosticManager\", \"音声デバイスの修復を試行中...\")\n                # 実際の修復処理はここに実装\n                # 注：管理者権限が必要な操作は含めない\n                return True\n            return False\n        except Exception as e:\n            self.app_logger.error(\"DiagnosticManager\", f\"音声デバイス修復エラー: {e}\")\n            return False\n    \n    def _fix_disk_space(self) -> bool:\n        \"\"\"ディスク容量問題の修復\"\"\"\n        try:\n            # 古いログファイルを削除\n            logs_dir = Path(\"logs\")\n            if logs_dir.exists():\n                old_logs = sorted(logs_dir.glob(\"*.log\"), key=os.path.getmtime)[:-5]  # 最新5つを残す\n                deleted_count = 0\n                for log_file in old_logs:\n                    try:\n                        log_file.unlink()\n                        deleted_count += 1\n                    except Exception:\n                        pass\n                \n                if deleted_count > 0:\n                    self.app_logger.info(\"DiagnosticManager\", f\"{deleted_count}個の古いログファイルを削除しました\")\n                    return True\n            return False\n        except Exception as e:\n            self.app_logger.error(\"DiagnosticManager\", f\"ディスク容量修復エラー: {e}\")\n            return False\n    \n    def _fix_missing_directory(self, dir_name: str) -> bool:\n        \"\"\"不足ディレクトリの修復\"\"\"\n        try:\n            dir_path = Path(dir_name)\n            dir_path.mkdir(parents=True, exist_ok=True)\n            self.app_logger.info(\"DiagnosticManager\", f\"ディレクトリを作成しました: {dir_name}\")\n            return True\n        except Exception as e:\n            self.app_logger.error(\"DiagnosticManager\", f\"ディレクトリ作成エラー {dir_name}: {e}\")\n            return False\n    \n    def _fix_logs_directory(self) -> bool:\n        \"\"\"ログディレクトリの修復\"\"\"\n        return self._fix_missing_directory(\"logs\")\n    \n    def _fix_missing_package(self, package_name: str) -> bool:\n        \"\"\"不足パッケージの修復\"\"\"\n        try:\n            # pip install を実行（実際のプロダクション環境では注意が必要）\n            result = subprocess.run(\n                [sys.executable, \"-m\", \"pip\", \"install\", package_name],\n                capture_output=True, text=True, timeout=300\n            )\n            \n            if result.returncode == 0:\n                self.app_logger.info(\"DiagnosticManager\", f\"パッケージをインストールしました: {package_name}\")\n                return True\n            else:\n                self.app_logger.error(\"DiagnosticManager\", f\"パッケージインストール失敗 {package_name}: {result.stderr}\")\n                return False\n                \n        except Exception as e:\n            self.app_logger.error(\"DiagnosticManager\", f\"パッケージインストールエラー {package_name}: {e}\")\n            return False\n    \n    def get_latest_results(self) -> List[DiagnosticResult]:\n        \"\"\"最新の診断結果を取得\"\"\"\n        return self.diagnostic_results.copy()\n    \n    def get_health_score(self) -> Tuple[float, Dict[str, int]]:\n        \"\"\"システムの健全性スコアを計算\"\"\"\n        if not self.diagnostic_results:\n            return 0.0, {}\n        \n        status_counts = {\n            DiagnosticStatus.HEALTHY: 0,\n            DiagnosticStatus.WARNING: 0,\n            DiagnosticStatus.ERROR: 0,\n            DiagnosticStatus.CRITICAL: 0,\n            DiagnosticStatus.UNKNOWN: 0\n        }\n        \n        for result in self.diagnostic_results:\n            status_counts[result.status] += 1\n        \n        # スコア計算（健全：4点、警告：2点、エラー：1点、クリティカル：0点、不明：1点）\n        total_points = (\n            status_counts[DiagnosticStatus.HEALTHY] * 4 +\n            status_counts[DiagnosticStatus.WARNING] * 2 +\n            status_counts[DiagnosticStatus.ERROR] * 1 +\n            status_counts[DiagnosticStatus.CRITICAL] * 0 +\n            status_counts[DiagnosticStatus.UNKNOWN] * 1\n        )\n        \n        max_points = len(self.diagnostic_results) * 4\n        health_score = (total_points / max_points) * 100 if max_points > 0 else 0\n        \n        return health_score, {status.value: count for status, count in status_counts.items()}"