"""
AI機能の共通設定モジュール
Azure OpenAI接続設定、クライアント初期化、定数定義
"""
import os
import streamlit as st
from openai import AzureOpenAI
from dotenv import load_dotenv

# .env から読み込み
load_dotenv()

# Azure OpenAI設定
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_KEY")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2025-04-01-preview")
MODEL_NAME = os.getenv("AZURE_OPENAI_MODEL", "gpt-5-mini")

# トークン上限設定（GPT-5-mini最適化）
DEFAULT_MAX_COMPLETION_TOKENS = 5000
YOUTUBE_QUIZ_MAX_COMPLETION_TOKENS = 10000

# reasoning_effort設定（GPT-5-mini用）
# タスクの性質に応じて使い分けることが重要
# 
# minimal: 速度最優先・単純タスク向け
#   - データ抽出（テキストから特定情報を取り出す）
#   - フォーマット変換（JSON変換、整形など）
#   - 簡単な分類（positive/negative/neutralなど）
#   - 短いテキストの書き換え
#   - 速度が重要なリアルタイムアプリケーション
#
# low: 比較的単純な推論タスク向け
#   - 構造化されたコンテンツ生成
#   - 簡単な推論を含むタスク
#   - トークン使用量: 少ない、速度: 速い
#
# medium: 一般的なタスク向け（デフォルト）
#   - 複雑な分析や計画タスク
#   - 包括的な評価・レポート生成
#   - トークン使用量: 中程度、速度: 中程度
#
# high: 複雑な多段階タスク向け（最も遅い）
#   - 大規模な戦略立案
#   - マルチステップの複雑な推論
#   - トークン使用量: 多い、速度: 遅い
#
# 💡 選択指針: コスト削減優先 → minimal/low、品質優先 → medium/high
DEFAULT_REASONING_EFFORT = "minimal"  # 速度最優先の単純タスク用
LOW_REASONING_EFFORT = "low"          # 比較的単純な推論タスク用
COMPLEX_REASONING_EFFORT = "medium"   # 一般的な複雑タスク用

# 接続確認
if not AZURE_OPENAI_ENDPOINT or not AZURE_OPENAI_KEY:
    st.error("AZURE_OPENAI_ENDPOINT / AZURE_OPENAI_KEY が .env に設定されていません。")
    st.stop()

# Azure OpenAI Client初期化
client = AzureOpenAI(
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    api_key=AZURE_OPENAI_KEY,
    api_version=AZURE_OPENAI_API_VERSION,
)

VISION_ENDPOINT = AZURE_OPENAI_ENDPOINT
VISION_KEY = AZURE_OPENAI_KEY


def determine_reasoning_effort(input_length: int, task_complexity: str = "medium") -> str:
    """
    データ量とタスクの複雑さに応じて最適なreasoning_effortを決定
    
    Args:
        input_length: 入力データの長さ（文字数）
        task_complexity: タスクの複雑さ ("simple", "medium", "complex")
        
    Returns:
        最適なreasoning_effort ("minimal", "low", "medium", "high")
        
    Note:
        - simple: データ抽出、分類、短い書き換え
        - medium: 分析、評価、構造化されたコンテンツ生成
        - complex: 多段階推論、戦略立案、包括的なレポート生成
    """
    # タスクの複雑さによる基本設定
    if task_complexity == "simple":
        base_effort = "minimal"
        threshold_low = 1000
        threshold_medium = 5000
    elif task_complexity == "complex":
        base_effort = "medium"
        threshold_low = 500
        threshold_medium = 2000
    else:  # medium
        base_effort = "low"
        threshold_low = 500
        threshold_medium = 2000
    
    # データ量に応じて調整
    if input_length < threshold_low:
        if task_complexity == "simple":
            return "minimal"
        elif task_complexity == "complex":
            return "low"
        else:
            return "minimal"
    elif input_length < threshold_medium:
        if task_complexity == "simple":
            return "minimal"
        elif task_complexity == "complex":
            return "medium"
        else:
            return "low"
    else:
        if task_complexity == "simple":
            return "low"
        elif task_complexity == "complex":
            return "medium"
        else:
            return "medium"


def get_ai_response(prompt, system_content="教育支援AIです。", max_tokens=DEFAULT_MAX_COMPLETION_TOKENS, reasoning_effort=DEFAULT_REASONING_EFFORT):
    """GPT-5-mini用に最適化された汎用AI応答関数
    
    Args:
        prompt: ユーザープロンプト
        system_content: システムプロンプト
        max_tokens: 最大トークン数（デフォルト: 5000）
        reasoning_effort: 推論努力レベル（"minimal", "low", "medium", "high"）
            - minimal: 軽量タスク（抽出、分類、短い書き換え）- 速度優先
            - low: 低い推論努力
            - medium: 標準（複雑なタスク）
            - high: 高い推論努力（マルチステップタスク）
    
    Note:
        GPT-5推論モデルではtemperature、top_p、presence_penalty、
        frequency_penaltyなどのパラメータはサポートされていません。
        max_completion_tokensは推論トークン+出力トークンの合計です。
    """
    try:
        # デバッグ情報（開発時のみ表示）
        if st.session_state.get('debug_mode', False):
            st.write(f"📊 プロンプト長: {len(prompt)}文字")
            st.write(f"🎯 max_tokens: {max_tokens}")
            st.write(f"🤖 モデル: {MODEL_NAME}")
            st.write(f"🧠 reasoning_effort: {reasoning_effort}")
        
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_content},
                {"role": "user", "content": prompt}
            ],
            max_completion_tokens=max_tokens,
            reasoning_effort=reasoning_effort  # GPT-5-mini用パラメーター
        )
        
        # 🔍 詳細なデバッグ情報を表示
        st.write("### 🔍 デバッグ情報")
        st.write(f"**finish_reason**: `{response.choices[0].finish_reason}`")
        st.write(f"**model**: `{response.model}`")
        
        # 使用トークン数を表示（GPT-5推論モデルでは重要）
        if hasattr(response, 'usage') and response.usage:
            st.write("**使用トークン数**:")
            st.write(f"  - プロンプト: `{response.usage.prompt_tokens}` tokens")
            st.write(f"  - 完了: `{response.usage.completion_tokens}` tokens")
            st.write(f"  - 合計: `{response.usage.total_tokens}` tokens")
            
            # GPT-5推論モデルの推論トークンを表示
            if hasattr(response.usage, 'completion_tokens_details'):
                details = response.usage.completion_tokens_details
                if hasattr(details, 'reasoning_tokens') and details.reasoning_tokens:
                    st.write(f"  - 🧠 推論トークン: `{details.reasoning_tokens}` tokens")
                    st.write(f"  - 📝 出力トークン: `{response.usage.completion_tokens - details.reasoning_tokens}` tokens")
        
        # refusalをチェック（GPT-5では重要）
        if hasattr(response.choices[0].message, 'refusal') and response.choices[0].message.refusal:
            st.error(f"🚫 モデルが応答を拒否しました: {response.choices[0].message.refusal}")
            return f"モデルが応答を拒否しました: {response.choices[0].message.refusal}"
        
        result = response.choices[0].message.content
        
        # コンテンツ長をチェック
        content_length = len(result) if result else 0
        st.write(f"**content length**: `{content_length}` 文字")
        
        # finish_reasonの詳細チェック
        if response.choices[0].finish_reason == "content_filter":
            st.error("🚫 Azure Content Safety Filterによりブロックされました")
            st.info("💡 プロンプトまたは生成内容がコンテンツポリシーに違反している可能性があります")
            return "申し訳ありません。コンテンツポリシーにより応答が制限されました。プロンプトを見直してください。"
        
        if response.choices[0].finish_reason == "length":
            st.warning(f"⚠️ トークン制限（{max_tokens}）に達しました。max_tokensを増やしてください。")
            if result:
                st.info("⚠️ 応答が途中で切れている可能性があります")
        
        # 空の応答チェック
        if not result or result.strip() == "":
            st.error(f"⚠️ 空の応答が返されました（finish_reason: `{response.choices[0].finish_reason}`）")
            
            # 完全なresponseオブジェクトをデバッグ表示
            with st.expander("🔍 完全なレスポンスオブジェクト（デバッグ用）"):
                st.json(response.model_dump())
            
            return "申し訳ありません。応答の生成に失敗しました。上記のデバッグ情報を確認してください。"
        
        st.success("✅ 正常に応答を受信しました")
        return result
        
    except Exception as e:
        from openai import (
            APIError, 
            RateLimitError, 
            APIConnectionError,
            AuthenticationError,
            BadRequestError,
            InternalServerError
        )
        from logger import log_error
        
        error_msg = str(e)
        error_type = type(e).__name__
        
        # 詳細なエラー情報をログに記録
        log_error(e, "AI_API_ERROR", details={
            "model": MODEL_NAME,
            "reasoning_effort": reasoning_effort,
            "max_tokens": max_tokens,
            "prompt_length": len(prompt)
        })
        
        # ユーザーフレンドリーなエラーメッセージ
        if isinstance(e, RateLimitError):
            st.error("⏳ レート制限に達しました")
            st.info("💡 しばらく待ってから再試行してください。または、Azure ポータルでクォータを確認してください。")
            return "レート制限に達しました。しばらく待ってから再試行してください。"
        
        elif isinstance(e, APIConnectionError):
            st.error("🔌 接続エラーが発生しました")
            st.info("💡 ネットワーク接続を確認してください。VPNを使用している場合は一時的に無効にしてみてください。")
            return "接続エラー。ネットワークを確認してください。"
        
        elif isinstance(e, AuthenticationError):
            st.error("� 認証エラーが発生しました")
            st.info("💡 .env ファイルの AZURE_OPENAI_KEY を確認してください。")
            return "認証エラー。APIキーを確認してください。"
        
        elif isinstance(e, BadRequestError):
            st.error("⚠️ リクエストエラーが発生しました")
            st.info(f"💡 パラメータまたはプロンプトに問題があります: {error_msg}")
            # プロンプトが長すぎる場合のヒント
            if len(prompt) > 10000:
                st.warning("プロンプトが長すぎる可能性があります。内容を短縮してください。")
            return f"リクエストエラー: {error_msg}"
        
        elif isinstance(e, InternalServerError):
            st.error("🔴 Azure OpenAI サーバーエラー")
            st.info("💡 Azure側で一時的な問題が発生している可能性があります。少し待ってから再試行してください。")
            return "サーバーエラー。しばらく待ってから再試行してください。"
        
        elif isinstance(e, APIError):
            st.error(f"❌ APIエラーが発生しました: {error_msg}")
            st.error(f"エラーの種類: {error_type}")
            return f"APIエラー: {error_msg}"
        
        else:
            # その他の予期しないエラー
            st.error(f"❌ 予期しないエラーが発生しました: {error_msg}")
            st.error(f"エラーの種類: {error_type}")
            
            # デバッグ情報を展開可能な形で表示
            with st.expander("🔍 詳細なエラー情報（開発者向け）"):
                st.code(error_msg)
                import traceback
                st.code(traceback.format_exc())
            
            return f"申し訳ありません。エラーが発生しました: {error_type}"


def call_api_with_retry(func, max_retries=3, initial_wait=1, backoff_factor=2):
    """API呼び出しをリトライ機能付きで実行する汎用関数
    
    Args:
        func: 呼び出す関数（lambda等）
        max_retries: 最大リトライ回数
        initial_wait: 初回の待機時間（秒）
        backoff_factor: リトライごとに待機時間を増やす倍率
    
    Returns:
        funcの実行結果
    
    Raises:
        最後のリトライでも失敗した場合、例外を再送出
    """
    import time
    
    wait_time = initial_wait
    last_exception = None
    
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            last_exception = e
            if attempt < max_retries - 1:
                st.warning(f"⚠️ エラーが発生しました（{attempt + 1}/{max_retries}回目）: {str(e)}")
                st.info(f"⏳ {wait_time}秒待機してリトライします...")
                time.sleep(wait_time)
                wait_time *= backoff_factor
            else:
                st.error(f"❌ {max_retries}回リトライしましたが失敗しました")
    
    # 最後のリトライでも失敗した場合
    raise last_exception


def test_azure_openai_connection():
    """Azure OpenAI (GPT-5-mini) 接続をテストする関数"""
    st.write("### Azure OpenAI (GPT-5-mini) 接続テスト")
    
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "user", "content": "こんにちは。接続テストです。短く返答してください。"}
            ],
            max_completion_tokens=100
        )
        
        result = response.choices[0].message.content
        st.success(f"Azure OpenAI接続成功 (モデル: {MODEL_NAME})")
        st.write(f"応答: {result}")
        return True
        
    except Exception as e:
        st.error("Azure OpenAI接続失敗")
        st.error(f"エラー詳細: {str(e)}")
        return False
