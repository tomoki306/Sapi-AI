"""
翻訳AI機能モジュール
多言語翻訳機能
"""
import streamlit as st
from ai_config import get_ai_response, DEFAULT_REASONING_EFFORT
from data import get_user_profile

# 対応言語リスト
LANGUAGES_SOURCE = ["自動", "英語", "日本語", "韓国語", "中国語", "スペイン語"]
LANGUAGES_TARGET = ["英語", "日本語", "韓国語", "中国語", "スペイン語"]


def display_translation():
    """翻訳UIの表示"""
    st.subheader("翻訳")
    source_text = st.text_area("翻訳したいテキストを入力してください")
    
    source_lang = st.selectbox("翻訳元の言語を選択してください", LANGUAGES_SOURCE)
    target_lang = st.selectbox("翻訳先の言語を選択してください", LANGUAGES_TARGET)
    
    if st.button("翻訳を実行"):
        if not source_text.strip():
            st.warning("翻訳したいテキストを入力してください")
            return
            
        # ユーザープロフィールの取得
        user_profile = get_user_profile()
        vocabulary_level = ""
        if user_profile.get("education_level"):
            edu_level = user_profile["education_level"]
            if edu_level in ["小学生", "中学生"]:
                vocabulary_level = "平易で日常的な語彙を使用。"
            elif edu_level == "高校生":
                vocabulary_level = "一般的な語彙で、適度に専門用語も使用。"
            elif edu_level in ["大学生", "大学院生"]:
                vocabulary_level = "専門用語や学術的表現を適切に使用。"
        
        # GPT-5-mini向けに最適化
        system_prompt = f"プロ翻訳者です。{vocabulary_level}正確で自然な翻訳を提供します。"
        prompt = f"以下のテキストを{source_lang}から{target_lang}に翻訳してください。翻訳結果は{target_lang}のみで返してください:\n{source_text}"
        
        with st.spinner(f"{source_lang}から{target_lang}へ翻訳中..."):
            # 翻訳はシンプルな変換タスクなのでreasoning_effort='minimal'を使用（速度優先）
            response = get_ai_response(prompt, system_prompt, reasoning_effort=DEFAULT_REASONING_EFFORT)
        
        st.markdown("### 🌐 翻訳結果")
        st.write(response)
