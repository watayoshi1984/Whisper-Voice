## Whisper Voice MVP 開発バックログ（提案）

### 優先順位（Impact × Effort で総合判断）

- 優先A（高インパクト・低〜中工数: まず着手）
  1. 1) モデル選択UI（0.5人週, 低）
  2. 5) WebRTC VAD 無音検出（1人週, 中）
  3. 26) 低遅延チューニング（1人週, 中）
  4. 9) SRT/VTT出力（0.5-1人週, 低-中）
  5. 12) ホットキーGUIと永続化（0.5人週, 低）
  6. 3) 入力デバイス選択+テスト録音（1人週, 中）
  7. 28) モデルキャッシュ管理（0.5-1人週, 低）
  8. 37) 権限/占有セルフテスト（0.5人週, 低）

- 優先B（高インパクト・中工数: 次に着手）
  9. 6) 部分結果（ストリーミング）表示（1-2人週, 中）
  10. 7) 履歴タブと検索（1人週, 中）
  11. 4) ノイズ抑制（1-2人週, 中）
  12. 14) 設定ダイアログ統合（1人週, 中）
  13. 25) バッチ処理（1-2人週, 中）
  14. 39) レイテンシ可視化（1人週, 中）

- 優先C（中インパクト・低工数: 並行で実施）
  15. 2) ログON/OFF・レベル切替（0.5人週, 低）
  16. 8) クリップボード履歴（0.5-1人週, 低）
  17. 10) 言語自動検出（0.5人週, 低）
  18. 11) 句読点/整形（0.5-1人週, 低）
  19. 29) アプリ内ヘルプ/チュートリアル（0.5人週, 低）

- 優先D（高スペックや将来枠: 先行検証/PoC）
  20. 16) 量子化選択（0.5人週, 低）
  21. 17) GPU(CUDA)対応（1-2人週, 中）
  22. 23) 話者分離（3-6人週, 高）
  23. 18) DirectML/ONNX系検討（3-4人週, 高）
  24. 31) インストーラ整備（1-2人週, 中）/ 32) コード署名（0.5-1人週, 中）

注: 実際の優先順位は、ユーザー価値（初回体験・安定性・業務適用度）を最重視し、短期間での改善幅が大きいA群から着手する想定です。

以下は、今後の機能追加アイデアと必要開発リソース、使用ライブラリ/技術、実現内容、参考文献の提案リストです。いずれも現行アーキテクチャ（PySide6 + sounddevice + faster-whisper + PyInstaller）で実装可能です。

### スペック別 利用可能機能まとめ

- 低スペック（目安）: CPUのみ、2-4コア、RAM 4GB前後、GPUなし
  - 推奨モデル: `base` / `small`
  - 快適に使える機能:
    - モデル選択UI、ログレベル切替（1, 2）
    - 入力デバイス選択・テスト録音、アクセス権限セルフテスト（3, 37）
    - WebRTC VADベースの無音検出、低遅延チューニング（5, 26）
    - クリップボード履歴・用語置換辞書（8, 22）
    - SRT/VTT出力、言語自動検出・基本後処理（9, 10, 11）
    - アプリ内ヘルプ、ダークモード、ショートカット設定（29, 44, 12）
  - 注意点: 長時間/大規模ファイルの一括処理や高精度話者分離は非推奨

- 中スペック（目安）: CPU 4-8コア、RAM 8-16GB、iGPU可、GPUなしでも可
  - 推奨モデル: `small` / `medium` / `large-v3`（短時間）
  - 快適に使える機能:
    - ノイズ抑制、音声前処理パイプラインGUI（4, 36）
    - 部分結果（ストリーミング）表示、履歴と検索（6, 7）
    - トレイ常駐、設定統合、モデルキャッシュ管理（13, 14, 28）
    - バッチ処理（中規模）、レイテンシ可視化、スナップショットログ（25, 39, 40）
    - メモリ監視・自動フォールバック、エクスポート/インポート（35, 27）

- 高スペック（目安）: CPU 8コア+、RAM 16GB+、CUDA対応dGPU（VRAM 6GB+）
  - 推奨モデル: `large-v3-turbo` / `large-v3`（長時間）+ CUDA
  - 快適に使える機能:
    - GPU(CUDA)推論、量子化最適化（17, 16）
    - 高精度話者分離（pyannote/WhisperX）、単語タイムスタンプ拡張（23, 追加案: word timestamps）
    - リアルタイム翻訳、会議モード、WASAPIループバック収音（追加案）
    - 大規模バッチ、ダッシュボード/メトリクス、Slack/Teams連携（25, 39, 追加案）
  - 備考: ドライバ/CUDA環境の整備が前提（CTranslate2のCUDA依存）

1) モデル選択UI（ドロップダウン）
- 概要/実現: メイン画面にモデル選択（large-v3-turbo/large-v3/medium/small/base）。選択を`config.json`へ保存。
- リソース/難易度: 0.5人週 / 低
- ライブラリ/技術: PySide6、JSON設定
- 参考: [faster-whisper README](https://github.com/SYSTRAN/faster-whisper)

2) コンソールログON/OFFトグルとログレベル切替
- 概要/実現: UIで`INFO/DEBUG`切替、コンソール表示の有無を設定。`utils/logger_config.py`連携。
- リソース/難易度: 0.5人週 / 低
- ライブラリ/技術: logging, PySide6
- 参考: [Python logging](https://docs.python.org/3/library/logging.html)

3) 入力デバイス選択UIとテスト録音
- 概要/実現: マイク一覧表示・選択、1秒テスト録音→波形/レベル表示、再生確認。
- リソース/難易度: 1人週 / 中
- ライブラリ/技術: sounddevice, numpy, PySide6
- 参考: [python-sounddevice](https://python-sounddevice.readthedocs.io/)

4) ノイズ抑制（オプション）
- 概要/実現: 録音前処理にノイズ抑制（RNNoise or noisereduce）。ON/OFF切替可。
- リソース/難易度: 1-2人週 / 中
- ライブラリ/技術: noisereduce, RNNoise（ラッパー）, numpy
- 参考: [noisereduce](https://github.com/timsainb/noisereduce), [RNNoise](https://github.com/xiph/rnnoise)

5) WebRTC VAD での無音検出改善
- 概要/実現: `py-webrtcvad`を使って音声区間のみを抽出。短文での精度向上。
- リソース/難易度: 1人週 / 中
- ライブラリ/技術: py-webrtcvad, numpy
- 参考: [py-webrtcvad](https://github.com/wiseman/py-webrtcvad)

6) 部分結果（ストリーミング）表示
- 概要/実現: 録音中に短いチャンクで逐次文字起こしし、UIに部分結果を流す。
- リソース/難易度: 1-2人週 / 中
- ライブラリ/技術: faster-whisper（チャンク分割運用）, PySide6
- 参考: [faster-whisper usage](https://github.com/SYSTRAN/faster-whisper#python)

7) 文字起こし履歴タブと検索
- 概要/実現: セッションごとの履歴を保存・表示。全文検索や日付フィルタ提供。
- リソース/難易度: 1人週 / 中
- ライブラリ/技術: SQLite または JSON + Whoosh/簡易検索
- 参考: [SQLite](https://docs.python.org/3/library/sqlite3.html)

8) クリップボード履歴管理とエクスポート
- 概要/実現: コピーされたテキスト履歴、まとめてTXT/JSON出力。
- リソース/難易度: 0.5-1人週 / 低
- ライブラリ/技術: pyperclip, PySide6
- 参考: [pyperclip](https://pypi.org/project/pyperclip/)

9) タイムスタンプ付きSRT/VTT出力
- 概要/実現: セグメントの時刻からSRT/VTTを生成し保存。
- リソース/難易度: 0.5-1人週 / 低-中
- ライブラリ/技術: faster-whisper segments, srt/vttフォーマット
- 参考: [SRT spec](https://en.wikipedia.org/wiki/SubRip), [WebVTT](https://developer.mozilla.org/docs/Web/API/WebVTT_API)

10) 言語自動検出（多言語対応）
- 概要/実現: faster-whisperの言語検出を有効化し、日本語以外の音声にも対応。
- リソース/難易度: 0.5人週 / 低
- ライブラリ/技術: faster-whisper language detection
- 参考: [faster-whisper detect](https://github.com/SYSTRAN/faster-whisper#language-detection)

11) 句読点・大文字小文字整形の後処理
- 概要/実現: 日本語の句読点整形/スペース最適化。英語はケース調整。
- リソース/難易度: 0.5-1人週 / 低
- ライブラリ/技術: regex, tiny segmenter/ja-utils
- 参考: [TinySegmenter](https://github.com/takuyaa/tinysegmenter)

12) ホットキーのGUI設定と永続化
- 概要/実現: ホットキーをUIで編集し、次回起動時に復元。
- リソース/難易度: 0.5人週 / 低
- ライブラリ/技術: keyboard, JSON設定, PySide6
- 参考: [keyboard](https://pypi.org/project/keyboard/)

13) システムトレイ常駐とクイックメニュー
- 概要/実現: トレイアイコンから開始/停止、設定、ログ表示へアクセス。
- リソース/難易度: 1人週 / 中
- ライブラリ/技術: PySide6 QSystemTrayIcon
- 参考: [Qt QSystemTrayIcon](https://doc.qt.io/qt-6/qsystemtrayicon.html)

14) 設定ダイアログ統合（一般/音声/モデル/ログ）
- 概要/実現: 統一設定画面で各種設定を編集・保存。
- リソース/難易度: 1人週 / 中
- ライブラリ/技術: PySide6, JSON設定
- 参考: [Qt Dialogs](https://doc.qt.io/qt-6/qdialog.html)

15) モデルの事前ダウンロードとサイズ/所要時間見積表示
- 概要/実現: 初回前にモデルを明示ダウンロード、進捗・残り時間を表示。
- リソース/難易度: 1-2人週 / 中
- ライブラリ/技術: faster-whisper, HTTP進捗, キャッシュ管理
- 参考: [faster-whisper cache](https://github.com/SYSTRAN/faster-whisper#model-cache)

16) CTranslate2 INT8/INT16 量子化選択
- 概要/実現: `compute_type`を選択（float32/float16/int8_float16等）し速度/メモリ最適化。
- リソース/難易度: 0.5人週 / 低
- ライブラリ/技術: faster-whisper(CTranslate2)
- 参考: [CTranslate2 docs](https://opennmt.net/CTranslate2/)

17) GPU(CUDA)対応の切替
- 概要/実現: CUDA環境で`device=cuda`選択、性能向上。自動検出&フォールバック。
- リソース/難易度: 1-2人週 / 中
- ライブラリ/技術: faster-whisper CUDA, NVIDIA CUDA Toolkit
- 参考: [CUDA support (CTranslate2)](https://opennmt.net/CTranslate2/installation.html)

18) AMD/Intel GPU支援（代替エンジン・将来検討）
- 概要/実現: onnxruntime(DirectML)+Whisper-ONNX等の代替ルートを実験的に提供。
- リソース/難易度: 3-4人週 / 高
- ライブラリ/技術: onnxruntime-directml, whisper-onnx
- 参考: [ONNX Runtime DirectML](https://onnxruntime.ai/docs/execution-providers/DirectML-ExecutionProvider.html)

19) 自動更新（オプション）
- 概要/実現: 新リリースのチェックと差分更新。企業内ネットワーク前提なら手動配布も併用。
- リソース/難易度: 2-3人週 / 中-高
- ライブラリ/技術: PyUpdater など
- 参考: [PyUpdater](https://www.pyupdater.org/)

20) クラッシュレポート/診断ログ収集（オプトイン）
- 概要/実現: 例外を収集し、ユーザーが同意時のみ匿名送信 or ZIP化して共有。
- リソース/難易度: 1人週 / 中
- ライブラリ/技術: sentry-sdk（任意）, 標準logging, zipfile
- 参考: [Sentry Python](https://docs.sentry.io/platforms/python/)

21) デバッグウィンドウ強化（フィルタ/検索/エクスポート）
- 概要/実現: ログレベル・タグで絞込、CSV/JSONへエクスポート。
- リソース/難易度: 0.5-1人週 / 低-中
- ライブラリ/技術: PySide6, logger_config
- 参考: [Qt Model/View](https://doc.qt.io/qt-6/modelview.html)

22) 文字起こし結果の用語置換辞書（カスタム辞書）
- 概要/実現: 社内用語や専門用語の正規化辞書を適用。
- リソース/難易度: 0.5人週 / 低
- ライブラリ/技術: regex, JSON辞書
- 参考: [Regex HOWTO](https://docs.python.org/3/howto/regex.html)

23) スピーカーダイアライゼーション（話者分離・将来）
- 概要/実現: 簡易はエネルギー/ピッチ差で疑似分離。高精度はpyannote/WhisperX。
- リソース/難易度: 3-6人週 / 高
- ライブラリ/技術: pyannote.audio, whisperX
- 参考: [pyannote/audio](https://github.com/pyannote/pyannote-audio), [WhisperX](https://github.com/m-bain/whisperX)

24) 音声品質メータ（RMS/ピーク/クリッピング検出）
- 概要/実現: 入力レベルをUIにバー表示し、過大/過小を警告。
- リソース/難易度: 0.5-1人週 / 低
- ライブラリ/技術: numpy, PySide6
- 参考: [Audio amplitude](https://en.wikipedia.org/wiki/Amplitude)

25) バッチ処理（音声ファイル一括文字起こし）
- 概要/実現: WAV/MP3/MP4フォルダを選択して一括処理、進捗バー表示。
- リソース/難易度: 1-2人週 / 中
- ライブラリ/技術: soundfile/ffmpeg-python, faster-whisper
- 参考: [ffmpeg-python](https://github.com/kkroening/ffmpeg-python)

26) 低遅延チューニング（ブロックサイズ/チャンク長最適化）
- 概要/実現: 入出力バッファとVADパラメータを最適化し平均遅延を短縮。
- リソース/難易度: 1人週 / 中
- ライブラリ/技術: sounddevice, faster-whisperパラメータ
- 参考: [sounddevice latency](https://python-sounddevice.readthedocs.io/en/0.4.6/api.html#streams)

27) 設定/ログ/履歴のエクスポート・インポート
- 概要/実現: ZIPでまとめて出力/復元。PC移行やサポート用。
- リソース/難易度: 0.5人週 / 低
- ライブラリ/技術: zipfile, JSON, pathlib
- 参考: [zipfile](https://docs.python.org/3/library/zipfile.html)

28) モデルキャッシュ管理UI（容量/削除）
- 概要/実現: キャッシュサイズ表示・「古いモデルを削除」ボタン。
- リソース/難易度: 0.5-1人週 / 低
- ライブラリ/技術: pathlib, faster-whisper cache path
- 参考: [faster-whisper cache](https://github.com/SYSTRAN/faster-whisper#model-cache)

29) アプリ内ショートヘルプと初回チュートリアル
- 概要/実現: ツールチップ/モーダルで主要操作を案内。初回のみ表示。
- リソース/難易度: 0.5人週 / 低
- ライブラリ/技術: PySide6
- 参考: [Qt Widgets tutorial](https://doc.qt.io/qt-6/widgets-tutorials.html)

30) CIでの自動ビルド（GitHub Actions）
- 概要/実現: Windows RunnerでPyInstallerビルド→アーティファクト配布。
- リソース/難易度: 1人週 / 中
- ライブラリ/技術: GitHub Actions, PyInstaller
- 参考: [PyInstaller docs](https://pyinstaller.org/en/stable/), [GitHub Actions](https://docs.github.com/actions)

31) インストーラ整備（Inno Setup/NSIS/MSIX）
- 概要/実現: セットアップウィザード作成、スタートメニュー/デスクトップショートカット。
- リソース/難易度: 1-2人週 / 中
- ライブラリ/技術: Inno Setup/NSIS/MSIX
- 参考: [Inno Setup](https://jrsoftware.org/isinfo.php)

32) コード署名（企業配布向け）
- 概要/実現: `signtool`でEXE/MSIXに署名、SmartScreen警告低減。
- リソース/難易度: 0.5-1人週 / 中（証明書取得別途）
- ライブラリ/技術: Windows SDK signtool
- 参考: [SignTool](https://learn.microsoft.com/windows/win32/seccrypto/signtool)

33) 内部HTTPローカルAPI（オプション連携）
- 概要/実現: ローカルのみのREST APIで外部ツール連携（録音/停止/結果取得）。
- リソース/難易度: 2人週 / 中
- ライブラリ/技術: FastAPI/Flask, threading
- 参考: [FastAPI](https://fastapi.tiangolo.com/)

34) キーワード起動（キーワードスポッティング）
- 概要/実現: 合言葉で録音開始。軽量KWSモデル（Porcupine/Vosk等）。
- リソース/難易度: 2-3人週 / 中-高
- ライブラリ/技術: Porcupine/Picovoice or Vosk
- 参考: [Vosk](https://alphacephei.com/vosk/)

35) メモリ監視と自動フォールバック
- 概要/実現: メモリ使用量が閾値超過時に軽量モデルへ自動切替。
- リソース/難易度: 1人週 / 中
- ライブラリ/技術: psutil, logger_config
- 参考: [psutil](https://psutil.readthedocs.io/)

36) 音声前処理パイプラインGUI（順序と強度）
- 概要/実現: 正規化/ノイズ抑制/VADの順序と強度をGUIで調整。
- リソース/難易度: 1-2人週 / 中
- ライブラリ/技術: numpy, noisereduce, py-webrtcvad, PySide6
- 参考: 上記各ライブラリ

37) アクセス権限/占有チェックのセルフテスト
- 概要/実現: 起動時チェックをUIで再実行、詳細レポートを提示。
- リソース/難易度: 0.5人週 / 低
- ライブラリ/技術: sounddevice, utils/diagnostic_manager
- 参考: 現行実装/`utils/diagnostic_manager.py`

38) 用語ハイライトとコピー単位の選択
- 概要/実現: 特定用語を色付け、選択したセグメント単位でコピー。
- リソース/難易度: 0.5-1人週 / 低-中
- ライブラリ/技術: PySide6, regex
- 参考: Qt Rich Text

39) レイテンシ/処理時間メトリクスの可視化
- 概要/実現: モデルロード・推論時間・I/O遅延をグラフ表示。CSV出力。
- リソース/難易度: 1人週 / 中
- ライブラリ/技術: PySide6 Charts または matplotlib（軽量に）
- 参考: [Qt Charts](https://doc.qt.io/qt-6/qtcharts-index.html)

40) スナップショットログ収集（ワンクリックZIP）
- 概要/実現: `logs/`と設定/バージョン情報をZIP化して保存/共有。
- リソース/難易度: 0.5人週 / 低
- ライブラリ/技術: zipfile, pathlib
- 参考: [zipfile](https://docs.python.org/3/library/zipfile.html)

41) 手動/自動句読点推定モデル（英語中心・任意）
- 概要/実現: シンプルなテキスト正規化 or 軽量モデルで句読点補完。
- リソース/難易度: 1-2人週 / 中
- ライブラリ/技術: simpletransformers/fastpunct（検討）
- 参考: [fastpunct](https://github.com/notAI-tech/fastPunct)

42) フットスイッチ対応（HID）
- 概要/実現: HIDデバイスの押下で録音トグル（ミーティング用途）。
- リソース/難易度: 1-2人週 / 中
- ライブラリ/技術: hidapi/pyhid
- 参考: [hidapi](https://pypi.org/project/hidapi/)

43) 文字起こし品質評価（簡易）
- 概要/実現: 語彙率/疑似WERを算出し品質の相対指標を提示。
- リソース/難易度: 1人週 / 中
- ライブラリ/技術: jiwer（英語中心）, numpy
- 参考: [jiwer](https://github.com/jitsi/jiwer)

44) 既存UIのダークモード対応
- 概要/実現: OSテーマ検出 + 独自テーマ切替。
- リソース/難易度: 0.5人週 / 低
- ライブラリ/技術: PySide6 QPalette/StyleSheet
- 参考: [Qt Style Sheets](https://doc.qt.io/qt-6/stylesheet.html)

45) 外部アプリ連携（カスタムURLスキーム/CLI）
- 概要/実現: `whisper-voice://start`等のURLまたはコマンドで制御。
- リソース/難易度: 2人週 / 中
- ライブラリ/技術: Windowsレジストリ（URLスキーム）, argparse
- 参考: [Windows URL Protocols](https://learn.microsoft.com/windows/win32/shell/progids)

—

注: 難易度/工数は目安であり、要件詳細や品質基準により変動します。優先度決定の際は、現場の体験課題（初回モデルDLの分かりやすさ、マイク占有対策、ログの見える化）を優先することを推奨します。


### 追加アイデア（重複なし・新規30件）

46) リアルタイム翻訳（ja↔en）オーバーレイ
- 概要/実現: 文字起こし結果を逐次機械翻訳し字幕ウィンドウに並行表示（任意でオンラインAPI）。
- リソース/難易度: 2-3人週 / 中
- ライブラリ/技術: transformers(MarianMT)/DeepL API/Google Translate API, PySide6
- 参考: [Helsinki-NLP/Opus-MT](https://huggingface.co/Helsinki-NLP)

47) 語彙ブースト/コンテキストプロンプト
- 概要/実現: 会議議題や人名を事前登録し、`condition_on_previous_text`やプロンプトで誤認低減。
- リソース/難易度: 0.5-1人週 / 低-中
- ライブラリ/技術: faster-whisper オプション活用
- 参考: [faster-whisper options](https://github.com/SYSTRAN/faster-whisper#python)

48) セグメント手動編集・話者タグ付けUI
- 概要/実現: タイムライン上で分割/結合、話者名を手付け。データアノテーションにも活用。
- リソース/難易度: 1-2人週 / 中
- ライブラリ/技術: PySide6, model/view
- 参考: [Qt Model/View](https://doc.qt.io/qt-6/modelview.html)

49) ミーティングモード（長時間・自動区切り・自動保存）
- 概要/実現: 30分ごとなどに自動セッション分割、バックグラウンド保存、再開容易化。
- リソース/難易度: 1-2人週 / 中
- ライブラリ/技術: threading, pathlib
- 参考: 設計指針のみ

50) デバイスホットプラグ検知・自動切替
- 概要/実現: マイク抜き差し検知で安全に再初期化、UI通知。
- リソース/難易度: 1人週 / 中
- ライブラリ/技術: sounddevice, pywin32
- 参考: [sounddevice devices](https://python-sounddevice.readthedocs.io/)

51) プッシュ・トゥ・トーク（PTT）
- 概要/実現: 押している間だけ録音・処理（会議の囁き取りに最適）。
- リソース/難易度: 0.5-1人週 / 低
- ライブラリ/技術: keyboard, PySide6
- 参考: [keyboard](https://pypi.org/project/keyboard/)

52) 単語レベルタイムスタンプ（word timestamps）
- 概要/実現: セグメントより細粒度のタイムスタンプ出力。字幕編集品質向上。
- リソース/難易度: 1人週 / 中
- ライブラリ/技術: faster-whisper `word_timestamps=True`
- 参考: [faster-whisper params](https://github.com/SYSTRAN/faster-whisper#transcription-parameters)

53) 日本語校正・表記ゆれ統一
- 概要/実現: 送り仮名/用字用語をルールで統一、不要スペース・重ね表現を修正。
- リソース/難易度: 1人週 / 中
- ライブラリ/技術: SudachiPy, neologdn, regex
- 参考: [SudachiPy](https://github.com/WorksApplications/SudachiPy)

54) ふりがな/固有名詞推定付与
- 概要/実現: 人名・地名に読みを補助表示（UIツールチップ/括弧）。
- リソース/難易度: 1人週 / 中
- ライブラリ/技術: Janome/SudachiPy
- 参考: [Janome](https://github.com/mocobeta/janome)

55) マルチチャネル入力対応（選択/ミックス）
- 概要/実現: 会議室マイク（2ch以上）で最適チャンネルを選択/合成。
- リソース/難易度: 1人週 / 中
- ライブラリ/技術: sounddevice, numpy
- 参考: [sounddevice streams](https://python-sounddevice.readthedocs.io/)

56) エコーキャンセル/AEC（会議向け）
- 概要/実現: スピーカー音の回り込みを抑制し音声明瞭度を改善。
- リソース/難易度: 2人週 / 中-高
- ライブラリ/技術: webrtc-audio-processing, speexdsp
- 参考: [webrtc-audio-processing](https://chromium.googlesource.com/chromium/src/+/HEAD/third_party/webrtc/modules/audio_processing/)

57) Markdown/Word出力（テンプレ付き）
- 概要/実現: 見出し・箇条書きを整形し、markdown/Word(docx)で保存。
- リソース/難易度: 0.5-1人週 / 低
- ライブラリ/技術: python-docx, markdown
- 参考: [python-docx](https://python-docx.readthedocs.io/)

58) スケジュール/アプリ連動自動開始
- 概要/実現: Zoom/Teams起動検知や指定時刻で録音自動開始・停止。
- リソース/難易度: 1-2人週 / 中
- ライブラリ/技術: psutil, pywin32
- 参考: [psutil](https://psutil.readthedocs.io/)

59) システム音（WASAPIループバック）文字起こし
- 概要/実現: マイクでなくPC出力音の直接取り込みに対応（オンライン会議の字幕化）。
- リソース/難易度: 1-2人週 / 中
- ライブラリ/技術: soundcard/pyaudio(WASAPI)
- 参考: [soundcard](https://github.com/bastibe/SoundCard)

60) アクティブアプリへ自動貼り付け/入力
- 概要/実現: 最終結果を自動でアクティブウィンドウに入力（支援文書作成）。
- リソース/難易度: 0.5-1人週 / 低
- ライブラリ/技術: pyautogui/keyboard
- 参考: [PyAutoGUI](https://pyautogui.readthedocs.io/)

61) スニペット展開（略称→定型文）
- 概要/実現: 辞書に基づき略記を自動展開（医療/法務の定型句など）。
- リソース/難易度: 0.5人週 / 低
- ライブラリ/技術: regex, JSON辞書
- 参考: 設計指針のみ

62) 複数プロファイル（業務/個人/会議など）
- 概要/実現: 設定・辞書・ホットキーをプロファイル単位で切替。
- リソース/難易度: 0.5-1人週 / 低
- ライブラリ/技術: JSON設定, PySide6
- 参考: 設計指針のみ

63) セッションタグ/カテゴリ付与と集計
- 概要/実現: タグで検索/集計し、ダッシュボードで可視化。
- リソース/難易度: 1人週 / 中
- ライブラリ/技術: SQLite/JSON, PySide6
- 参考: [SQLite](https://docs.python.org/3/library/sqlite3.html)

64) 個人情報の自動マスキング
- 概要/実現: 電話番号/住所/メール等を正規表現で伏字化するプライバシーモード。
- リソース/難易度: 0.5-1人週 / 低
- ライブラリ/技術: regex
- 参考: [Regex HOWTO](https://docs.python.org/3/howto/regex.html)

65) 音声の保存（WAV/FLAC）とリンク
- 概要/実現: テキストと音源を紐付け保存、後から検証や再文字起こし。
- リソース/難易度: 0.5-1人週 / 低
- ライブラリ/技術: soundfile, pathlib
- 参考: [SoundFile](https://pysoundfile.readthedocs.io/)

66) ノイズレベル診断とアドバイス
- 概要/実現: 入力RMS/ピークから「距離を詰める/環境騒音注意」等の助言を提示。
- リソース/難易度: 0.5-1人週 / 低
- ライブラリ/技術: numpy, PySide6
- 参考: 基礎音響知識

67) 長時間無音で自動停止・復帰
- 概要/実現: 一定時間の無音で録音停止、音声検出で自動再開（省リソース）。
- リソース/難易度: 0.5-1人週 / 低
- ライブラリ/技術: py-webrtcvad, timers
- 参考: [py-webrtcvad](https://github.com/wiseman/py-webrtcvad)

68) リソースモニタパネル（CPU/RAM/ディスク）
- 概要/実現: 稼働中のシステムリソースをリアルタイム表示。
- リソース/難易度: 0.5-1人週 / 低
- ライブラリ/技術: psutil, PySide6
- 参考: [psutil](https://psutil.readthedocs.io/)

69) Slack/Teams等へのWebhook送信
- 概要/実現: 完了時にチャンネルへ要約/全文をPOST（企業内共有）。
- リソース/難易度: 0.5-1人週 / 低
- ライブラリ/技術: requests, 各サービスWebhook
- 参考: [Slack Incoming Webhooks](https://api.slack.com/messaging/webhooks)

70) 画面キャプションOCRフォールバック
- 概要/実現: 音が取れない場合、画面上の字幕をOCR取得してテキスト化。
- リソース/難易度: 1-2人週 / 中
- ライブラリ/技術: pytesseract, opencv-python
- 参考: [pytesseract](https://pypi.org/project/pytesseract/)

71) 初回セットアップウィザード
- 概要/実現: モデルDL・マイク検証・ホットキー設定をガイド。
- リソース/難易度: 0.5-1人週 / 低
- ライブラリ/技術: PySide6
- 参考: UI設計ベストプラクティス

72) コマンドパレット（Ctrl+K）
- 概要/実現: 機能を検索して即実行するランチャー。
- リソース/難易度: 0.5-1人週 / 低
- ライブラリ/技術: PySide6, キーバインド
- 参考: VSCode風コマンドパレット

73) ポータブルモード（USB配布）
- 概要/実現: 設定/履歴/ログをアプリ配下に相対保存、非管理端末でも動作。
- リソース/難易度: 0.5人週 / 低
- ライブラリ/技術: pathlib, 相対パス管理
- 参考: ポータブルアプリ設計

74) 多言語セグメント分割と表示
- 概要/実現: 言語切替を検出し、セクションごとに言語ラベル付与。
- リソース/難易度: 1人週 / 中
- ライブラリ/技術: faster-whisper language info
- 参考: [faster-whisper language](https://github.com/SYSTRAN/faster-whisper#language-detection)

75) バックエンドプラグイン（Whisper API等の切替）
- 概要/実現: ローカル/クラウド推論を設定で切替できるプラガブル設計。
- リソース/難易度: 2人週 / 中
- ライブラリ/技術: 抽象インターフェース, requests
- 参考: プラグインアーキテクチャ設計


