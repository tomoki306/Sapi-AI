"""
環境変数検証モジュール
.envファイルの必須変数が正しく設定されているか確認
"""

import os
import streamlit as st


def validate_env_variables():
    """必須の環境変数が設定されているか確認"""
    required_vars = {
        "AZURE_OPENAI_ENDPOINT": "Azure OpenAI のエンドポイントURL",
        "AZURE_OPENAI_KEY": "Azure OpenAI の APIキー",
        "AZURE_OPENAI_API_VERSION": "Azure OpenAI の APIバージョン",
        "AZURE_OPENAI_MODEL": "使用するモデル名（例: gpt-5-mini）"
    }
    
    missing = []
    invalid = []
    
    for var, description in required_vars.items():
        value = os.getenv(var)
        
        if not value:
            missing.append(f"- {var}: {description}")
        else:
            # 値の妥当性チェック
            if var == "AZURE_OPENAI_ENDPOINT":
                if not value.startswith("https://"):
                    invalid.append(f"- {var}: URLは https:// で始まる必要があります（現在: {value[:30]}...）")
            
            elif var == "AZURE_OPENAI_KEY":
                if len(value) < 20:
                    invalid.append(f"- {var}: APIキーの長さが短すぎます（現在: {len(value)}文字）")
            
            elif var == "AZURE_OPENAI_API_VERSION":
                if not value.startswith("202"):
                    invalid.append(f"- {var}: APIバージョンは 202X-XX-XX 形式である必要があります（現在: {value}）")
    
    # エラー表示
    if missing or invalid:
        st.error("⚠️ 環境変数の設定に問題があります")
        
        if missing:
            st.error("### 未設定の環境変数")
            st.markdown("\n".join(missing))
        
        if invalid:
            st.error("### 不正な環境変数")
            st.markdown("\n".join(invalid))
        
        st.info("### 📝 解決方法")
        st.markdown("""
        1. プロジェクトのルートディレクトリに `.env` ファイルを作成
        2. 以下の形式で環境変数を設定:
        ```
        AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
        AZURE_OPENAI_KEY=your-api-key-here
        AZURE_OPENAI_API_VERSION=2025-04-01-preview
        AZURE_OPENAI_MODEL=gpt-5-mini
        ```
        3. アプリを再起動
        """)
        
        st.stop()
    
    st.success("✅ 環境変数の検証が完了しました")


def validate_optional_env_variables():
    """オプションの環境変数のチェック（警告のみ）"""
    optional_vars = {
        "VOICE_AZURE_OPENAI_KEY": "音声機能用のAPIキー（未設定の場合は通常のキーを使用）",
        "VOICE_GPT_DEPLOYMENT_NAME": "音声機能用のモデル名",
        "VOICE_TTS_DEPLOYMENT_NAME": "音声合成用のデプロイメント名",
        "VOICE_STT_DEPLOYMENT_NAME": "音声認識用のデプロイメント名"
    }
    
    missing_optional = []
    
    for var, description in optional_vars.items():
        if not os.getenv(var):
            missing_optional.append(f"- {var}: {description}")
    
    if missing_optional:
        with st.expander("💡 オプション環境変数の設定推奨"):
            st.info("以下の環境変数は未設定ですが、デフォルト値で動作します:")
            st.markdown("\n".join(missing_optional))


def display_env_status():
    """環境変数の設定状況を表示（デバッグ用）"""
    with st.expander("🔍 環境変数の設定状況"):
        required_vars = [
            "AZURE_OPENAI_ENDPOINT",
            "AZURE_OPENAI_KEY",
            "AZURE_OPENAI_API_VERSION",
            "AZURE_OPENAI_MODEL"
        ]
        
        for var in required_vars:
            value = os.getenv(var)
            if value:
                # APIキーは一部のみ表示
                if "KEY" in var:
                    display_value = f"{value[:8]}...{value[-4:]}" if len(value) > 12 else "****"
                else:
                    display_value = value
                
                st.success(f"✅ {var}: `{display_value}`")
            else:
                st.error(f"❌ {var}: 未設定")
