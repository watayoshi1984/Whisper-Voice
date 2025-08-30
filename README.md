# Whisper Voice MVP

リアルタイム文字起こしアプリケーション MVP版

## 概要

PC上のマイク音声をリアルタイムでテキストに変換するアプリケーションです。OpenAIのWhisper Large-v3 Turboモデルをデフォルトで使用し、完全にオフラインで動作します。

## 主な機能

- ✅ マイク音声のリアルタイム文字起こし
- ✅ シンプルなマイクアイコンUI
- ✅ グローバルホットキー操作 (Ctrl+Shift+S)
- ✅ 自動クリップボードコピー
- ✅ 完全オフライン動作
- ✅ Whisper Large-v3 Turbo による高精度・高速度な文字起こし（デフォルト）
- ✅ 必要に応じて Whisper Large-v3（精度優先）へ切り替え可能
- ✅ ドラッグ可能なフローティングウィンドウ

## 動作環境

- Windows 10/11 (64bit)
- Python 3.10+
- マイクデバイス
- RAM: 4GB以上推奨 (Whisper Large-v3 Turboモデル用)

## セットアップ

### 方法1: Poetry を使用（開発者向け）

```bash
# リポジトリをクローン
git clone <repository-url>
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

1. **起動**: アプリケーションを起動すると、デスクトップ右下にマイクアイコンが表示されます
2. **録音開始**: 以下のいずれかの方法で録音を開始:
   - マイクアイコンをクリック
   - グローバルホットキー `Ctrl+Shift+S` を押下
3. **録音中**: アイコンが赤色に変化し、パルス効果が表示されます
4. **録音停止**: 再度アイコンクリック または `Ctrl+Shift+S` で停止
5. **文字起こし**: 自動的に文字起こしが実行され、結果が表示されます
6. **結果取得**: 文字起こし結果は自動的にクリップボードにコピーされ、他のアプリで `Ctrl+V` で貼り付け可能

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
- リアルタイムストリーミング（現在は録音→文字起こしの方式）
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