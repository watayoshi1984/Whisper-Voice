# Whisper Voice MVP - メンテナンス・運用ガイド

## 目次

1. [開発環境のメンテナンス](#開発環境のメンテナンス)
2. [ログ管理とモニタリング](#ログ管理とモニタリング)
3. [パフォーマンス監視と最適化](#パフォーマンス監視と最適化)
4. [セキュリティとアップデート](#セキュリティとアップデート)
5. [バックアップと復旧](#バックアップと復旧)
6. [継続的改善](#継続的改善)
7. [チーム開発における注意点](#チーム開発における注意点)

---

## 開発環境のメンテナンス

### 🔧 定期的なメンテナンス作業

#### 毎週実施すべき作業

**依存関係の確認と更新**
```bash
# セキュリティアップデートの確認
poetry show --outdated

# 安全な更新（マイナーバージョンのみ）
poetry update --lock

# 動作確認
poetry run python run_dev.py test
```

**ログファイルのクリーンアップ**
```bash
# 古いログファイルの削除（1週間以上前）
find logs/ -name "*.log" -mtime +7 -delete
find logs/ -name "*.json" -mtime +7 -delete

# ログディスク使用量確認
du -sh logs/
```

#### 毎月実施すべき作業

**完全な環境再構築テスト**
```bash
# 1. バックアップ作成
cp -r . ../backup-$(date +%Y%m%d)

# 2. 仮想環境の再作成
poetry env remove python
poetry install

# 3. 全テストの実行
poetry run python run_dev.py test
```

**パフォーマンステスト**
```bash
# システム診断の実行
poetry run python -c "
from src.utils.diagnostic_manager import SystemDiagnosticManager
manager = SystemDiagnosticManager()
results = manager.run_full_diagnostics()
for r in results:
    print(f'{r.component}: {r.status.value} - {r.message}')
"
```

### 🏗️ 環境別の設定管理

#### 開発環境 (Development)
```bash
# デバッグモード有効
export WHISPER_VOICE_DEBUG=true
export WHISPER_VOICE_LOG_LEVEL=DEBUG

# 軽量モデルを使用（開発時の高速化）
export WHISPER_MODEL_SIZE=small

# 実行
poetry run python src/main.py
```

#### テスト環境 (Testing)
```bash
# テストモード有効
export WHISPER_VOICE_TEST_MODE=true
export WHISPER_VOICE_LOG_LEVEL=INFO

# 中程度のモデルでテスト
export WHISPER_MODEL_SIZE=medium

# テスト実行
poetry run pytest tests/ -v
```

#### 本番環境 (Production)
```bash
# 本番モード
export WHISPER_VOICE_LOG_LEVEL=WARNING
export WHISPER_MODEL_SIZE=large-v3

# .exe 実行
./dist/WhisperVoiceMVP.exe
```

### 📦 依存関係管理のベストプラクティス

#### pyproject.toml の管理
```toml
[tool.poetry.dependencies]
# メジャーバージョンは固定、マイナーは柔軟に
PySide6 = "^6.6.0"          # OK: 6.6.x を許可
faster-whisper = "0.10.0"   # 固定: 安定性重視

[tool.poetry.group.dev.dependencies]
# 開発用は比較的柔軟に
pytest = "^7.4.0"
black = "^23.9.0"
```

#### バージョンアップ時の確認事項
1. **破壊的変更の確認**
   ```bash
   # CHANGELOG.md や release notes を確認
   poetry show faster-whisper --latest
   ```

2. **段階的アップデート**
   ```bash
   # 1つずつアップデート
   poetry add "faster-whisper@^0.11.0"
   poetry run python run_dev.py test
   
   # 問題があれば元に戻す
   poetry add "faster-whisper@0.10.0"
   ```

3. **互換性テスト**
   ```bash
   # 全機能のテスト
   poetry run python run_dev.py test
   
   # 手動テスト項目
   # - 音声認識精度
   # - UI動作
   # - ホットキー機能
   # - ファイル出力
   ```

---

## ログ管理とモニタリング

### 📊 ログレベルと用途

| レベル | 用途 | 保存期間 | 自動削除 |
|--------|------|----------|---------|
| TRACE | 詳細デバッグ | 1日 | ✅ |
| DEBUG | 開発用デバッグ | 3日 | ✅ |
| INFO | 一般動作ログ | 1週間 | ✅ |
| WARNING | 注意事項 | 1ヶ月 | ⚠️ |
| ERROR | エラー情報 | 3ヶ月 | ❌ |
| CRITICAL | 重大エラー | 1年 | ❌ |

### 🔍 ログ分析の自動化

#### ログ分析スクリプト作成
```python
# scripts/analyze_logs.py
import json
from pathlib import Path
from collections import Counter
from datetime import datetime, timedelta

def analyze_error_trends(days=7):
    """過去N日間のエラー傾向を分析"""
    logs_dir = Path("logs")
    error_counts = Counter()
    
    cutoff_date = datetime.now() - timedelta(days=days)
    
    for log_file in logs_dir.glob("*.json"):
        if log_file.stat().st_mtime > cutoff_date.timestamp():
            with open(log_file) as f:
                for line in f:
                    try:
                        log_entry = json.loads(line)
                        if log_entry.get('level') in ['ERROR', 'CRITICAL']:
                            error_code = log_entry.get('error_code')
                            if error_code:
                                error_counts[error_code] += 1
                    except json.JSONDecodeError:
                        continue
    
    return error_counts

if __name__ == "__main__":
    trends = analyze_error_trends()
    for error_code, count in trends.most_common(10):
        print(f"Error {error_code}: {count} occurrences")
```

#### 定期レポート生成
```bash
# cron job または Windows Task Scheduler
# 毎日午前9時に実行
0 9 * * * cd /path/to/whisper-voice && python scripts/analyze_logs.py > reports/daily_$(date +\%Y\%m\%d).txt
```

### 📈 監視アラートの設定

#### エラー閾値監視
```python
# scripts/monitor_alerts.py
import smtplib
from email.mime.text import MIMEText
from datetime import datetime

def check_error_threshold(threshold=10):
    """エラー数が閾値を超えた場合にアラート"""
    error_count = analyze_error_trends(days=1)
    total_errors = sum(error_count.values())
    
    if total_errors > threshold:
        send_alert_email(
            subject=f"Whisper Voice Alert: {total_errors} errors detected",
            body=f"Error details:\n" + "\n".join(
                f"{code}: {count}" for code, count in error_count.items()
            )
        )

def send_alert_email(subject, body):
    """アラートメール送信（設定が必要）"""
    # メール設定は環境変数から取得
    pass
```

---

## パフォーマンス監視と最適化

### ⚡ パフォーマンス測定

#### システムリソース監視
```python
# scripts/performance_monitor.py
import psutil
import time
from datetime import datetime

class PerformanceMonitor:
    def __init__(self):
        self.metrics = []
    
    def collect_metrics(self, duration_minutes=60):
        """指定時間中のメトリクスを収集"""
        end_time = time.time() + (duration_minutes * 60)
        
        while time.time() < end_time:
            metric = {
                'timestamp': datetime.now().isoformat(),
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_percent': psutil.virtual_memory().percent,
                'memory_used_gb': psutil.virtual_memory().used / (1024**3),
                'disk_io': psutil.disk_io_counters(),
                'network_io': psutil.net_io_counters()
            }
            self.metrics.append(metric)
            time.sleep(60)  # 1分間隔
    
    def generate_report(self):
        """パフォーマンスレポート生成"""
        if not self.metrics:
            return "No metrics collected"
        
        avg_cpu = sum(m['cpu_percent'] for m in self.metrics) / len(self.metrics)
        avg_memory = sum(m['memory_percent'] for m in self.metrics) / len(self.metrics)
        
        return f"""Performance Report
=================
Average CPU Usage: {avg_cpu:.2f}%
Average Memory Usage: {avg_memory:.2f}%
Peak Memory Usage: {max(m['memory_percent'] for m in self.metrics):.2f}%
Measurements: {len(self.metrics)} samples
"""

# 使用例
if __name__ == "__main__":
    monitor = PerformanceMonitor()
    monitor.collect_metrics(duration_minutes=30)
    print(monitor.generate_report())
```

#### Whisper処理時間最適化
```python
# src/utils/performance_optimizer.py
import time
from functools import wraps

def measure_transcription_time(func):
    """文字起こし処理時間を測定するデコレータ"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        
        processing_time = end_time - start_time
        
        # ログに記録
        logger = get_logger()
        logger.info(
            "PerformanceOptimizer", 
            f"Transcription time: {processing_time:.2f}s",
            context={
                "processing_time_seconds": processing_time,
                "audio_length_seconds": kwargs.get('audio_length', 'unknown')
            }
        )
        
        return result
    return wrapper

# 使用例（transcriber.py に追加）
@measure_transcription_time
def transcribe_audio(self, audio_data, sample_rate=16000):
    # 既存の処理...
```

### 🚀 最適化のガイドライン

#### CPU使用率最適化
```python
# マルチスレッド処理の最適化
import concurrent.futures
import threading

class OptimizedTranscriptionEngine(TranscriptionEngine):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # CPUコア数に基づいてワーカー数を決定
        self.max_workers = min(4, os.cpu_count() or 1)
        
    def batch_transcribe(self, audio_batches):
        """複数の音声データを並列処理"""
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [
                executor.submit(self.transcribe_audio, batch) 
                for batch in audio_batches
            ]
            
            results = []
            for future in concurrent.futures.as_completed(futures):
                try:
                    result = future.result(timeout=30)
                    results.append(result)
                except Exception as e:
                    self.app_logger.error("OptimizedEngine", f"Batch processing error: {e}")
                    
            return results
```

#### メモリ使用量最適化
```python
# メモリ効率的な音声バッファ管理
import gc
from collections import deque

class MemoryEfficientAudioProcessor(AudioProcessor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 循環バッファでメモリ使用量を制限
        self.audio_buffer = deque(maxlen=1000)  # 最大1000チャンク
        
    def _audio_callback(self, indata, frames, time_info, status):
        """メモリ効率を考慮した音声コールバック"""
        if self.is_recording:
            # 古いデータは自動的に削除される
            self.audio_buffer.append(indata.copy())
            
            # 定期的にガベージコレクションを実行
            if len(self.audio_buffer) % 100 == 0:
                gc.collect()
```

---

## セキュリティとアップデート

### 🔒 セキュリティ監査チェックリスト

#### 毎月実施すべきセキュリティチェック

**依存関係の脆弱性スキャン**
```bash
# pipのセキュリティチェック（safety をインストール）
poetry add --group dev safety
poetry run safety check

# または poetry-audit-plugin を使用
poetry self add poetry-audit-plugin
poetry audit
```

**ファイル権限の確認**
```bash
# 実行ファイルの権限確認
ls -la dist/WhisperVoiceMVP.exe

# 設定ファイルの権限確認（機密情報を含む場合）
ls -la *.toml *.json *.env
```

**ログファイルの機密情報チェック**
```bash
# ログに機密情報が含まれていないか確認
grep -r "password\|token\|key\|secret" logs/
```

#### セキュリティ強化のための設定

**ログの匿名化**
```python
# src/utils/secure_logger.py
import re
import hashlib

class SecureLogger:
    def __init__(self):
        # 機密情報のパターン
        self.sensitive_patterns = [
            r'password[=:]\s*[^\s]+',
            r'token[=:]\s*[^\s]+',
            r'key[=:]\s*[^\s]+',
            r'secret[=:]\s*[^\s]+'
        ]
    
    def sanitize_message(self, message):
        """ログメッセージから機密情報を除去"""
        for pattern in self.sensitive_patterns:
            message = re.sub(pattern, '[REDACTED]', message, flags=re.IGNORECASE)
        return message
    
    def hash_user_data(self, data):
        """ユーザーデータのハッシュ化"""
        return hashlib.sha256(str(data).encode()).hexdigest()[:8]
```

### 🔄 アップデート管理

#### 自動アップデート機能の実装
```python
# src/utils/updater.py
import requests
import json
import subprocess
from pathlib import Path

class AutoUpdater:
    def __init__(self):
        self.current_version = "1.0.0"
        self.update_url = "https://api.github.com/repos/yourrepo/whisper-voice/releases/latest"
    
    def check_for_updates(self):
        """最新バージョンをチェック"""
        try:
            response = requests.get(self.update_url, timeout=10)
            if response.status_code == 200:
                release_data = response.json()
                latest_version = release_data['tag_name'].lstrip('v')
                
                if self._is_newer_version(latest_version, self.current_version):
                    return {
                        'update_available': True,
                        'latest_version': latest_version,
                        'download_url': release_data['assets'][0]['browser_download_url'],
                        'changelog': release_data['body']
                    }
            
            return {'update_available': False}
            
        except Exception as e:
            self.app_logger.warning("AutoUpdater", f"Update check failed: {e}")
            return {'update_available': False, 'error': str(e)}
    
    def _is_newer_version(self, latest, current):
        """バージョン比較"""
        latest_parts = [int(x) for x in latest.split('.')]
        current_parts = [int(x) for x in current.split('.')]
        
        for i in range(max(len(latest_parts), len(current_parts))):
            latest_num = latest_parts[i] if i < len(latest_parts) else 0
            current_num = current_parts[i] if i < len(current_parts) else 0
            
            if latest_num > current_num:
                return True
            elif latest_num < current_num:
                return False
        
        return False
```

---

## バックアップと復旧

### 💾 バックアップ戦略

#### 自動バックアップスクリプト
```bash
#!/bin/bash
# scripts/backup.sh

# バックアップ設定
BACKUP_DIR="/backup/whisper-voice"
PROJECT_DIR="$(pwd)"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="whisper-voice-backup-${DATE}"

# バックアップディレクトリ作成
mkdir -p "${BACKUP_DIR}"

# プロジェクトファイルのバックアップ
echo "Creating backup: ${BACKUP_NAME}"
tar -czf "${BACKUP_DIR}/${BACKUP_NAME}.tar.gz" \
    --exclude="logs/*.log" \
    --exclude="logs/*.json" \
    --exclude=".git" \
    --exclude="__pycache__" \
    --exclude="dist" \
    --exclude="build" \
    "${PROJECT_DIR}"

# 古いバックアップの削除（30日以上前）
find "${BACKUP_DIR}" -name "*.tar.gz" -mtime +30 -delete

echo "Backup completed: ${BACKUP_DIR}/${BACKUP_NAME}.tar.gz"
```

#### 設定ファイルの分離管理
```
project/
├── configs/
│   ├── development.json
│   ├── production.json
│   └── user_preferences.json
├── src/
└── backups/
    ├── configs/
    └── logs/
```

### 🔄 災害復旧手順

#### レベル1: 設定ファイル破損
```bash
# 1. バックアップから設定復旧
cp backups/configs/latest/*.json configs/

# 2. アプリケーション再起動
poetry run python src/main.py
```

#### レベル2: 依存関係破損
```bash
# 1. 仮想環境の完全再構築
poetry env remove python
poetry install --no-cache

# 2. テスト実行
poetry run python run_dev.py test
```

#### レベル3: システム全体の復旧
```bash
# 1. 最新バックアップから復旧
cd /path/to/restore
tar -xzf /backup/whisper-voice/whisper-voice-backup-latest.tar.gz

# 2. 環境の再構築
poetry install
poetry run python run_dev.py test

# 3. ログの確認
tail -f logs/whisper_voice_$(date +%Y%m%d).log
```

---

## 継続的改善

### 📊 品質メトリクスの追跡

#### コード品質メトリクス
```bash
# scripts/quality_check.sh

echo "=== Code Quality Report ==="

# 1. 複雑度チェック
echo "## Cyclomatic Complexity"
poetry run radon cc src/ -a -nc

# 2. 保守性指数
echo "## Maintainability Index"
poetry run radon mi src/ -nc

# 3. 重複コードチェック
echo "## Code Duplication"
poetry run pylint --disable=all --enable=duplicate-code src/

# 4. テストカバレッジ
echo "## Test Coverage"
poetry run pytest --cov=src tests/ --cov-report=term-missing
```

#### パフォーマンスメトリクス
```python
# scripts/performance_baseline.py
import time
import numpy as np
from src.app.transcriber import TranscriptionEngine

def measure_baseline_performance():
    """基準パフォーマンスを測定"""
    engine = TranscriptionEngine(model_size="small")  # 軽量モデル
    
    # テスト用音声データ（1秒、44.1kHz）
    test_audio = np.random.random(44100).astype(np.float32)
    
    # 10回測定して平均を取る
    times = []
    for _ in range(10):
        start = time.time()
        # engine.transcribe_audio(test_audio, 44100)  # 実際の処理
        time.sleep(0.1)  # 仮の処理時間
        end = time.time()
        times.append(end - start)
    
    avg_time = np.mean(times)
    std_time = np.std(times)
    
    print(f"Baseline Performance:")
    print(f"  Average: {avg_time:.3f}s")
    print(f"  Std Dev: {std_time:.3f}s")
    print(f"  Min: {min(times):.3f}s")
    print(f"  Max: {max(times):.3f}s")
    
    return {
        'average': avg_time,
        'std_dev': std_time,
        'min': min(times),
        'max': max(times)
    }
```

### 🔄 継続的統合 (CI) の設定

#### GitHub Actions設定例
```yaml
# .github/workflows/ci.yml
name: Continuous Integration

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: windows-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    
    - name: Install Poetry
      uses: snok/install-poetry@v1
      
    - name: Install dependencies
      run: poetry install
      
    - name: Run tests
      run: poetry run pytest tests/ -v
      
    - name: Run linting
      run: poetry run ruff check src/
      
    - name: Check code formatting
      run: poetry run black --check src/
      
    - name: Security audit
      run: poetry run safety check
```

---

## チーム開発における注意点

### 👥 開発チーム向けガイドライン

#### コードレビューチェックリスト

**機能追加時**
- [ ] エラーハンドリングは適切か？
- [ ] ログ出力は適切なレベルで行われているか？
- [ ] パフォーマンスに影響はないか？
- [ ] セキュリティ上の問題はないか？
- [ ] テストケースは追加されているか？

**バグ修正時**
- [ ] 根本原因は特定されているか？
- [ ] 同様の問題が他にもないか確認したか？
- [ ] 回帰テストは追加されているか？
- [ ] ログレベルやエラーコードは適切か？

#### ブランチ戦略
```
main (本番)
├── develop (開発統合)
│   ├── feature/audio-enhancement (機能開発)
│   ├── feature/ui-improvements (機能開発)
│   └── bugfix/memory-leak (バグ修正)
└── hotfix/critical-security-fix (緊急修正)
```

#### コミットメッセージ規約
```
# 形式: <type>(<scope>): <subject>

feat(audio): Add noise reduction functionality
fix(ui): Resolve microphone icon positioning issue
docs(readme): Update installation instructions
test(transcriber): Add unit tests for error handling
refactor(logger): Simplify log formatting logic
```

### 📋 リリース管理

#### バージョン管理戦略
```
Major.Minor.Patch (例: 1.2.3)

Major: 破壊的変更
Minor: 新機能追加（後方互換性あり）
Patch: バグ修正
```

#### リリースチェックリスト
- [ ] 全テストがパスしているか
- [ ] パフォーマンステストを実行したか
- [ ] セキュリティ監査を実行したか
- [ ] ドキュメントは更新されているか
- [ ] バックアップは作成されているか
- [ ] ロールバック手順は準備されているか

#### デプロイメント手順
```bash
# scripts/deploy.sh
#!/bin/bash

# 1. バックアップ作成
./scripts/backup.sh

# 2. テスト実行
poetry run python run_dev.py test
if [ $? -ne 0 ]; then
    echo "Tests failed. Deployment aborted."
    exit 1
fi

# 3. ビルド
poetry run python build_exe.py

# 4. 成果物の検証
if [ ! -f "dist/WhisperVoiceMVP.exe" ]; then
    echo "Build failed. Executable not found."
    exit 1
fi

# 5. リリースパッケージ作成
zip -r "whisper-voice-v$(poetry version -s).zip" dist/ docs/ README.md

echo "Deployment package ready: whisper-voice-v$(poetry version -s).zip"
```

---

## 付録

### 📚 参考資料

**公式ドキュメント**
- [PySide6 Documentation](https://doc.qt.io/qtforpython/)
- [faster-whisper GitHub](https://github.com/guillaumekln/faster-whisper)
- [Poetry Documentation](https://python-poetry.org/docs/)

**コミュニティリソース**
- [Python Packaging User Guide](https://packaging.python.org/)
- [12-Factor App Methodology](https://12factor.net/)

**セキュリティリソース**
- [OWASP Python Security](https://owasp.org/www-project-python-security/)
- [Python Security Best Practices](https://python-security.readthedocs.io/)

### 🛠️ 便利なツールとコマンド

**開発効率化**
```bash
# プロジェクト全体の統計情報
cloc src/ tests/ --exclude-dir=__pycache__

# 依存関係ツリーの表示
poetry show --tree

# 未使用インポートの検出
poetry run unimport --check --diff src/

# コード複雑度レポート
poetry run xenon --max-absolute B --max-modules A --max-average A src/
```

**デバッグ支援**
```bash
# リアルタイムログ監視
tail -f logs/whisper_voice_$(date +%Y%m%d).log | grep ERROR

# メモリ使用量監視
watch -n 1 "ps aux | grep python | grep -v grep"

# ファイル変更監視
poetry run watchmedo shell-command \
    --patterns="*.py" \
    --recursive \
    --command='echo "File changed: ${watch_src_path}"' \
    src/
```

**本番環境監視**
```powershell
# Windows PowerShell
# CPU・メモリ使用率の監視
Get-Counter "\Processor(_Total)\% Processor Time","\Memory\Available MBytes" -SampleInterval 5 -MaxSamples 60

# プロセス監視
Get-Process | Where-Object {$_.ProcessName -like "*Whisper*"} | Format-Table -AutoSize
```

このメンテナンスガイドは、プロジェクトの成長に合わせて継続的に更新してください。新しい問題や改善点が見つかった場合は、速やかにドキュメントに反映することを推奨します。