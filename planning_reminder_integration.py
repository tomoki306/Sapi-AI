# planning_reminder_integration.py - 学習計画とリマインダーの連携機能

import streamlit as st
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any
from logger import log_info, log_error


# =========================
# ヘルパー関数
# =========================

def save_reminders():
    """リマインダーをJSONファイルに保存"""
    try:
        with open('reminders.json', 'w', encoding='utf-8') as f:
            json.dump(st.session_state.reminders, f, ensure_ascii=False, indent=4)
    except Exception as e:
        log_error(e, "リマインダーの保存エラー")


# =========================
# 学習計画からリマインダーを自動生成
# =========================

def create_reminders_from_plan(plan: Dict[str, Any], reminder_options: Dict[str, bool]):
    """
    学習計画からリマインダーを自動生成
    
    Args:
        plan: 学習計画データ
        reminder_options: リマインダー生成オプション
            - "1_week_before": 1週間前
            - "3_days_before": 3日前
            - "1_day_before": 前日
            - "on_deadline": 期限当日
    """
    if 'reminders' not in st.session_state:
        st.session_state.reminders = []
    
    created_count = 0
    
    # 計画の期限を取得
    deadline_str = plan.get('deadline')
    if not deadline_str:
        return 0
    
    try:
        deadline = datetime.strptime(deadline_str, '%Y-%m-%d')
    except Exception as e:
        log_error(e, "期限の日付変換エラー")
        return 0
    
    subject = plan.get('subject', '不明')
    plan_title = plan.get('title', '学習計画')
    
    # 各タイミングでリマインダーを作成
    reminders_to_create = []
    
    if reminder_options.get('1_week_before', False):
        reminder_date = deadline - timedelta(days=7)
        if reminder_date >= datetime.now():
            reminders_to_create.append({
                'date': reminder_date.strftime('%Y-%m-%d'),
                'text': f"【1週間前】{subject} - {plan_title}",
                'timing': '1週間前'
            })
    
    if reminder_options.get('3_days_before', False):
        reminder_date = deadline - timedelta(days=3)
        if reminder_date >= datetime.now():
            reminders_to_create.append({
                'date': reminder_date.strftime('%Y-%m-%d'),
                'text': f"【3日前】{subject} - {plan_title}",
                'timing': '3日前'
            })
    
    if reminder_options.get('1_day_before', False):
        reminder_date = deadline - timedelta(days=1)
        if reminder_date >= datetime.now():
            reminders_to_create.append({
                'date': reminder_date.strftime('%Y-%m-%d'),
                'text': f"【前日】{subject} - {plan_title}",
                'timing': '前日'
            })
    
    if reminder_options.get('on_deadline', True):
        reminders_to_create.append({
            'date': deadline.strftime('%Y-%m-%d'),
            'text': f"【期限日】{subject} - {plan_title}",
            'timing': '期限日'
        })
    
    # リマインダーを追加
    for reminder_data in reminders_to_create:
        reminder = {
            'subject': subject,
            'type': '学習計画',
            'date': reminder_data['date'],
            'text': reminder_data['text'],
            'completed': False,
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'source': 'planning',
            'plan_id': plan.get('id'),
            'timing': reminder_data['timing']
        }
        
        st.session_state.reminders.append(reminder)
        created_count += 1
    
    # 保存
    if created_count > 0:
        save_reminders()
        log_info(f"学習計画からリマインダー生成: {subject} - {plan_title} ({created_count}件)", "PLANNING_REMINDER")
    
    return created_count


def update_plan_reminders(plan_id: str, new_deadline: str):
    """
    学習計画の期限が変更された場合、関連するリマインダーを更新
    
    Args:
        plan_id: 計画ID
        new_deadline: 新しい期限 (YYYY-MM-DD)
    """
    if 'reminders' not in st.session_state:
        return 0
    
    try:
        new_deadline_date = datetime.strptime(new_deadline, '%Y-%m-%d')
    except Exception as e:
        log_error(e, "新しい期限の日付変換エラー")
        return 0
    
    updated_count = 0
    
    for reminder in st.session_state.reminders:
        # この計画に関連するリマインダーのみ更新
        if reminder.get('plan_id') == plan_id and not reminder.get('completed', False):
            timing = reminder.get('timing')
            
            # タイミングに応じて新しい日付を計算
            if timing == '1週間前':
                new_date = new_deadline_date - timedelta(days=7)
            elif timing == '3日前':
                new_date = new_deadline_date - timedelta(days=3)
            elif timing == '前日':
                new_date = new_deadline_date - timedelta(days=1)
            elif timing == '期限日':
                new_date = new_deadline_date
            else:
                continue
            
            # 過去の日付にならないようにチェック
            if new_date >= datetime.now():
                reminder['date'] = new_date.strftime('%Y-%m-%d')
                updated_count += 1
    
    if updated_count > 0:
        save_reminders()
        log_info(f"学習計画変更に伴うリマインダー更新: 計画ID {plan_id} ({updated_count}件)", "PLANNING_REMINDER")
    
    return updated_count


def complete_plan_reminders(plan_id: str):
    """
    学習計画が完了した場合、関連するリマインダーを完了状態に
    
    Args:
        plan_id: 計画ID
    """
    if 'reminders' not in st.session_state:
        return 0
    
    completed_count = 0
    
    for reminder in st.session_state.reminders:
        if reminder.get('plan_id') == plan_id and not reminder.get('completed', False):
            reminder['completed'] = True
            reminder['completed_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            completed_count += 1
    
    if completed_count > 0:
        save_reminders()
        log_info(f"学習計画完了に伴うリマインダー完了: 計画ID {plan_id} ({completed_count}件)", "PLANNING_REMINDER")
    
    return completed_count


def delete_plan_reminders(plan_id: str):
    """
    学習計画が削除された場合、関連するリマインダーを削除
    
    Args:
        plan_id: 計画ID
    """
    if 'reminders' not in st.session_state:
        return 0
    
    original_count = len(st.session_state.reminders)
    
    # 関連しないリマインダーのみ残す
    st.session_state.reminders = [
        r for r in st.session_state.reminders
        if r.get('plan_id') != plan_id
    ]
    
    deleted_count = original_count - len(st.session_state.reminders)
    
    if deleted_count > 0:
        save_reminders()
        log_info(f"学習計画削除に伴うリマインダー削除: 計画ID {plan_id} ({deleted_count}件)", "PLANNING_REMINDER")
    
    return deleted_count


# =========================
# UI機能
# =========================

def display_planning_reminder_integration():
    """学習計画とリマインダー連携の設定画面"""
    st.title("🔗 学習計画とリマインダーの連携")
    st.markdown("学習計画から自動的にリマインダーを生成できます。")
    
    # タブで機能を分ける
    tab1, tab2 = st.tabs(["📅 リマインダー自動生成", "📊 連携状況"])
    
    with tab1:
        display_auto_reminder_generation()
    
    with tab2:
        display_integration_status()


def display_auto_reminder_generation():
    """リマインダー自動生成タブ"""
    st.subheader("📅 学習計画からリマインダーを生成")
    
    # 学習計画一覧を取得 (study_plans.jsonから読み込み)
    try:
        import os
        import uuid
        if not os.path.exists('study_plans.json'):
            st.info("💡 学習計画が保存されていません。「学習計画作成」メニューから計画を作成してください。")
            return
        
        with open('study_plans.json', 'r', encoding='utf-8') as f:
            plans = json.load(f)
        
        if not plans:
            st.info("💡 学習計画が保存されていません。「学習計画作成」メニューから計画を作成してください。")
            return
        
        # データ移行: 古い計画にidとdeadlineを追加
        updated = False
        for plan in plans:
            if 'id' not in plan:
                plan['id'] = str(uuid.uuid4())
                updated = True
            if 'deadline' not in plan and 'target_date' in plan:
                plan['deadline'] = plan['target_date']
                updated = True
            if 'title' not in plan and 'name' in plan:
                plan['title'] = plan['name']
                updated = True
        
        # 更新があった場合は保存
        if updated:
            with open('study_plans.json', 'w', encoding='utf-8') as f:
                json.dump(plans, f, ensure_ascii=False, indent=4)
            log_info("学習計画データを最新フォーマットに移行しました", "DATA_MIGRATION")
        
    except Exception as e:
        log_error(e, "学習計画の読み込みエラー")
        st.error("学習計画の読み込みに失敗しました")
        return
    
    # 計画選択
    plan_options = [f"{plan.get('subject', '不明')} - {plan.get('title', '無題')}" for plan in plans]
    selected_plan_index = st.selectbox("計画を選択", range(len(plan_options)), format_func=lambda i: plan_options[i])
    
    selected_plan = plans[selected_plan_index]
    
    # 計画詳細表示
    with st.expander("📋 計画詳細", expanded=True):
        st.markdown(f"**科目**: {selected_plan.get('subject', '不明')}")
        st.markdown(f"**タイトル**: {selected_plan.get('title', '無題')}")
        st.markdown(f"**期限**: {selected_plan.get('deadline', '未設定')}")
        
        if selected_plan.get('description'):
            st.markdown(f"**説明**: {selected_plan.get('description')}")
    
    # リマインダー生成オプション
    st.markdown("#### ⏰ リマインダーのタイミング")
    
    col1, col2 = st.columns(2)
    
    with col1:
        one_week_before = st.checkbox("1週間前", value=True)
        three_days_before = st.checkbox("3日前", value=True)
    
    with col2:
        one_day_before = st.checkbox("前日", value=True)
        on_deadline = st.checkbox("期限当日", value=True)
    
    # 生成ボタン
    if st.button("🔔 リマインダーを生成", type="primary"):
        reminder_options = {
            '1_week_before': one_week_before,
            '3_days_before': three_days_before,
            '1_day_before': one_day_before,
            'on_deadline': on_deadline
        }
        
        created_count = create_reminders_from_plan(selected_plan, reminder_options)
        
        if created_count > 0:
            st.success(f"✅ {created_count}件のリマインダーを生成しました!")
        else:
            st.warning("⚠️ 生成可能なリマインダーがありませんでした。期限が過去の日付になっていないか確認してください。")


def display_integration_status():
    """連携状況タブ"""
    st.subheader("📊 学習計画とリマインダーの連携状況")
    
    if 'reminders' not in st.session_state or not st.session_state.reminders:
        st.info("💡 リマインダーが登録されていません。")
        return
    
    # 学習計画から生成されたリマインダーを抽出
    plan_reminders = [r for r in st.session_state.reminders if r.get('source') == 'planning']
    
    if not plan_reminders:
        st.info("💡 学習計画から生成されたリマインダーはありません。")
        return
    
    st.markdown(f"**学習計画連携リマインダー数**: {len(plan_reminders)}件")
    
    # 完了・未完了の統計
    completed_reminders = [r for r in plan_reminders if r.get('completed', False)]
    active_reminders = [r for r in plan_reminders if not r.get('completed', False)]
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📋 全体", len(plan_reminders))
    with col2:
        st.metric("✅ 完了", len(completed_reminders))
    with col3:
        st.metric("⏰ アクティブ", len(active_reminders))
    
    # 計画別のリマインダー一覧
    st.markdown("---")
    st.markdown("#### 計画別リマインダー")
    
    # 計画IDでグループ化
    plan_groups = {}
    for reminder in plan_reminders:
        plan_id = reminder.get('plan_id', 'unknown')
        if plan_id not in plan_groups:
            plan_groups[plan_id] = []
        plan_groups[plan_id].append(reminder)
    
    for plan_id, reminders_list in plan_groups.items():
        # 最初のリマインダーから計画情報を取得
        first_reminder = reminders_list[0]
        subject = first_reminder.get('subject', '不明')
        
        with st.expander(f"📚 {subject} ({len(reminders_list)}件のリマインダー)"):
            for reminder in sorted(reminders_list, key=lambda x: x['date']):
                status = "✅ 完了" if reminder.get('completed', False) else "⏰ アクティブ"
                timing = reminder.get('timing', '不明')
                date = reminder.get('date', '不明')
                text = reminder.get('text', '')
                
                st.markdown(f"- **{status}** [{date}] {timing}: {text}")
    
    # 一括操作
    st.markdown("---")
    st.markdown("#### 🔧 一括操作")
    
    if st.button("🗑️ 完了済みリマインダーを全て削除"):
        original_count = len(st.session_state.reminders)
        st.session_state.reminders = [
            r for r in st.session_state.reminders
            if not (r.get('source') == 'planning' and r.get('completed', False))
        ]
        deleted_count = original_count - len(st.session_state.reminders)
        
        if deleted_count > 0:
            from data import save_reminders
            save_reminders()
            st.success(f"✅ {deleted_count}件の完了済みリマインダーを削除しました。")
            st.rerun()
        else:
            st.info("💡 削除対象のリマインダーがありませんでした。")


# =========================
# planning.py用の補助関数
# =========================

def add_reminder_integration_to_planning(plan: Dict[str, Any]):
    """
    planning.pyの保存処理に追加する関数
    学習計画保存時にリマインダー生成オプションを提示
    
    Args:
        plan: 保存する学習計画データ
    
    Returns:
        bool: リマインダーを生成した場合True
    """
    st.markdown("---")
    st.markdown("### 🔔 リマインダー自動生成")
    
    auto_generate = st.checkbox("この計画からリマインダーを自動生成する", value=True)
    
    if not auto_generate:
        return False
    
    col1, col2 = st.columns(2)
    
    with col1:
        one_week = st.checkbox("1週間前", value=True, key="reminder_1w")
        three_days = st.checkbox("3日前", value=True, key="reminder_3d")
    
    with col2:
        one_day = st.checkbox("前日", value=True, key="reminder_1d")
        deadline_day = st.checkbox("期限当日", value=True, key="reminder_deadline")
    
    reminder_options = {
        '1_week_before': one_week,
        '3_days_before': three_days,
        '1_day_before': one_day,
        'on_deadline': deadline_day
    }
    
    # リマインダー生成
    created_count = create_reminders_from_plan(plan, reminder_options)
    
    if created_count > 0:
        st.success(f"✅ {created_count}件のリマインダーを生成しました!")
        return True
    
    return False
