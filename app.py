# app.py

import streamlit as st

# アプリケーションの設定（最初に配置）
st.set_page_config(layout="wide", page_title="学習管理アプリ")

# ==== 追加: .env を読む ====
from dotenv import load_dotenv
import os

# 既存の環境変数をクリアしてから読み込み
if os.path.exists('.env'):
    load_dotenv(override=True)  # override=True で強制上書き
else:
    st.error("❌ .env ファイルが見つかりません")

# 環境変数の検証（セキュリティ強化）
from env_validator import validate_env_variables, validate_optional_env_variables
validate_env_variables()
# ===========================

from data import initialize_session_state
from subject import register_subject
from reminder import set_reminders, display_reminder_sidebar  # リマインダー通知追加
from progress import track_progress
from grade import record_grades, display_grade_search  # 成績検索機能追加
from goal import set_goals
from goal_progress import display_all_goals_progress  # 目標進捗管理追加
from dashboard import display_dashboard
from ai_grade_evaluation import display_grade_evaluation
from ai_paper_explanation import display_paper_explanation
from ai_translation import display_translation
from ai_answer_analysis import display_answer_analysis
from ai_youtube_quiz import display_youtube_quiz
from ai_study_plan import display_study_planning_in_ai
from ai_learning_report import display_learning_report_in_ai
from data_management import display_data_management  # データ管理機能追加
from grade_analytics import display_advanced_analytics  # 高度な成績分析追加
from data_integrity import auto_check_on_startup
from backup_manager import auto_backup_on_startup
from logger import log_maintenance_on_startup, log_info
# 新機能のインポート (高優先)
from bulk_operations import display_bulk_operations  # 一括操作機能追加
from grade_prediction import display_grade_prediction  # 成績予測機能追加
from enhanced_visualization import display_enhanced_visualization  # 高度な可視化追加
from ml_grade_prediction import display_ml_grade_prediction  # ML成績予測機能追加 ✨NEW
# 新機能のインポート (中優先) ✨NEW
from templates import display_template_management  # テンプレート機能追加
from auto_reports import display_auto_reports, check_and_generate_auto_reports  # 自動レポート生成追加
from notes import display_notes_management  # メモ・ノート機能追加
from planning_reminder_integration import display_planning_reminder_integration  # 学習計画リマインダー連携追加
from planning import display_study_planning  # 学習計画作成追加
from csv_export_enhanced import display_csv_export  # CSVエクスポート機能追加
from cache_optimization import display_cache_management  # キャッシュ最適化追加

def main():
    # セッションステートの初期化
    initialize_session_state()
    
    # オプション環境変数のチェック（警告のみ）
    validate_optional_env_variables()
    
    # 起動時の自動メンテナンス（初回のみ実行）
    if 'app_initialized' not in st.session_state:
        log_maintenance_on_startup()
        auto_check_on_startup()
        auto_backup_on_startup()
        check_and_generate_auto_reports()  # 自動レポート生成チェック ✨NEW
        st.session_state.app_initialized = True
        log_info("アプリケーションの初期化が完了しました", "APP_STARTUP")
    
    # サイドバーのメニュー（カテゴリー別に整理）
    st.sidebar.title("📚 学習管理システム")
    
    # メインカテゴリー選択
    with st.sidebar:
        main_category = st.selectbox(
            "カテゴリーを選択",
            [
                "📝 学習管理",
                "📊 成績管理", 
                "📈 分析・予測",
                "🤖 AI機能",
                "⚙️ データ管理"
            ],
            key="main_category"
        )
        
        st.markdown("---")
        
        # カテゴリー別のサブメニュー
        if main_category == "📝 学習管理":
            menu = st.radio("機能を選択", [
                "科目登録",
                "進捗ダッシュボード",
                "統計レポート",
                "学習目標設定",
                "目標進捗管理",
                "学習計画作成",
                "進捗トラッキング",
                "リマインダー設定",
                "計画リマインダー連携",
                "メモ・ノート"
            ])
        
        elif main_category == "📊 成績管理":
            menu = st.radio("機能を選択", [
                "成績記録",
                "成績検索",
                "テンプレート管理"
            ])
        
        elif main_category == "📈 分析・予測":
            menu = st.radio("機能を選択", [
                "成績分析",
                "成績予測",
                "高度な可視化"
            ])
        
        elif main_category == "🤖 AI機能":
            menu = st.radio("機能を選択", [
                "🤖 ML成績予測",  # ✨ML予測をAI機能に移動
                "成績評価",
                "論文解説",
                "翻訳",
                "解答分析",
                "YouTube確認問題生成",
                "学習計画作成",
                "学習レポート生成"
            ])
        
        elif main_category == "⚙️ データ管理":
            menu = st.radio("機能を選択", [
                "データ管理",
                "データ一括操作",
                "CSVエクスポート",
                "キャッシュ管理"
            ])
    
    # リマインダー通知をサイドバーに常時表示
    display_reminder_sidebar()
    
    # 自動メンテナンス結果の通知（サイドバー）
    if st.session_state.get('data_repairs_count', 0) > 0:
        st.sidebar.info(f"🔧 {st.session_state.data_repairs_count}件のデータ修復を実行しました")
    if st.session_state.get('auto_backup_done', False):
        st.sidebar.success("💾 自動バックアップが完了しました")
    
    # メニューに応じた関数の呼び出し
    if main_category == "📝 学習管理":
        if menu == "科目登録":
            register_subject()
        elif menu == "進捗ダッシュボード":
            display_dashboard()
        elif menu == "統計レポート":
            display_auto_reports()
        elif menu == "学習目標設定":
            set_goals()
        elif menu == "目標進捗管理":
            display_all_goals_progress()
        elif menu == "学習計画作成":
            display_study_planning()
        elif menu == "進捗トラッキング":
            track_progress()
        elif menu == "リマインダー設定":
            set_reminders()
        elif menu == "計画リマインダー連携":
            display_planning_reminder_integration()
        elif menu == "メモ・ノート":
            display_notes_management()

    elif main_category == "📊 成績管理":
        if menu == "成績記録":
            record_grades()
        elif menu == "成績検索":
            display_grade_search()
        elif menu == "テンプレート管理":
            display_template_management()

    elif main_category == "📈 分析・予測":
        if menu == "成績分析":
            display_advanced_analytics()
        elif menu == "成績予測":
            display_grade_prediction()
        elif menu == "高度な可視化":
            display_enhanced_visualization()

    elif main_category == "🤖 AI機能":
        if menu == "🤖 ML成績予測":  # ✨ML予測をAI機能に移動
            display_ml_grade_prediction()
        elif menu == "成績評価":
            display_grade_evaluation()
        elif menu == "論文解説":
            display_paper_explanation()
        elif menu == "翻訳":
            display_translation()
        elif menu == "解答分析":
            display_answer_analysis()
        elif menu == "YouTube確認問題生成":
            display_youtube_quiz()
        elif menu == "学習計画作成":
            display_study_planning_in_ai()
        elif menu == "学習レポート生成":
            display_learning_report_in_ai()

    elif main_category == "⚙️ データ管理":
        if menu == "データ管理":
            display_data_management()
        elif menu == "データ一括操作":
            display_bulk_operations()
        elif menu == "CSVエクスポート":
            display_csv_export()
        elif menu == "キャッシュ管理":
            display_cache_management()


    # 画面下部に小型の音声エージェントを常時表示
    render_mini_voice_agent()


def render_mini_voice_agent():
    """折りたたみ式のミニ音声チャットエージェント (Azure OpenAI: GPT-4o mini + gpt-4o-mini-transcribe + TTS)。
    
    機能を voice_agent_components.py に分割して保守性を向上させました。
    """
    from voice_agent_components import (
        initialize_voice_agent,
        get_azure_client,
        handle_voice_input,
        render_input_ui,
        handle_text_input,
        render_send_button,
        generate_ai_response,
        display_chat_history,
        render_audio_player
    )
    
    with st.expander("ユーザーエージェント（音声チャット）", expanded=False):
        st.caption("GPT-5-mini + gpt-4o-mini-transcribe + TTS（マルチリソース対応）")
        
        # 初期化
        initialize_voice_agent()
        
        # Azure クライアントの取得（GPT用、音声認識用、TTS用）
        result = get_azure_client()
        if result is None or result[0] is None:
            return
        gpt_client, voice_client, GPT_DEPLOYMENT_NAME, STT_DEPLOYMENT_NAME, tts_config = result
        
        # 入力UI
        col1, col2 = st.columns([1, 1])
        
        with col1:
            user_text = render_input_ui()
        
        with col2:
            transcribed_text = handle_voice_input(voice_client, STT_DEPLOYMENT_NAME)
        
        # 最終的な入力の決定
        final_input = handle_text_input(user_text, transcribed_text)
        
        # 送信UI
        send = render_send_button()
        
        # AI応答処理
        if send and final_input and final_input.strip():
            st.session_state["voice_agent_messages"].append({"role": "user", "content": final_input.strip()})
            
            # AI応答生成 + TTS音声生成（GPTクライアント使用 - East US 2）
            ai_reply, audio_data = generate_ai_response(gpt_client, GPT_DEPLOYMENT_NAME, final_input, tts_config)
            
            if ai_reply:
                st.session_state["voice_agent_messages"].append({"role": "assistant", "content": ai_reply})
                st.success(ai_reply)
                
                # 音声再生UI
                if audio_data:
                    render_audio_player(audio_data)
        
        # チャット履歴表示
        display_chat_history()


if __name__ == "__main__":
    main()
