# Sapi-AI 学習管理システム

AIを活用した統合学習管理アプリケーション

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/streamlit-1.28%2B-FF4B4B)](https://streamlit.io/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

## 🚀 クイックスタート

```bash
# 1. リポジトリをクローン
git clone https://github.com/tomoki306/Sapi-AI.git
cd Sapi-AI

# 2. 依存パッケージをインストール
pip install -r requirements.txt

# 3. 環境変数を設定
cp .env.example .env
# .envファイルを編集してAzure OpenAI APIキーを設定

# 4. セットアップを確認
python3 check_setup.py

# 5. アプリケーションを起動
streamlit run app.py
```

## 📋 目次

- [概要](#概要)
- [主な機能](#主な機能)
- [必要な環境](#必要な環境)
- [セットアップ手順](#セットアップ手順)
- [使い方](#使い方)
- [プロジェクト構造](#プロジェクト構造)
- [トラブルシューティング](#トラブルシューティング)
- [開発情報](#開発情報)
- [貢献](#貢献)
- [ライセンス](#ライセンス)

## 概要

Sapi-AIは、学習の記録、進捗管理、成績分析、AI支援機能を統合した学習管理システムです。Azure OpenAI APIを活用し、成績評価、論文解説、翻訳、回答分析など、さまざまなAI機能を提供します。

## 主な機能

### 📝 学習管理
- **科目登録**: 科目の追加・管理
- **進捗ダッシュボード**: 学習状況の可視化
- **学習目標設定**: 目標の設定と進捗追跡
- **学習計画作成**: 効果的な学習計画の立案
- **リマインダー**: 学習タスクの通知機能

### 📊 成績管理
- **成績記録**: テスト・課題の成績入力
- **成績検索**: 過去の成績の検索・フィルタリング
- **統計レポート**: 成績の統計分析

### 📈 分析・予測
- **高度な成績分析**: 詳細な成績トレンド分析
- **成績予測**: 機械学習による成績予測
- **高度な可視化**: インタラクティブなグラフとチャート

### 🤖 AI機能 (Azure OpenAI)
- **成績評価**: AIによる成績の評価とフィードバック
- **論文解説**: 学術論文の要約と解説
- **翻訳**: 多言語翻訳機能
- **回答分析**: 学習内容の理解度分析
- **YouTube問題生成**: 動画から自動で問題を生成
- **学習レポート生成**: AIによる包括的な学習レポート

### ⚙️ データ管理
- **一括操作**: データの一括インポート・エクスポート
- **データ管理**: バックアップと復元
- **テンプレート管理**: よく使う設定のテンプレート化
- **CSVエクスポート**: データのCSV形式でのエクスポート

## 必要な環境

以下のバージョンで動作確認済みです：

- **Python**: 3.13.5 以上 (Python 3.8以上推奨)
- **pip**: 25.1 以上
- **Git**: 2.39.5 以上
- **OS**: macOS, Windows, Linux

## セットアップ手順

### 1. リポジトリのクローン

```bash
git clone https://github.com/tomoki306/Sapi-AI.git
cd Sapi-AI
```

### 2. Python仮想環境の作成（推奨）

```bash
# 仮想環境の作成
python3 -m venv venv

# 仮想環境の有効化
# macOS/Linux:
source venv/bin/activate

# Windows:
# venv\Scripts\activate
```

### 3. 依存パッケージのインストール

```bash
pip install -r requirements.txt
```

必要なパッケージ一覧：
- `streamlit>=1.28.0` - Webアプリケーションフレームワーク
- `pandas>=2.0.0` - データ処理
- `numpy>=1.24.0` - 数値計算
- `openai>=1.0.0` - Azure OpenAI API
- `scikit-learn>=1.7.0` - 機械学習
- `python-dotenv>=1.0.0` - 環境変数管理
- `plotly>=5.17.0` - インタラクティブな可視化
- `matplotlib>=3.7.0` - グラフ作成
- `youtube-transcript-api>=0.6.0` - YouTube字幕取得
- `audio-recorder-streamlit>=0.0.8` - 音声録音機能

### 4. 環境変数の設定

`.env.example`ファイルを`.env`にコピーして、必要な環境変数を設定します：

```bash
cp .env.example .env
```

`.env`ファイルを編集して、以下の環境変数を設定してください：

```bash
# Azure OpenAI API設定（必須）
AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com/
AZURE_OPENAI_KEY=your_api_key_here
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_MODEL=gpt-4

# 音声機能用の設定（オプション）
VOICE_AZURE_OPENAI_ENDPOINT=https://your-voice-resource.openai.azure.com/
VOICE_AZURE_OPENAI_KEY=your_voice_api_key_here
VOICE_AZURE_OPENAI_API_VERSION=2024-02-15-preview
VOICE_TTS_DEPLOYMENT_NAME=tts-1
VOICE_STT_DEPLOYMENT_NAME=whisper-1
```

#### Azure OpenAI APIの取得方法

1. [Azure Portal](https://portal.azure.com/)にログイン
2. 「Azure OpenAI」サービスを作成
3. リソースを作成後、「キーとエンドポイント」から必要な情報を取得
4. モデルのデプロイメントを作成（例：gpt-4, gpt-35-turbo）

### 5. .env.exampleファイルの作成

リポジトリに`.env.example`ファイルを作成します：

```bash
cat > .env.example << 'EOF'
# Azure OpenAI API設定（必須）
AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com/
AZURE_OPENAI_KEY=your_api_key_here
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_MODEL=gpt-4

# 音声機能用の設定（オプション）
VOICE_AZURE_OPENAI_ENDPOINT=https://your-voice-resource.openai.azure.com/
VOICE_AZURE_OPENAI_KEY=your_voice_api_key_here
VOICE_AZURE_OPENAI_API_VERSION=2024-02-15-preview
VOICE_TTS_DEPLOYMENT_NAME=tts-1
VOICE_STT_DEPLOYMENT_NAME=whisper-1
EOF
```

## 使い方

### アプリケーションの起動

```bash
streamlit run app.py
```

ブラウザで自動的に `http://localhost:8501` が開きます。

### 初回起動時の設定

1. **科目登録**: サイドバーから「科目登録」を選択し、学習する科目を登録
2. **学習目標設定**: 「学習目標設定」で目標を設定
3. **リマインダー設定**: 「リマインダー」で通知を設定

### 主な使用フロー

1. **科目の登録**: 学習する科目を登録
2. **進捗の記録**: 学習した内容を記録
3. **成績の入力**: テストや課題の成績を入力
4. **AI機能の活用**: 成績評価、論文解説、翻訳などのAI機能を利用
5. **分析とレポート**: 学習状況を分析し、レポートを生成

## プロジェクト構造

```
Sapi-AI/
├── app.py                          # メインアプリケーション
├── requirements.txt                # 依存パッケージ
├── .env                           # 環境変数（要作成）
├── .env.example                   # 環境変数テンプレート
│
├── 学習管理機能
│   ├── subject.py                 # 科目管理
│   ├── progress.py                # 進捗管理
│   ├── goal.py                    # 目標設定
│   ├── goal_progress.py           # 目標進捗追跡
│   ├── planning.py                # 学習計画
│   └── reminder.py                # リマインダー
│
├── 成績管理機能
│   ├── grade.py                   # 成績記録
│   ├── grade_analytics.py         # 成績分析
│   ├── grade_prediction.py        # 成績予測
│   └── ml_grade_prediction.py     # ML成績予測
│
├── AI機能
│   ├── ai_config.py               # AI設定
│   ├── ai_functions.py            # AI共通関数
│   ├── ai_grade_evaluation.py     # 成績評価
│   ├── ai_paper_explanation.py    # 論文解説
│   ├── ai_translation.py          # 翻訳
│   ├── ai_answer_analysis.py      # 回答分析
│   ├── ai_youtube_quiz.py         # YouTube問題生成
│   ├── ai_study_plan.py           # 学習計画生成
│   └── ai_learning_report.py      # 学習レポート
│
├── データ管理
│   ├── data.py                    # データ基本操作
│   ├── data_management.py         # データ管理
│   ├── data_integrity.py          # データ整合性
│   ├── backup_manager.py          # バックアップ
│   ├── bulk_operations.py         # 一括操作
│   └── csv_export_enhanced.py     # CSVエクスポート
│
├── 可視化・レポート
│   ├── dashboard.py               # ダッシュボード
│   ├── enhanced_visualization.py  # 高度な可視化
│   ├── report.py                  # レポート生成
│   └── auto_reports.py            # 自動レポート
│
├── ユーティリティ
│   ├── logger.py                  # ログ管理
│   ├── validators.py              # バリデーション
│   ├── env_validator.py           # 環境変数検証
│   ├── templates.py               # テンプレート管理
│   └── cache_optimization.py      # キャッシュ最適化
│
├── データファイル
│   ├── subjects.json              # 科目データ
│   ├── grades.json                # 成績データ
│   ├── goals.json                 # 目標データ
│   ├── progress.json              # 進捗データ
│   ├── reminders.json             # リマインダー
│   ├── notes.json                 # メモ・ノート
│   └── study_plans.json           # 学習計画
│
└── ディレクトリ
    ├── backups/                   # バックアップファイル
    ├── ml_models/                 # 機械学習モデル
    ├── reports/                   # 生成されたレポート
    └── __pycache__/               # Pythonキャッシュ
```

## トラブルシューティング

### よくある問題と解決方法

#### 1. モジュールが見つからないエラー

```bash
ModuleNotFoundError: No module named 'streamlit'
```

**解決方法**: 依存パッケージを再インストール

```bash
pip install -r requirements.txt
```

#### 2. Azure OpenAI APIエラー

```
❌ .env ファイルが見つかりません
```

**解決方法**: `.env`ファイルを作成し、必要な環境変数を設定

```bash
cp .env.example .env
# .envファイルを編集してAPIキーを設定
```

#### 3. ポートが使用中

```
Port 8501 is already in use
```

**解決方法**: 別のポートを指定してアプリケーションを起動

```bash
streamlit run app.py --server.port 8502
```

#### 4. データファイルが読み込めない

**解決方法**: JSONファイルの整合性を確認

```bash
# アプリ内の「データ管理」→「データ整合性チェック」を実行
```

### ログファイルの確認

問題が発生した場合は、`app.log`ファイルを確認してください：

```bash
tail -f app.log
```

## 開発情報

### 使用技術

- **フロントエンド**: Streamlit
- **バックエンド**: Python
- **AI/ML**: Azure OpenAI API, scikit-learn
- **データ処理**: Pandas, NumPy
- **可視化**: Plotly, Matplotlib

### 動作環境（確認済み）

- Python 3.13.5
- Streamlit 1.45.1
- pip 25.1
- Git 2.39.5
- macOS (Apple Git-154)

## 貢献

プロジェクトへの貢献を歓迎します！詳細は[CONTRIBUTING.md](CONTRIBUTING.md)をご覧ください。

### 開発に貢献する

1. このリポジトリをフォーク
2. 新しいブランチを作成 (`git checkout -b feature/amazing-feature`)
3. 変更をコミット (`git commit -m 'Add some amazing feature'`)
4. ブランチにプッシュ (`git push origin feature/amazing-feature`)
5. プルリクエストを作成

## セキュリティに関する注意

- `.env`ファイルは**絶対にGitにコミットしないでください**
- APIキーは安全に管理してください
- `.gitignore`に`.env`が含まれていることを確認してください

## ライセンス

このプロジェクトのライセンスについては、リポジトリの管理者にお問い合わせください。

## 連絡先

プロジェクト管理者: [@tomoki306](https://github.com/tomoki306)

リポジトリ: [https://github.com/tomoki306/Sapi-AI](https://github.com/tomoki306/Sapi-AI)

---

⭐ このプロジェクトが役に立った場合は、スターをつけていただけると嬉しいです！