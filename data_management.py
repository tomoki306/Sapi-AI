# data_management.py
# データ管理機能（編集・削除・エクスポート・インポート）

import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
import zipfile
import io
from data import (
    delete_grades, update_grade, 
    delete_progress, update_progress,
    delete_reminders, update_reminder,
    delete_subject
)
# 新機能のインポート
from data_integrity import display_data_integrity_check
from backup_manager import display_backup_management
from logger import display_log_viewer

def display_data_management():
    """データ管理画面のメイン関数"""
    st.header("📊 データ管理")
    
    # タブで機能を分ける
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "データ編集・削除", 
        "エクスポート", 
        "インポート", 
        "データ整合性チェック", 
        "バックアップ管理", 
        "ログビューア"
    ])
    
    with tab1:
        display_data_editor()
    
    with tab2:
        display_data_export()
    
    with tab3:
        display_data_import()
    
    with tab4:
        display_data_integrity_check()
    
    with tab5:
        display_backup_management()
    
    with tab6:
        display_log_viewer()

# =============== データ編集・削除機能 ===============

def display_data_editor():
    """データ編集・削除画面"""
    st.subheader("データの編集・削除")
    
    # データタイプ選択
    data_type = st.selectbox(
        "編集するデータタイプを選択",
        ["成績データ", "進捗データ", "リマインダー", "科目管理"]
    )
    
    if data_type == "成績データ":
        edit_grades_data()
    elif data_type == "進捗データ":
        edit_progress_data()
    elif data_type == "リマインダー":
        edit_reminders_data()
    elif data_type == "科目管理":
        manage_subjects()

def edit_grades_data():
    """成績データの編集"""
    st.markdown("### 成績データの管理")
    
    if not st.session_state.subjects:
        st.warning("科目が登録されていません")
        return
    
    subject = st.selectbox("科目を選択", st.session_state.subjects, key="grade_subject")
    
    if subject not in st.session_state.grades or not st.session_state.grades[subject]:
        st.info("この科目の成績データはありません")
        return
    
    # データをDataFrameに変換
    grades_list = []
    for idx, grade in enumerate(st.session_state.grades[subject]):
        grades_list.append({
            "選択": False,
            "番号": idx,
            "日時": grade.get("date", ""),
            "タイプ": grade.get("type", ""),
            "点数": grade.get("grade", 0),
            "重み": grade.get("weight", 1),
            "コメント": grade.get("comment", "")
        })
    
    df = pd.DataFrame(grades_list)
    
    # データ編集
    st.markdown("#### データ編集")
    edited_df = st.data_editor(
        df,
        use_container_width=True,
        num_rows="fixed",
        column_config={
            "選択": st.column_config.CheckboxColumn("選択", help="削除する行を選択"),
            "番号": st.column_config.NumberColumn("番号", disabled=True),
            "日時": st.column_config.TextColumn("日時", disabled=True),
            "タイプ": st.column_config.SelectboxColumn(
                "タイプ",
                options=["定期テスト", "小テスト", "課題", "模試"]
            ),
            "点数": st.column_config.NumberColumn("点数", min_value=0, max_value=100),
            "重み": st.column_config.NumberColumn("重み", min_value=0.1, max_value=10.0, step=0.1),
            "コメント": st.column_config.TextColumn("コメント", width="large")
        },
        hide_index=True,
        key="grades_editor"
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("✅ 変更を保存", type="primary", key="save_grades"):
            # 変更を保存
            for idx, row in edited_df.iterrows():
                original_idx = int(row["番号"])
                if (row["タイプ"] != df.loc[idx, "タイプ"] or
                    row["点数"] != df.loc[idx, "点数"] or
                    row["重み"] != df.loc[idx, "重み"] or
                    row["コメント"] != df.loc[idx, "コメント"]):
                    update_grade(
                        subject, original_idx,
                        row["タイプ"], row["点数"], row["重み"], row["コメント"]
                    )
            st.success("✅ 変更を保存しました")
            st.rerun()
    
    with col2:
        if st.button("🗑️ 選択した行を削除", type="secondary", key="delete_grades"):
            selected_indices = edited_df[edited_df["選択"]]["番号"].tolist()
            if selected_indices:
                if delete_grades(subject, selected_indices):
                    st.success(f"✅ {len(selected_indices)}件のデータを削除しました")
                    st.rerun()
            else:
                st.warning("削除する行を選択してください")

def edit_progress_data():
    """進捗データの編集"""
    st.markdown("### 進捗データの管理")
    
    if not st.session_state.subjects:
        st.warning("科目が登録されていません")
        return
    
    subject = st.selectbox("科目を選択", st.session_state.subjects, key="progress_subject")
    
    if subject not in st.session_state.progress or not st.session_state.progress[subject]:
        st.info("この科目の進捗データはありません")
        return
    
    # データをDataFrameに変換
    progress_list = []
    for idx, prog in enumerate(st.session_state.progress[subject]):
        progress_list.append({
            "選択": False,
            "番号": idx,
            "日付": prog.get("date", ""),
            "学習時間": prog.get("time", 0),
            "タスク": prog.get("task", ""),
            "やる気": prog.get("motivation", "")
        })
    
    df = pd.DataFrame(progress_list)
    
    # データ編集
    st.markdown("#### データ編集")
    edited_df = st.data_editor(
        df,
        use_container_width=True,
        num_rows="fixed",
        column_config={
            "選択": st.column_config.CheckboxColumn("選択", help="削除する行を選択"),
            "番号": st.column_config.NumberColumn("番号", disabled=True),
            "日付": st.column_config.TextColumn("日付"),
            "学習時間": st.column_config.NumberColumn("学習時間(h)", min_value=0, max_value=24, step=0.5),
            "タスク": st.column_config.TextColumn("タスク", width="large"),
            "やる気": st.column_config.SelectboxColumn(
                "やる気",
                options=["低い", "普通", "高い"]
            )
        },
        hide_index=True,
        key="progress_editor"
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("✅ 変更を保存", type="primary", key="save_progress"):
            for idx, row in edited_df.iterrows():
                original_idx = int(row["番号"])
                if (row["日付"] != df.loc[idx, "日付"] or
                    row["学習時間"] != df.loc[idx, "学習時間"] or
                    row["タスク"] != df.loc[idx, "タスク"] or
                    row["やる気"] != df.loc[idx, "やる気"]):
                    update_progress(
                        subject, original_idx,
                        row["日付"], row["学習時間"], row["タスク"], row["やる気"]
                    )
            st.success("✅ 変更を保存しました")
            st.rerun()
    
    with col2:
        if st.button("🗑️ 選択した行を削除", type="secondary", key="delete_progress"):
            selected_indices = edited_df[edited_df["選択"]]["番号"].tolist()
            if selected_indices:
                if delete_progress(subject, selected_indices):
                    st.success(f"✅ {len(selected_indices)}件のデータを削除しました")
                    st.rerun()
            else:
                st.warning("削除する行を選択してください")

def edit_reminders_data():
    """リマインダーの編集"""
    st.markdown("### リマインダーの管理")
    
    if not os.path.exists('reminders.json'):
        st.info("リマインダーが登録されていません")
        return
    
    with open('reminders.json', 'r', encoding='utf-8') as f:
        reminders = json.load(f)
    
    if not reminders:
        st.info("リマインダーが登録されていません")
        return
    
    # データをDataFrameに変換
    reminder_list = []
    for idx, reminder in enumerate(reminders):
        reminder_list.append({
            "選択": False,
            "番号": idx,
            "科目": reminder.get("subject", ""),
            "タイプ": reminder.get("type", ""),
            "期日": reminder.get("date", ""),
            "内容": reminder.get("text", "")
        })
    
    df = pd.DataFrame(reminder_list)
    
    # データ編集
    st.markdown("#### データ編集")
    edited_df = st.data_editor(
        df,
        use_container_width=True,
        num_rows="fixed",
        column_config={
            "選択": st.column_config.CheckboxColumn("選択", help="削除する行を選択"),
            "番号": st.column_config.NumberColumn("番号", disabled=True),
            "科目": st.column_config.TextColumn("科目"),
            "タイプ": st.column_config.SelectboxColumn(
                "タイプ",
                options=["テスト", "課題", "その他"]
            ),
            "期日": st.column_config.TextColumn("期日"),
            "内容": st.column_config.TextColumn("内容", width="large")
        },
        hide_index=True,
        key="reminder_editor"
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("✅ 変更を保存", type="primary", key="save_reminders"):
            for idx, row in edited_df.iterrows():
                original_idx = int(row["番号"])
                if (row["科目"] != df.loc[idx, "科目"] or
                    row["タイプ"] != df.loc[idx, "タイプ"] or
                    row["期日"] != df.loc[idx, "期日"] or
                    row["内容"] != df.loc[idx, "内容"]):
                    update_reminder(
                        original_idx,
                        row["科目"], row["タイプ"], row["期日"], row["内容"]
                    )
            st.success("✅ 変更を保存しました")
            st.rerun()
    
    with col2:
        if st.button("🗑️ 選択した行を削除", type="secondary", key="delete_reminders"):
            selected_indices = edited_df[edited_df["選択"]]["番号"].tolist()
            if selected_indices:
                if delete_reminders(selected_indices):
                    st.success(f"✅ {len(selected_indices)}件のリマインダーを削除しました")
                    st.rerun()
            else:
                st.warning("削除する行を選択してください")

def manage_subjects():
    """科目管理"""
    st.markdown("### 科目管理")
    
    if not st.session_state.subjects:
        st.info("科目が登録されていません")
        return
    
    st.warning("⚠️ 科目を削除すると、関連する全データ（成績・進捗・目標・リマインダー）も削除されます")
    
    # 科目リスト表示
    subject_list = []
    for idx, subject in enumerate(st.session_state.subjects):
        # 関連データのカウント
        grades_count = len(st.session_state.grades.get(subject, []))
        progress_count = len(st.session_state.progress.get(subject, []))
        
        subject_list.append({
            "選択": False,
            "科目名": subject,
            "成績データ": grades_count,
            "進捗データ": progress_count
        })
    
    df = pd.DataFrame(subject_list)
    
    edited_df = st.data_editor(
        df,
        use_container_width=True,
        num_rows="fixed",
        column_config={
            "選択": st.column_config.CheckboxColumn("削除", help="削除する科目を選択"),
            "科目名": st.column_config.TextColumn("科目名", disabled=True),
            "成績データ": st.column_config.NumberColumn("成績データ件数", disabled=True),
            "進捗データ": st.column_config.NumberColumn("進捗データ件数", disabled=True)
        },
        hide_index=True,
        key="subject_manager"
    )
    
    if st.button("🗑️ 選択した科目を削除", type="secondary", key="delete_subjects"):
        selected_subjects = edited_df[edited_df["選択"]]["科目名"].tolist()
        if selected_subjects:
            for subject in selected_subjects:
                delete_subject(subject)
            st.success(f"✅ {len(selected_subjects)}件の科目と関連データを削除しました")
            st.rerun()
        else:
            st.warning("削除する科目を選択してください")

# =============== エクスポート機能 ===============

def display_data_export():
    """データエクスポート画面"""
    st.subheader("データのエクスポート")
    
    st.info("💡 すべてのデータをバックアップしたり、他の端末に移行できます")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📦 全データをZIPでダウンロード")
        if st.button("全データをZIPダウンロード", type="primary", key="export_zip"):
            zip_data = create_data_zip()
            if zip_data:
                st.download_button(
                    label="💾 ZIPファイルをダウンロード",
                    data=zip_data,
                    file_name=f"learning_data_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                    mime="application/zip"
                )
    
    with col2:
        st.markdown("### 📄 個別JSONダウンロード")
        
        json_files = {
            "科目データ": "subjects.json",
            "成績データ": "grades.json",
            "進捗データ": "progress.json",
            "リマインダー": "reminders.json",
            "ユーザープロフィール": "user_profile.json"
        }
        
        for label, filename in json_files.items():
            if os.path.exists(filename):
                with open(filename, 'r', encoding='utf-8') as f:
                    data = f.read()
                st.download_button(
                    label=f"📥 {label}",
                    data=data,
                    file_name=filename,
                    mime="application/json",
                    key=f"download_{filename}"
                )

def create_data_zip():
    """全データをZIPファイルに圧縮"""
    try:
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            json_files = ['subjects.json', 'grades.json', 'progress.json', 
                         'reminders.json', 'user_profile.json']
            
            for filename in json_files:
                if os.path.exists(filename):
                    zip_file.write(filename)
        
        return zip_buffer.getvalue()
    except Exception as e:
        st.error(f"ZIPファイル作成エラー: {str(e)}")
        return None

# =============== インポート機能 ===============

def display_data_import():
    """データインポート画面"""
    st.subheader("データのインポート")
    
    st.warning("⚠️ データをインポートすると、現在のデータは上書きされます。事前にバックアップを取ることを推奨します。")
    
    # バックアップボタン
    if st.button("💾 現在のデータをバックアップ", key="backup_before_import"):
        zip_data = create_data_zip()
        if zip_data:
            st.download_button(
                label="📥 バックアップをダウンロード",
                data=zip_data,
                file_name=f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                mime="application/zip",
                key="backup_download"
            )
    
    st.markdown("---")
    
    # ZIPファイルインポート
    st.markdown("### 📦 ZIPファイルからインポート")
    zip_file = st.file_uploader("ZIPファイルを選択", type=['zip'], key="import_zip")
    
    if zip_file:
        if st.button("📂 ZIPファイルをインポート", type="primary", key="import_zip_btn"):
            if import_from_zip(zip_file):
                st.success("✅ データのインポートに成功しました")
                st.rerun()
            else:
                st.error("❌ データのインポートに失敗しました")
    
    st.markdown("---")
    
    # 個別JSONインポート
    st.markdown("### 📄 個別JSONファイルからインポート")
    
    json_types = {
        "科目データ": "subjects.json",
        "成績データ": "grades.json",
        "進捗データ": "progress.json",
        "リマインダー": "reminders.json",
        "ユーザープロフィール": "user_profile.json"
    }
    
    import_type = st.selectbox("インポートするデータタイプ", list(json_types.keys()))
    json_file = st.file_uploader("JSONファイルを選択", type=['json'], key="import_json")
    
    if json_file:
        if st.button("📂 JSONファイルをインポート", type="primary", key="import_json_btn"):
            if import_json_file(json_file, json_types[import_type]):
                st.success(f"✅ {import_type}のインポートに成功しました")
                st.rerun()
            else:
                st.error(f"❌ {import_type}のインポートに失敗しました")

def import_from_zip(zip_file):
    """ZIPファイルからデータをインポート"""
    try:
        with zipfile.ZipFile(zip_file, 'r') as zip_ref:
            zip_ref.extractall('.')
        
        # セッションステートを再読み込み
        from data import load_subjects, load_grades, load_progress, load_user_profile
        load_subjects()
        load_grades()
        load_progress()
        load_user_profile()
        
        return True
    except Exception as e:
        st.error(f"インポートエラー: {str(e)}")
        return False

def import_json_file(uploaded_file, target_filename):
    """個別JSONファイルをインポート"""
    try:
        content = uploaded_file.read().decode('utf-8')
        data = json.loads(content)
        
        # ファイルに保存
        with open(target_filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        
        # セッションステートを更新
        if target_filename == 'subjects.json':
            st.session_state.subjects = data
        elif target_filename == 'grades.json':
            st.session_state.grades = data
        elif target_filename == 'progress.json':
            st.session_state.progress = data
        elif target_filename == 'user_profile.json':
            st.session_state.user_profile = data
        
        return True
    except Exception as e:
        st.error(f"インポートエラー: {str(e)}")
        return False
