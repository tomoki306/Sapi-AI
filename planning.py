# planning.py
# 学習計画機能

import streamlit as st
import json
import os
from datetime import datetime, timedelta
from ai_study_plan import generate_study_plan

def display_study_planning():
    """学習計画機能のメイン画面"""
    st.header("📅 学習計画作成")
    
    # タブで機能を分ける
    tab1, tab2 = st.tabs(["新規計画作成", "保存済み計画"])
    
    with tab1:
        create_new_plan()
    
    with tab2:
        view_saved_plans()

# =============== 新規計画作成 ===============

def create_new_plan():
    """新規学習計画の作成"""
    st.subheader("📝 新規学習計画を作成")
    
    # 科目選択
    if 'subjects' not in st.session_state or not st.session_state.subjects:
        st.warning("まず科目を登録してください")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        subject = st.selectbox("科目を選択", st.session_state.subjects)
        current_level = st.selectbox(
            "現在のレベル",
            ["初心者", "初級", "中級", "中級上", "上級", "エキスパート"]
        )
        weekly_hours = st.number_input(
            "週あたりの学習時間（時間）",
            min_value=1,
            max_value=40,
            value=5,
            step=1
        )
    
    with col2:
        target_level = st.selectbox(
            "目標レベル",
            ["初級", "中級", "中級上", "上級", "エキスパート", "プロフェッショナル"]
        )
        target_date = st.date_input(
            "目標達成日",
            value=datetime.now() + timedelta(days=90),
            min_value=datetime.now() + timedelta(days=1)
        )
    
    # 計画名
    plan_name = st.text_input(
        "計画名（任意）",
        value=f"{subject}_{target_level}への道",
        help="この学習計画を識別するための名前"
    )
    
    # AI生成ボタン
    if st.button("🤖 AIで学習計画を生成", type="primary"):
        with st.spinner("AIが学習計画を作成しています..."):
            plan_content = generate_study_plan(
                subject=subject,
                current_level=current_level,
                target_level=target_level,
                target_date=target_date.strftime("%Y-%m-%d"),
                weekly_hours=weekly_hours
            )
            
            if plan_content:
                import uuid
                st.session_state.generated_plan = {
                    "id": str(uuid.uuid4()),  # 一意のID生成
                    "name": plan_name,
                    "title": plan_name,  # タイトルとして追加
                    "subject": subject,
                    "current_level": current_level,
                    "target_level": target_level,
                    "target_date": target_date.strftime("%Y-%m-%d"),
                    "deadline": target_date.strftime("%Y-%m-%d"),  # deadline追加
                    "weekly_hours": weekly_hours,
                    "content": plan_content,
                    "description": plan_content[:200] + "..." if len(plan_content) > 200 else plan_content,  # 説明追加
                    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
    
    # 生成された計画の表示
    if 'generated_plan' in st.session_state and st.session_state.generated_plan:
        st.markdown("---")
        st.subheader("✨ 生成された学習計画")
        
        plan = st.session_state.generated_plan
        
        # 計画のサマリー
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("科目", plan['subject'])
        with col2:
            st.metric("現在→目標", f"{plan['current_level']} → {plan['target_level']}")
        with col3:
            st.metric("目標達成日", plan['target_date'])
        with col4:
            st.metric("週あたり", f"{plan['weekly_hours']}時間")
        
        # 計画内容
        st.markdown("### 📋 計画内容")
        st.markdown(plan['content'])
        
        # リマインダー自動生成オプション
        st.markdown("---")
        st.markdown("### 🔔 リマインダー自動生成（オプション）")
        
        auto_generate_reminders = st.checkbox(
            "この計画からリマインダーを自動生成する",
            value=True,
            help="保存時に期限に基づいたリマインダーを自動的に生成します"
        )
        
        reminder_timings = {}
        if auto_generate_reminders:
            col_r1, col_r2 = st.columns(2)
            with col_r1:
                reminder_timings['1_week_before'] = st.checkbox("1週間前", value=True, key="plan_reminder_1w")
                reminder_timings['3_days_before'] = st.checkbox("3日前", value=True, key="plan_reminder_3d")
            with col_r2:
                reminder_timings['1_day_before'] = st.checkbox("前日", value=True, key="plan_reminder_1d")
                reminder_timings['on_deadline'] = st.checkbox("期限当日", value=True, key="plan_reminder_deadline")
        
        # 保存・ダウンロードボタン
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("💾 計画を保存", type="primary"):
                if save_study_plan(plan):
                    st.success("✅ 学習計画を保存しました")
                    
                    # リマインダー生成
                    if auto_generate_reminders:
                        from planning_reminder_integration import create_reminders_from_plan
                        reminder_count = create_reminders_from_plan(plan, reminder_timings)
                        if reminder_count > 0:
                            st.success(f"🔔 {reminder_count}件のリマインダーを生成しました")
                    
                    del st.session_state.generated_plan
                    st.rerun()
        
        with col2:
            # テキストファイルとしてダウンロード
            plan_text = format_plan_for_download(plan)
            st.download_button(
                label="📥 テキストファイルをダウンロード",
                data=plan_text,
                file_name=f"study_plan_{plan['subject']}_{datetime.now().strftime('%Y%m%d')}.txt",
                mime="text/plain"
            )
        
        with col3:
            if st.button("🔄 新しい計画を作成", type="secondary"):
                del st.session_state.generated_plan
                st.rerun()

# =============== 保存済み計画の表示 ===============

def view_saved_plans():
    """保存済みの学習計画を表示"""
    st.subheader("📚 保存済み学習計画")
    
    if not os.path.exists('study_plans.json'):
        st.info("保存された学習計画はありません")
        return
    
    with open('study_plans.json', 'r', encoding='utf-8') as f:
        plans = json.load(f)
    
    if not plans:
        st.info("保存された学習計画はありません")
        return
    
    # 計画の一覧表示
    for idx, plan in enumerate(plans):
        with st.expander(f"📖 {plan['name']} （作成日: {plan['created_at'][:10]}）"):
            # サマリー
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("科目", plan['subject'])
            with col2:
                st.metric("現在→目標", f"{plan['current_level']} → {plan['target_level']}")
            with col3:
                st.metric("目標達成日", plan['target_date'])
            with col4:
                st.metric("週あたり", f"{plan['weekly_hours']}時間")
            
            # 内容表示
            st.markdown("### 📋 計画内容")
            st.markdown(plan['content'])
            
            # アクションボタン
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # ダウンロード
                plan_text = format_plan_for_download(plan)
                st.download_button(
                    label="📥 ダウンロード",
                    data=plan_text,
                    file_name=f"study_plan_{plan['subject']}_{datetime.now().strftime('%Y%m%d')}.txt",
                    mime="text/plain",
                    key=f"download_plan_{idx}"
                )
            
            with col2:
                # 削除
                if st.button("🗑️ 削除", key=f"delete_plan_{idx}", type="secondary"):
                    if delete_study_plan(idx):
                        st.success("✅ 計画を削除しました")
                        st.rerun()

# =============== ヘルパー関数 ===============

def save_study_plan(plan):
    """学習計画を保存"""
    try:
        # 既存の計画を読み込み
        if os.path.exists('study_plans.json'):
            with open('study_plans.json', 'r', encoding='utf-8') as f:
                plans = json.load(f)
        else:
            plans = []
        
        # 新しい計画を追加
        plans.append(plan)
        
        # 保存
        with open('study_plans.json', 'w', encoding='utf-8') as f:
            json.dump(plans, f, ensure_ascii=False, indent=4)
        
        return True
    except Exception as e:
        st.error(f"保存に失敗しました: {str(e)}")
        return False

def delete_study_plan(index):
    """学習計画を削除"""
    try:
        with open('study_plans.json', 'r', encoding='utf-8') as f:
            plans = json.load(f)
        
        if 0 <= index < len(plans):
            del plans[index]
            
            with open('study_plans.json', 'w', encoding='utf-8') as f:
                json.dump(plans, f, ensure_ascii=False, indent=4)
            
            return True
        return False
    except Exception as e:
        st.error(f"削除に失敗しました: {str(e)}")
        return False

def format_plan_for_download(plan):
    """ダウンロード用にテキスト形式にフォーマット"""
    text = f"""
======================================
学習計画: {plan['name']}
======================================

作成日: {plan['created_at']}

【科目情報】
科目: {plan['subject']}
現在のレベル: {plan['current_level']}
目標レベル: {plan['target_level']}
目標達成日: {plan['target_date']}
週あたりの学習時間: {plan['weekly_hours']}時間

【計画内容】
{plan['content']}

======================================
この計画は学習管理システムで生成されました
======================================
"""
    return text
