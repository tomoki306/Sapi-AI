# 貢献ガイドライン

Sapi-AIプロジェクトへの貢献に興味を持っていただきありがとうございます！このドキュメントでは、プロジェクトに貢献する方法について説明します。

## 貢献の方法

### バグ報告

バグを見つけた場合は、以下の情報を含めてIssueを作成してください：

- **バグの説明**: 何が起きたか
- **再現手順**: バグを再現する手順
- **期待される動作**: 本来どう動作すべきか
- **環境情報**: 
  - OS（例：macOS 14.0）
  - Pythonバージョン（例：Python 3.13.5）
  - Streamlitバージョン（例：1.45.1）
- **スクリーンショット**: 可能であれば

### 機能提案

新しい機能を提案する場合は、以下を含めてください：

- **機能の説明**: 何を追加したいか
- **使用例**: どのように使われるか
- **利点**: なぜこの機能が必要か

### コードの貢献

#### 準備

1. リポジトリをフォーク
2. ローカルにクローン
   ```bash
   git clone https://github.com/YOUR_USERNAME/Sapi-AI.git
   cd Sapi-AI
   ```
3. 開発用ブランチを作成
   ```bash
   git checkout -b feature/your-feature-name
   ```

#### 開発

1. 仮想環境を作成・有効化
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # macOS/Linux
   ```

2. 依存パッケージをインストール
   ```bash
   pip install -r requirements.txt
   ```

3. 環境変数を設定
   ```bash
   cp .env.example .env
   # .envファイルを編集
   ```

4. コードを変更

5. 動作確認
   ```bash
   streamlit run app.py
   ```

#### コーディング規約

- **Python Style**: PEP 8に従う
- **インデント**: スペース4つ
- **命名規則**:
  - 関数名: `snake_case`
  - クラス名: `PascalCase`
  - 定数: `UPPER_CASE`
- **コメント**: 日本語で記述可
- **Docstring**: 関数やクラスには説明を追加

例：
```python
def calculate_average_grade(grades: list) -> float:
    """
    成績リストから平均を計算する
    
    Args:
        grades (list): 成績のリスト
        
    Returns:
        float: 平均成績
    """
    return sum(grades) / len(grades)
```

#### コミット

- コミットメッセージは分かりやすく
- 日本語または英語で記述
- 1つのコミットには1つの変更

良い例：
```bash
git commit -m "成績予測機能に新しいアルゴリズムを追加"
git commit -m "Add new algorithm to grade prediction feature"
```

悪い例：
```bash
git commit -m "update"
git commit -m "fix"
```

#### プルリクエスト

1. 変更をプッシュ
   ```bash
   git push origin feature/your-feature-name
   ```

2. GitHubでプルリクエストを作成

3. プルリクエストの説明に以下を含める：
   - 変更内容の説明
   - 関連するIssue番号（あれば）
   - テスト方法
   - スクリーンショット（UIの変更の場合）

## プロジェクト構造の理解

主要なモジュールの責務：

- `app.py`: メインアプリケーション、ルーティング
- `data.py`: データの基本操作
- `ai_*.py`: AI機能の実装
- `grade*.py`: 成績管理関連
- `*_management.py`: 管理機能

新しい機能を追加する場合は、適切なモジュールに配置するか、新しいモジュールを作成してください。

## テスト

現在、テストフレームワークは実装中です。将来的には以下のテストが必要になります：

- ユニットテスト
- 統合テスト
- UIテスト

## ドキュメント

コードの変更に伴い、以下のドキュメントも更新してください：

- README.md: 新機能の追加や使用方法の変更
- docstring: 関数やクラスの説明
- コメント: 複雑なロジックの説明

## 質問やサポート

質問がある場合は：

1. まずREADME.mdとドキュメントを確認
2. 既存のIssueを検索
3. 新しいIssueを作成

## 行動規範

- 敬意を持って接する
- 建設的なフィードバックを心がける
- 多様性を尊重する
- プロフェッショナルな態度を保つ

## ライセンス

このプロジェクトに貢献することで、あなたの貢献が現在のプロジェクトライセンスの下で公開されることに同意したものとみなされます。

---

ご協力ありがとうございます！ 🎉
