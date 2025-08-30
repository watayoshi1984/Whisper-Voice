# Whisper Voice MVP

音声文字起こしアプリケーション MVP版

## 概要

PC上のマイク音声をテキストに変換するアプリケーションです。OpenAIのWhisper Large-v3 Turboモデルをデフォルトで使用し、完全にオフラインで動作します。

## 主な機能

- ✅ マイク音声の文字起こし
- ✅ 透過背景のマイクアイコンUI
- ✅ グローバルホットキー操作 (Ctrl+Shift+S)
- ✅ 自動クリップボードコピー
- ✅ 完全オフライン動作
- ✅ Whisper Large-v3 Turbo による高精度・高速度な文字起こし（デフォルト）
- ✅ Whisper Large-v3（精度優先）とのリアルタイム切り替え
- ✅ ドラッグ可能なフローティングウィンドウ
- ✅ WebRTCノイズ除去機能
- ✅ 編集可能な文字起こし結果ダイアログ（コピー・クリア機能付き）

## 動作環境

- Windows 10/11 (64bit)
- Python 3.10+
- マイクデバイス
- RAM: 4GB以上推奨 (Whisper Large-v3 Turboモデル用)

## セットアップ

### 方法1: Poetry を使用（開発者向け）

```bash
# リポジトリをクローン
git clone https://github.com/watayoshi1984/Whisper-Voice.git
cd Whisper-Voice

# Poetry を使用して依存関係をインストール
poetry install

# 仮想環境をアクティベート
poetry shell
```

### 方法2: 簡単セットアップ（開発者向け）

```bash
# 開発用スクリプトを使用
python run_dev.py install
```

### 方法3: 実行ファイル版（一般ユーザー向け）

```bash
# 実行ファイルを生成
python build_exe.py

# dist/WhisperVoiceMVP.exe を実行
```

## 使用方法

### 開発環境での実行

```bash
# 方法1: Poetry経由
poetry run python src/main.py

# 方法2: 開発スクリプト経由
python run_dev.py run
```

### アプリケーションの操作

1. **起動**: アプリケーションを起動すると、デスクトップ右下に透過背景のマイクアイコンが表示されます
2. **モデル切り替え**: 上部のボタンでWhisperモデルを切り替え:
   - 「v3」（緑）= large-v3（高精度・低速）
   - 「turbo」（青）= large-v3-turbo（中精度・高速）
3. **録音開始**: 以下のいずれかの方法で録音を開始:
   - マイクアイコンをクリック
   - グローバルホットキー `Ctrl+Shift+S` を押下
4. **録音中**: アイコンが赤色に変化し、パルス効果が表示されます
5. **録音停止**: 再度アイコンクリック または `Ctrl+Shift+S` で停止
6. **文字起こし**: 自動的に文字起こしが実行され、結果が表示されます
7. **結果編集**: 文字起こし結果ダイアログで内容を編集・コピー・クリア可能
8. **結果取得**: 文字起こし結果は自動的にクリップボードにコピーされ、他のアプリで `Ctrl+V` で貼り付け可能

### UI状態の説明

| 状態 | アイコン色 | 説明 |
|------|------------|------|
| 待機中 | 緑色 | 録音待機状態 |
| 録音中 | 赤色（パルス効果） | 音声録音中 |
| 処理中 | オレンジ色 | 文字起こし処理中 |

## テスト実行

```bash
# テストを実行
python run_dev.py test

# または直接pytest実行
poetry run pytest tests/ -v
```

## 実行ファイル生成

```bash
# .exeファイルの生成
python build_exe.py

# 生成されたファイル: dist/WhisperVoiceMVP.exe
```

## モデル選択

デフォルトのモデルは large-v3-turbo です。精度を優先したい場合は large-v3 に切り替えできます。

- 開発実行スクリプト経由:
  - 速度・バランス（デフォルト）: `python run_dev.py run --model large-v3-turbo`
  - 精度優先: `python run_dev.py run --model large-v3`
- 直接実行/Poetry経由:
  - `poetry run python src/main.py --model large-v3`
- 環境変数で指定（CLI指定が優先されます）:
  - PowerShell: `$env:WHISPER_MODEL="large-v3"; python run_dev.py run`
  - CMD: `set WHISPER_MODEL=large-v3 && python run_dev.py run`

フォールバック: 選択モデルのダウンロード/ロードに失敗した場合、自動的に `large-v3` や軽量モデルへフォールバックします。

## アーキテクチャ

```
src/
├── main.py                 # エントリーポイント
├── app/
│   ├── core.py             # メインアプリケーションロジック
│   ├── audio_processor.py  # 音声処理（録音、デバイス管理）
│   ├── transcriber.py      # Whisper文字起こしエンジン
│   └── ui/
│       └── main_window.py  # PySide6 GUI
└── utils/
    ├── clipboard.py        # クリップボード操作
    └── hotkey.py           # グローバルホットキー
```

## 技術スタック

| カテゴリ | ライブラリ | 用途 |
|----------|------------|------|
| AI/ML | faster-whisper | 音声文字起こし |
| GUI | PySide6 | ユーザーインターフェース |
| 音声処理 | sounddevice | 音声入力 |
| 音声フォーマット | soundfile | 音声ファイル処理 |
| ノイズ除去 | webrtcvad | 音声活動検出 |
| ノイズ除去 | noisereduce | スペクトラル減算 |
| 信号処理 | scipy | 音声フィルタリング |
| システム | keyboard | グローバルホットキー |
| システム | pyperclip | クリップボード操作 |
| パッケージング | PyInstaller | 実行ファイル生成 |

## トラブルシューティング

### よくある問題

**Q: マイクアイコンが表示されない**
- A: マイクデバイスの接続を確認してください
- A: Windowsの音声設定でマイクが有効になっているか確認

**Q: 文字起こしができない**
- A: 初回起動時はWhisperモデルのダウンロードに時間がかかります
- A: しばらく待ってから再試行してください
- A: 十分な音量で話してください

**Q: ホットキーが効かない**
- A: 管理者権限でアプリケーションを実行してみてください
- A: 他のアプリケーションが同じホットキーを使用していないか確認

**Q: 文字起こし精度が低い**
- A: マイクに近づいて、はっきりと話してください
- A: 周囲の雑音を減らしてください
- A: 日本語で話してください（日本語に最適化されています）

**Q: アプリケーションが重い**
- A: Whisper Large-v3は計算量が多いため、高性能PCが推奨されます
- A: 他の重いアプリケーションを閉じてください

### ログ確認

開発環境では、コンソールにログが表示されます：

```bash
# ログ出力付きで実行
python run_dev.py run
```

### サポート対象外

- macOS、Linux
- 複数言語同時認識
- 話者識別機能

## 開発

### 開発環境セットアップ

```bash
# Poetry インストール（まだの場合）
curl -sSL https://install.python-poetry.org | python3 -

# プロジェクトセットアップ
git clone <repository>
cd Whisper-Voice
python run_dev.py install
```

### コードスタイル

```bash
# フォーマット
poetry run black src/ tests/

# リント
poetry run ruff src/ tests/
```

### 貢献

1. このリポジトリをフォーク
2. 機能ブランチを作成 (`git checkout -b feature/amazing-feature`)
3. 変更をコミット (`git commit -m 'Add amazing feature'`)
4. ブランチにプッシュ (`git push origin feature/amazing-feature`)
5. プルリクエストを作成

## ライセンス

MIT License

## 免責事項

- 本アプリケーションはMVP（最小実行可能製品）版です
- 音声認識の精度は100%ではありません
- 重要な会議や文書作成には十分な確認を行ってください

## 変更履歴 (Changelog)

### v1.2.0 - 2024-12-XX

#### 追加機能
- ✨ **透過背景UI**: マイクアイコンの背景を透明化、デスクトップに溶け込むデザイン
- ✨ **Whisperモデル切り替え**: UIからリアルタイムでv3/v3-turboモデルを切り替え可能
- ✨ **WebRTCノイズ除去**: 環境音を除去する高度なノイズ処理機能
- ✨ **編集可能文字起こし結果**: コピー・クリア機能付きの編集可能テキストダイアログ
- ✨ **改良されたマイクアイコン**: 影とグリル詳細を追加したモダンなデザイン

#### 改善
- 🔧 **音声処理の安定性向上**: 短い音声データでのフィルタエラーを修正
- 🔧 **UIレスポンシブ性**: ウィンドウサイズ調整とレイアウト最適化
- 🔧 **エラーハンドリング強化**: ノイズ除去処理の例外処理を改善

#### 技術的変更
- 📦 **新依存関係**: scipy, webrtcvad, noisereduceを追加
- 🏗️ **アーキテクチャ改善**: モデル動的切り替え機能の実装
- 🧹 **コード整理**: リアルタイム機能を一時保留（将来の実装に向けて）

#### 既知の問題
- ⚠️ リアルタイムストリーミング機能は遅延のため一時保留中
- ⚠️ ノイズ除去は短い音声（0.5秒未満）では無効化されます

### v1.1.0 - 2024-12-XX

#### 初期機能
- 🎤 基本的な音声文字起こし機能
- 🖼️ シンプルなマイクアイコンUI
- ⌨️ グローバルホットキー対応
- 📋 自動クリップボードコピー
- 🔄 Whisperモデル選択機能



<a href="https://ko-fi.com/watayoshi1984">
  <img src="https://cdn.ko-fi.com/cdn/kofi3.png?v=3" height="50" width="210" alt="watayoshi1984" />
</a>

