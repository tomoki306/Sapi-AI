# reminder.py

import streamlit as st
from datetime import datetime, timedelta
import json

def categorize_reminders():
    """リマインダーを期限で分類する
    
    Returns:
        dict: {
            'overdue': [],    # 期限切れ（赤）
            'urgent': [],     # 緊急：今日・明日（黄）
            'upcoming': []    # 近日：1週間以内（青）
        }
    """
    try:
        with open('reminders.json', 'r', encoding='utf-8') as f:
            reminders = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {'overdue': [], 'urgent': [], 'upcoming': []}
    
    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)
    week_later = today + timedelta(days=7)
    
    categorized = {
        'overdue': [],    # 期限切れ
        'urgent': [],     # 緊急（今日・明日）
        'upcoming': []    # 近日（1週間以内）
    }
    
    for reminder in reminders:
        try:
            reminder_date = datetime.strptime(reminder['date'], '%Y-%m-%d').date()
            
            if reminder_date < today:
                categorized['overdue'].append(reminder)
            elif reminder_date <= tomorrow:
                categorized['urgent'].append(reminder)
            elif reminder_date <= week_later:
                categorized['upcoming'].append(reminder)
        except Exception:
            # 日付のパースエラーはスキップ
            continue
    
    return categorized

def display_reminder_sidebar():
    """サイドバーにリマインダーを色分けして表示"""
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🔔 リマインダー通知")
    
    categorized = categorize_reminders()
    
    # 期限切れ（赤）
    if categorized['overdue']:
        st.sidebar.markdown("#### 🔴 期限切れ")
        for reminder in categorized['overdue']:
            st.sidebar.error(
                f"**{reminder['subject']}** - {reminder['type']}\n"
                f"期日: {reminder['date']}\n"
                f"{reminder['text']}"
            )
    
    # 緊急（黄）
    if categorized['urgent']:
        st.sidebar.markdown("#### 🟡 緊急（今日・明日）")
        for reminder in categorized['urgent']:
            st.sidebar.warning(
                f"**{reminder['subject']}** - {reminder['type']}\n"
                f"期日: {reminder['date']}\n"
                f"{reminder['text']}"
            )
    
    # 近日（青）
    if categorized['upcoming']:
        st.sidebar.markdown("#### 🔵 近日（1週間以内）")
        for reminder in categorized['upcoming']:
            st.sidebar.info(
                f"**{reminder['subject']}** - {reminder['type']}\n"
                f"期日: {reminder['date']}\n"
                f"{reminder['text']}"
            )
    
    # リマインダーがない場合
    if not any(categorized.values()):
        st.sidebar.success("📭 現在、通知はありません")
    
    st.sidebar.markdown("---")

def set_reminders():
    # リマインダー設定の処理
    st.header("リマインダー設定")
    
    # タブで機能を分ける
    tab1, tab2 = st.tabs(["新規リマインダー", "リマインダー管理"])
    
    with tab1:
        create_reminder()
    
    with tab2:
        manage_reminders()

def create_reminder():
    """新規リマインダーの作成"""
    st.subheader("📝 新規リマインダーを作成")
    
    # 科目が存在するか確認
    if 'subjects' not in st.session_state or not st.session_state.subjects:
        st.error("まず科目を登録してください")
        return

    # アプリ起動時にJSONファイルからリマインダーを読み込む
    if 'reminders' not in st.session_state:
        try:
            with open('reminders.json', 'r', encoding='utf-8') as f:
                st.session_state.reminders = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            st.session_state.reminders = []

    col1, col2 = st.columns(2)
    
    with col1:
        subject = st.selectbox("科目を選択", st.session_state.subjects, key="new_reminder_subject")
        reminder_type = st.selectbox("リマインダータイプ", ["課題", "試験", "その他"], key="new_reminder_type")
    
    with col2:
        reminder_date = st.date_input("期日", value=datetime.today(), key="new_reminder_date")
    
    reminder_text = st.text_area("リマインダー内容", key="new_reminder_text")
    
    # 繰り返し設定の追加
    st.markdown("---")
    st.markdown("##### 🔁 繰り返し設定（オプション）")
    
    col3, col4 = st.columns(2)
    with col3:
        is_recurring = st.checkbox("繰り返しリマインダーにする", key="new_reminder_recurring")
    
    with col4:
        recurring_interval = None
        if is_recurring:
            recurring_interval = st.selectbox(
                "繰り返し間隔",
                ["毎日", "毎週", "毎月"],
                key="new_reminder_interval"
            )
    
    if st.button("✅ リマインダーを設定", type="primary"):
        # リマインダーをセッションステートに保存
        if subject and reminder_text:
            if 'reminders' not in st.session_state:
                st.session_state.reminders = []
            
            new_reminder = {
                "subject": subject,
                "type": reminder_type,
                "date": reminder_date.strftime('%Y-%m-%d'),
                "text": reminder_text,
                "completed": False,  # 完了フラグ追加
                "snoozed_until": None,  # スヌーズ情報
                "is_recurring": is_recurring,  # 繰り返しフラグ
                "recurring_interval": recurring_interval if is_recurring else None,  # 繰り返し間隔
                "created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # 作成日時
            }
            
            st.session_state.reminders.append(new_reminder)
            st.success("✅ リマインダーが設定されました")

            # リマインダーをJSONファイルに保存
            with open('reminders.json', 'w', encoding='utf-8') as f:
                json.dump(st.session_state.reminders, f, ensure_ascii=False, indent=4)
            st.rerun()
        else:
            st.error("科目とリマインダー内容は必須です")

def manage_reminders():
    """リマインダーの管理（編集・削除）"""
    st.subheader("📋 設定済みリマインダー管理")
    
    # リマインダーを読み込み
    try:
        with open('reminders.json', 'r', encoding='utf-8') as f:
            reminders = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        st.info("設定済みのリマインダーはありません")
        return
    
    if not reminders:
        st.info("設定済みのリマインダーはありません")
        return
    
    # 表示フィルター
    col1, col2 = st.columns(2)
    with col1:
        show_completed = st.checkbox("完了済みを表示", value=False, key="show_completed")
    with col2:
        show_stats = st.checkbox("統計を表示", value=True, key="show_stats")
    
    # 統計情報
    if show_stats:
        total_reminders = len(reminders)
        completed_reminders = sum(1 for r in reminders if r.get('completed', False))
        active_reminders = total_reminders - completed_reminders
        
        col_a, col_b, col_c = st.columns(3)
        col_a.metric("総リマインダー数", total_reminders)
        col_b.metric("有効", active_reminders)
        col_c.metric("完了", completed_reminders)
        st.markdown("---")
    
    # カテゴリー分類して表示
    categorized = categorize_reminders()
    
    # フィルタリング（完了済みを除外）
    if not show_completed:
        categorized['overdue'] = [r for r in categorized['overdue'] if not r.get('completed', False)]
        categorized['urgent'] = [r for r in categorized['urgent'] if not r.get('completed', False)]
        categorized['upcoming'] = [r for r in categorized['upcoming'] if not r.get('completed', False)]
    
    # 期限切れ
    if categorized['overdue']:
        st.markdown("### 🔴 期限切れ")
        display_reminder_list(categorized['overdue'], reminders, "overdue")
    
    # 緊急
    if categorized['urgent']:
        st.markdown("### 🟡 緊急（今日・明日）")
        display_reminder_list(categorized['urgent'], reminders, "urgent")
    
    # 近日
    if categorized['upcoming']:
        st.markdown("### 🔵 近日（1週間以内）")
        display_reminder_list(categorized['upcoming'], reminders, "upcoming")
    
    # その他（1週間以降）
    other_reminders = [r for r in reminders if r not in categorized['overdue'] + categorized['urgent'] + categorized['upcoming']]
    if not show_completed:
        other_reminders = [r for r in other_reminders if not r.get('completed', False)]
    
    if other_reminders:
        st.markdown("### ⚪ その他")
        display_reminder_list(other_reminders, reminders, "other")

def display_reminder_list(reminder_list, all_reminders, category_key):
    """リマインダーリストの表示と操作"""
    for reminder in reminder_list:
        # リマインダーのインデックスを取得
        idx = all_reminders.index(reminder)
        
        # 完了状態の表示
        completed_icon = "✅" if reminder.get('completed', False) else "📌"
        completed_style = "text-decoration: line-through; opacity: 0.6;" if reminder.get('completed', False) else ""
        
        # スヌーズ情報の表示
        snooze_info = ""
        if reminder.get('snoozed_until'):
            snooze_info = f"⏰ スヌーズ中 (再通知: {reminder['snoozed_until']})"
        
        # 繰り返し情報の表示
        recurring_info = ""
        if reminder.get('is_recurring', False):
            recurring_info = f"� {reminder.get('recurring_interval', '')} 繰り返し"
        
        title = f"{completed_icon} {reminder['subject']} - {reminder['type']} ({reminder['date']}) {snooze_info} {recurring_info}"
        
        with st.expander(title):
            st.markdown(f"<div style='{completed_style}'>**内容**: {reminder['text']}</div>", unsafe_allow_html=True)
            
            # クイックアクションボタン
            st.markdown("---")
            st.markdown("##### クイックアクション")
            
            col_quick1, col_quick2, col_quick3, col_quick4 = st.columns(4)
            
            with col_quick1:
                if not reminder.get('completed', False):
                    if st.button("✅ 完了", key=f"complete_{category_key}_{idx}", type="primary"):
                        all_reminders[idx]['completed'] = True
                        all_reminders[idx]['completed_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        
                        # 繰り返し設定がある場合は次の日付を生成
                        if reminder.get('is_recurring', False):
                            next_reminder = create_next_recurring_reminder(reminder)
                            all_reminders.append(next_reminder)
                        
                        with open('reminders.json', 'w', encoding='utf-8') as f:
                            json.dump(all_reminders, f, ensure_ascii=False, indent=4)
                        
                        st.success("✅ リマインダーを完了しました")
                        st.rerun()
                else:
                    if st.button("↩️ 未完了に戻す", key=f"uncomplete_{category_key}_{idx}"):
                        all_reminders[idx]['completed'] = False
                        all_reminders[idx]['completed_at'] = None
                        
                        with open('reminders.json', 'w', encoding='utf-8') as f:
                            json.dump(all_reminders, f, ensure_ascii=False, indent=4)
                        
                        st.success("↩️ リマインダーを未完了に戻しました")
                        st.rerun()
            
            with col_quick2:
                if not reminder.get('completed', False):
                    if st.button("⏰ 1時間後", key=f"snooze_1h_{category_key}_{idx}"):
                        snooze_time = datetime.now() + timedelta(hours=1)
                        all_reminders[idx]['snoozed_until'] = snooze_time.strftime('%Y-%m-%d %H:%M')
                        
                        with open('reminders.json', 'w', encoding='utf-8') as f:
                            json.dump(all_reminders, f, ensure_ascii=False, indent=4)
                        
                        st.success(f"⏰ 1時間後に再通知します")
                        st.rerun()
            
            with col_quick3:
                if not reminder.get('completed', False):
                    if st.button("📅 明日", key=f"snooze_tomorrow_{category_key}_{idx}"):
                        tomorrow = (datetime.now() + timedelta(days=1)).replace(hour=9, minute=0)
                        all_reminders[idx]['date'] = tomorrow.strftime('%Y-%m-%d')
                        all_reminders[idx]['snoozed_until'] = tomorrow.strftime('%Y-%m-%d %H:%M')
                        
                        with open('reminders.json', 'w', encoding='utf-8') as f:
                            json.dump(all_reminders, f, ensure_ascii=False, indent=4)
                        
                        st.success(f"📅 明日に延期しました")
                        st.rerun()
            
            with col_quick4:
                if reminder.get('snoozed_until'):
                    if st.button("🔕 スヌーズ解除", key=f"unsnooze_{category_key}_{idx}"):
                        all_reminders[idx]['snoozed_until'] = None
                        
                        with open('reminders.json', 'w', encoding='utf-8') as f:
                            json.dump(all_reminders, f, ensure_ascii=False, indent=4)
                        
                        st.success("🔕 スヌーズを解除しました")
                        st.rerun()
            
            # 編集フォーム
            st.markdown("---")
            st.markdown("##### 詳細編集")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if 'subjects' in st.session_state and st.session_state.subjects:
                    edit_subject = st.selectbox(
                        "科目",
                        st.session_state.subjects,
                        index=st.session_state.subjects.index(reminder['subject']) if reminder['subject'] in st.session_state.subjects else 0,
                        key=f"edit_subject_{category_key}_{idx}"
                    )
                else:
                    edit_subject = st.text_input("科目", value=reminder['subject'], key=f"edit_subject_{category_key}_{idx}")
                
                edit_type = st.selectbox(
                    "タイプ",
                    ["課題", "試験", "その他"],
                    index=["課題", "試験", "その他"].index(reminder['type']) if reminder['type'] in ["課題", "試験", "その他"] else 0,
                    key=f"edit_type_{category_key}_{idx}"
                )
            
            with col2:
                try:
                    current_date = datetime.strptime(reminder['date'], '%Y-%m-%d').date()
                except Exception:
                    current_date = datetime.today()
                
                edit_date = st.date_input(
                    "期日",
                    value=current_date,
                    key=f"edit_date_{category_key}_{idx}"
                )
            
            edit_text = st.text_area(
                "内容",
                value=reminder['text'],
                key=f"edit_text_{category_key}_{idx}"
            )
            
            # 繰り返し設定の編集
            col_rec1, col_rec2 = st.columns(2)
            with col_rec1:
                edit_recurring = st.checkbox(
                    "繰り返しリマインダー",
                    value=reminder.get('is_recurring', False),
                    key=f"edit_recurring_{category_key}_{idx}"
                )
            with col_rec2:
                if edit_recurring:
                    edit_interval = st.selectbox(
                        "繰り返し間隔",
                        ["毎日", "毎週", "毎月"],
                        index=["毎日", "毎週", "毎月"].index(reminder.get('recurring_interval', '毎週')) if reminder.get('recurring_interval') in ["毎日", "毎週", "毎月"] else 1,
                        key=f"edit_interval_{category_key}_{idx}"
                    )
                else:
                    edit_interval = None
            
            # アクションボタン
            col_a, col_b, col_c = st.columns([1, 1, 2])
            
            with col_a:
                if st.button("💾 更新", key=f"update_{category_key}_{idx}", type="primary"):
                    all_reminders[idx] = {
                        "subject": edit_subject,
                        "type": edit_type,
                        "date": edit_date.strftime('%Y-%m-%d'),
                        "text": edit_text,
                        "completed": reminder.get('completed', False),
                        "completed_at": reminder.get('completed_at'),
                        "snoozed_until": reminder.get('snoozed_until'),
                        "is_recurring": edit_recurring,
                        "recurring_interval": edit_interval,
                        "created_at": reminder.get('created_at', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                    }
                    
                    with open('reminders.json', 'w', encoding='utf-8') as f:
                        json.dump(all_reminders, f, ensure_ascii=False, indent=4)
                    
                    st.success("✅ リマインダーを更新しました")
                    st.rerun()
            
            with col_b:
                if st.button("🗑️ 削除", key=f"delete_{category_key}_{idx}", type="secondary"):
                    del all_reminders[idx]
                    
                    with open('reminders.json', 'w', encoding='utf-8') as f:
                        json.dump(all_reminders, f, ensure_ascii=False, indent=4)
                    
                    st.success("✅ リマインダーを削除しました")
                    st.rerun()


def create_next_recurring_reminder(reminder: dict) -> dict:
    """繰り返しリマインダーの次の予定を生成"""
    try:
        current_date = datetime.strptime(reminder['date'], '%Y-%m-%d')
    except Exception:
        current_date = datetime.now()
    
    interval = reminder.get('recurring_interval', '毎週')
    
    if interval == '毎日':
        next_date = current_date + timedelta(days=1)
    elif interval == '毎週':
        next_date = current_date + timedelta(weeks=1)
    elif interval == '毎月':
        # 簡易的な月次処理（同じ日付で翌月）
        next_date = current_date + timedelta(days=30)
    else:
        next_date = current_date + timedelta(weeks=1)
    
    return {
        "subject": reminder['subject'],
        "type": reminder['type'],
        "date": next_date.strftime('%Y-%m-%d'),
        "text": reminder['text'],
        "completed": False,
        "snoozed_until": None,
        "is_recurring": True,
        "recurring_interval": interval,
        "created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

