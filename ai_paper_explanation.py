"""
論文解説AI機能モジュール
論文内容の要約と重要ポイントの抽出
"""
import streamlit as st
from ai_config import get_ai_response, COMPLEX_REASONING_EFFORT
from data import get_user_profile


def display_paper_explanation():
    """論文解説UIの表示"""
    st.subheader("論文解説")
    paper_text = st.text_area("論文の内容を入力してください")
    
    if st.button("解説を取得"):
        if not paper_text.strip():
            st.warning("論文の内容を入力してください")
            return
            
        # ユーザープロフィールの取得
        user_profile = get_user_profile()
        explanation_level = ""
        if user_profile.get("education_level"):
            edu_level = user_profile["education_level"]
            if edu_level in ["小学生", "中学生"]:
                explanation_level = "小中学生でも理解できるよう、専門用語を避け、たとえ話を使って優しく説明してください。"
            elif edu_level == "高校生":
                explanation_level = "高校生レベルの知識を前提に、基本的な専門用語は使いつつ、わかりやすく説明してください。"
            elif edu_level == "大学生":
                explanation_level = "大学生レベルの知識を前提に、専門用語を使って詳しく説明してください。"
            elif edu_level == "大学院生":
                explanation_level = "大学院レベルの深い理解を前提に、学術的な観点から詳細に分析してください。"
        
        prompt = f"以下の論文内容を分かりやすく要約し、重要なポイントを3つ挙げてください。{explanation_level}\n\n【論文内容】\n{paper_text}"
        
        with st.spinner("AIが論文を解説しています..."):
            # 論文理解は複雑なタスクなのでreasoning_effort='medium'を使用
            response = get_ai_response(prompt, reasoning_effort=COMPLEX_REASONING_EFFORT)
        
        st.markdown("### 📝 解説結果")
        st.write(response)
