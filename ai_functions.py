"""
AI機能統合モジュール（リファクタリング版）
各AI機能を分割モジュールから読み込み、UIルーティングのみを担当

ファイル構成:
- ai_config.py: 共通設定とAI応答関数
- ai_grade_evaluation.py: 成績評価機能
- ai_paper_explanation.py: 論文解説機能
- ai_translation.py: 翻訳機能
- ai_answer_analysis.py: 解答分析機能
- ai_youtube_quiz.py: YouTube確認問題生成機能
- ai_study_plan.py: 学習計画作成機能
- ai_learning_report.py: 学習レポート生成機能
"""
import streamlit as st

# 各機能モジュールのインポート
from ai_grade_evaluation import display_grade_evaluation
from ai_paper_explanation import display_paper_explanation
from ai_translation import display_translation
from ai_answer_analysis import display_answer_analysis
from ai_youtube_quiz import display_youtube_quiz
from ai_study_plan import display_study_planning_in_ai
from ai_learning_report import display_learning_report_in_ai


def ai_functions():
    """AI機能のメイン関数 - UIルーティングのみ担当"""
    st.title("AI機能")

    # ===== セッション初期化（YouTube確認問題用） =====
    if "quiz_data" not in st.session_state:
        st.session_state.quiz_data = None
    if "quiz_answers" not in st.session_state:
        st.session_state.quiz_answers = {}

    # AI機能カテゴリーをエクスパンダーで表示
    with st.expander("📚 AI機能カテゴリー", expanded=True):
        ai_feature = st.radio(
            "AI機能を選択してください", 
            ["成績評価", "論文解説", "翻訳", "解答分析", "YouTube確認問題生成", "学習計画作成", "学習レポート生成"]
        )

    # 選択された機能を実行
    if ai_feature == "成績評価":
        display_grade_evaluation()
    
    elif ai_feature == "論文解説":
        display_paper_explanation()
    
    elif ai_feature == "翻訳":
        display_translation()
    
    elif ai_feature == "解答分析":
        display_answer_analysis()
    
    elif ai_feature == "YouTube確認問題生成":
        display_youtube_quiz()
    
    elif ai_feature == "学習計画作成":
        display_study_planning_in_ai()
    
    elif ai_feature == "学習レポート生成":
        display_learning_report_in_ai()


# エントリポイント
if __name__ == "__main__":
    ai_functions()
