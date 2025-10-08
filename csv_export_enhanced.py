# csv_export_enhanced.py - 強化版CSVエクスポート機能

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any
import io
from logger import log_info, log_error


# =========================
# ユーティリティ関数
# =========================

def parse_date_flexible(date_str: str) -> datetime:
    """柔軟な日付パース関数
    
    Args:
        date_str: 日付文字列 ('YYYY-MM-DD' または 'YYYY-MM-DD HH:MM:SS' 形式)
    
    Returns:
        datetime: パースされた日付
    """
    # スペースで分割して日付部分のみを取得
    date_part = date_str.split()[0] if ' ' in date_str else date_str
    return datetime.strptime(date_part, '%Y-%m-%d')


# =========================
# CSVエクスポート機能
# =========================

def display_csv_export():
    """CSVエクスポート管理画面"""
    st.title("📥 CSV エクスポート")
    st.markdown("学習データをCSV形式でエクスポートできます。Excel、Google スプレッドシートで開けます。")
    
    # タブで機能を分ける
    tab1, tab2, tab3, tab4 = st.tabs(["📊 成績データ", "⏱️ 学習時間", "🎯 目標データ", "📋 全データ"])
    
    with tab1:
        export_grades_csv()
    
    with tab2:
        export_progress_csv()
    
    with tab3:
        export_goals_csv()
    
    with tab4:
        export_all_data_csv()


# =========================
# 成績データのエクスポート
# =========================

def export_grades_csv():
    """成績データのCSVエクスポート"""
    st.subheader("📊 成績データをエクスポート")
    
    grades_data = st.session_state.get('grades', {})
    
    if not grades_data:
        st.info("💡 成績データがありません。")
        return
    
    # フィルタオプション
    st.markdown("#### 🔧 エクスポート設定")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 科目選択
        all_subjects = list(grades_data.keys())
        selected_subjects = st.multiselect(
            "エクスポートする科目",
            options=all_subjects,
            default=all_subjects
        )
    
    with col2:
        # 期間選択
        period_type = st.selectbox(
            "期間",
            options=["すべて", "今月", "先月", "今年", "カスタム"]
        )
    
    # カスタム期間の場合
    start_date = None
    end_date = None
    
    if period_type == "カスタム":
        col_date1, col_date2 = st.columns(2)
        with col_date1:
            start_date = st.date_input("開始日")
        with col_date2:
            end_date = st.date_input("終了日")
    
    # プレビュー
    st.markdown("---")
    st.markdown("#### 👁️ プレビュー")
    
    # データフィルタリング
    filtered_data = filter_grades_for_export(
        grades_data,
        selected_subjects,
        period_type,
        start_date,
        end_date
    )
    
    if not filtered_data:
        st.warning("⚠️ 指定した条件に該当するデータがありません。")
        return
    
    # データフレーム作成
    df = create_grades_dataframe(filtered_data)
    
    # プレビュー表示
    st.dataframe(df.head(10), use_container_width=True)
    st.info(f"💡 全 {len(df)} 件のデータがエクスポートされます。")
    
    # エクスポートボタン
    st.markdown("---")
    st.markdown("#### 📥 ダウンロード")
    
    col_btn1, col_btn2 = st.columns(2)
    
    with col_btn1:
        # CSV形式でダウンロード
        csv_data = df.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="📥 CSV形式でダウンロード",
            data=csv_data,
            file_name=f"成績データ_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    
    with col_btn2:
        # Excel形式でダウンロード
        excel_buffer = io.BytesIO()
        df.to_excel(excel_buffer, index=False, engine='openpyxl')
        excel_data = excel_buffer.getvalue()
        
        st.download_button(
            label="📥 Excel形式でダウンロード",
            data=excel_data,
            file_name=f"成績データ_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    
    log_info(f"成績データCSVエクスポート: {len(df)}件", "CSV_EXPORT")


def filter_grades_for_export(
    grades_data: Dict[str, List[Dict]],
    selected_subjects: List[str],
    period_type: str,
    start_date=None,
    end_date=None
) -> List[Dict]:
    """成績データをフィルタリング"""
    filtered = []
    
    today = datetime.now()
    
    for subject in selected_subjects:
        if subject not in grades_data:
            continue
        
        for grade in grades_data[subject]:
            grade_date = parse_date_flexible(grade['date'])
            
            # 期間フィルタ
            if period_type == "今月":
                if grade_date.year != today.year or grade_date.month != today.month:
                    continue
            elif period_type == "先月":
                last_month = today.replace(day=1) - timedelta(days=1)
                if grade_date.year != last_month.year or grade_date.month != last_month.month:
                    continue
            elif period_type == "今年":
                if grade_date.year != today.year:
                    continue
            elif period_type == "カスタム":
                if start_date and end_date:
                    if not (datetime.combine(start_date, datetime.min.time()) <= grade_date <= datetime.combine(end_date, datetime.max.time())):
                        continue
            
            filtered.append({
                'subject': subject,
                'date': grade['date'],
                'type': grade['type'],
                'grade': grade['grade'],
                'weight': grade.get('weight', 1.0),
                'comment': grade.get('comment', '')
            })
    
    return filtered


def create_grades_dataframe(grades_list: List[Dict]) -> pd.DataFrame:
    """成績データからDataFrameを作成"""
    df = pd.DataFrame(grades_list)
    
    # カラム名を日本語に変更
    df = df.rename(columns={
        'subject': '科目',
        'date': '日付',
        'type': '種類',
        'grade': '点数',
        'weight': '重み',
        'comment': 'コメント'
    })
    
    # 日付でソート
    df = df.sort_values('日付', ascending=False)
    
    return df


# =========================
# 学習時間データのエクスポート
# =========================

def export_progress_csv():
    """学習時間データのCSVエクスポート"""
    st.subheader("⏱️ 学習時間をエクスポート")
    
    progress_data = st.session_state.get('progress', {})
    
    if not progress_data:
        st.info("💡 学習時間のデータがありません。")
        return
    
    # フィルタオプション
    st.markdown("#### 🔧 エクスポート設定")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 科目選択
        all_subjects = list(progress_data.keys())
        selected_subjects = st.multiselect(
            "エクスポートする科目",
            options=all_subjects,
            default=all_subjects,
            key="progress_subjects"
        )
    
    with col2:
        # 期間選択
        period_type = st.selectbox(
            "期間",
            options=["すべて", "今月", "先月", "今年", "カスタム"],
            key="progress_period"
        )
    
    # カスタム期間
    start_date = None
    end_date = None
    
    if period_type == "カスタム":
        col_date1, col_date2 = st.columns(2)
        with col_date1:
            start_date = st.date_input("開始日", key="progress_start")
        with col_date2:
            end_date = st.date_input("終了日", key="progress_end")
    
    # データフィルタリング
    filtered_data = filter_progress_for_export(
        progress_data,
        selected_subjects,
        period_type,
        start_date,
        end_date
    )
    
    if not filtered_data:
        st.warning("⚠️ 指定した条件に該当するデータがありません。")
        return
    
    # データフレーム作成
    df = create_progress_dataframe(filtered_data)
    
    # プレビュー
    st.markdown("---")
    st.markdown("#### 👁️ プレビュー")
    st.dataframe(df.head(10), use_container_width=True)
    st.info(f"💡 全 {len(df)} 件のデータがエクスポートされます。")
    
    # 統計情報
    total_hours = df['学習時間'].sum()
    st.metric("合計学習時間", f"{total_hours:.1f} 時間")
    
    # ダウンロード
    st.markdown("---")
    st.markdown("#### 📥 ダウンロード")
    
    csv_data = df.to_csv(index=False, encoding='utf-8-sig')
    st.download_button(
        label="📥 CSV形式でダウンロード",
        data=csv_data,
        file_name=f"学習時間_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )
    
    log_info(f"学習時間CSVエクスポート: {len(df)}件", "CSV_EXPORT")


def filter_progress_for_export(
    progress_data: Dict[str, List[Dict]],
    selected_subjects: List[str],
    period_type: str,
    start_date=None,
    end_date=None
) -> List[Dict]:
    """学習時間データをフィルタリング"""
    filtered = []
    
    today = datetime.now()
    
    for subject in selected_subjects:
        if subject not in progress_data:
            continue
        
        for progress in progress_data[subject]:
            progress_date = parse_date_flexible(progress['date'])
            
            # 期間フィルタ
            if period_type == "今月":
                if progress_date.year != today.year or progress_date.month != today.month:
                    continue
            elif period_type == "先月":
                last_month = today.replace(day=1) - timedelta(days=1)
                if progress_date.year != last_month.year or progress_date.month != last_month.month:
                    continue
            elif period_type == "今年":
                if progress_date.year != today.year:
                    continue
            elif period_type == "カスタム":
                if start_date and end_date:
                    if not (datetime.combine(start_date, datetime.min.time()) <= progress_date <= datetime.combine(end_date, datetime.max.time())):
                        continue
            
            filtered.append({
                'subject': subject,
                'date': progress['date'],
                'time': progress['time'],
                'task': progress.get('task', ''),
                'motivation': progress.get('motivation', 0)
            })
    
    return filtered


def create_progress_dataframe(progress_list: List[Dict]) -> pd.DataFrame:
    """学習時間データからDataFrameを作成"""
    df = pd.DataFrame(progress_list)
    
    # カラム名を日本語に変更
    df = df.rename(columns={
        'subject': '科目',
        'date': '日付',
        'time': '学習時間',
        'task': '学習内容',
        'motivation': 'モチベーション'
    })
    
    # 日付でソート
    df = df.sort_values('日付', ascending=False)
    
    return df


# =========================
# 目標データのエクスポート
# =========================

def export_goals_csv():
    """目標データのCSVエクスポート"""
    st.subheader("🎯 目標データをエクスポート")
    
    goals_data = st.session_state.get('goals', [])
    
    if not goals_data:
        st.info("💡 目標データがありません。")
        return
    
    # データフレーム作成
    df = create_goals_dataframe(goals_data)
    
    # プレビュー
    st.markdown("#### 👁️ プレビュー")
    st.dataframe(df, use_container_width=True)
    st.info(f"💡 全 {len(df)} 件のデータがエクスポートされます。")
    
    # ダウンロード
    st.markdown("---")
    st.markdown("#### 📥 ダウンロード")
    
    csv_data = df.to_csv(index=False, encoding='utf-8-sig')
    st.download_button(
        label="📥 CSV形式でダウンロード",
        data=csv_data,
        file_name=f"目標データ_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )
    
    log_info(f"目標データCSVエクスポート: {len(df)}件", "CSV_EXPORT")


def create_goals_dataframe(goals_list: List[Dict]) -> pd.DataFrame:
    """目標データからDataFrameを作成"""
    df = pd.DataFrame(goals_list)
    
    # カラム名を日本語に変更
    df = df.rename(columns={
        'subject': '科目',
        'goal_type': '目標タイプ',
        'goal': '目標内容',
        'deadline': '期限',
        'status': 'ステータス'
    })
    
    return df


# =========================
# 全データのエクスポート
# =========================

def export_all_data_csv():
    """全データを一括エクスポート"""
    st.subheader("📋 全データを一括エクスポート")
    st.markdown("すべての学習データを一度にエクスポートします。")
    
    # データ件数表示
    grades_count = sum([len(records) for records in st.session_state.get('grades', {}).values()])
    progress_count = sum([len(records) for records in st.session_state.get('progress', {}).values()])
    goals_count = len(st.session_state.get('goals', []))
    reminders_count = len(st.session_state.get('reminders', []))
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("成績記録", f"{grades_count}件")
    with col2:
        st.metric("学習時間", f"{progress_count}件")
    with col3:
        st.metric("目標", f"{goals_count}件")
    with col4:
        st.metric("リマインダー", f"{reminders_count}件")
    
    # エクスポート形式選択
    export_format = st.radio(
        "エクスポート形式",
        options=["個別CSV (ZIPファイル)", "統合Excel (複数シート)"],
        horizontal=True
    )
    
    st.markdown("---")
    
    if export_format == "個別CSV (ZIPファイル)":
        # ZIP形式でダウンロード
        if st.button("📥 全データをZIPでダウンロード", type="primary"):
            import zipfile
            
            zip_buffer = io.BytesIO()
            
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                # 成績データ
                if grades_count > 0:
                    grades_data = st.session_state.get('grades', {})
                    filtered_grades = filter_grades_for_export(grades_data, list(grades_data.keys()), "すべて")
                    df_grades = create_grades_dataframe(filtered_grades)
                    csv_grades = df_grades.to_csv(index=False, encoding='utf-8-sig')
                    zip_file.writestr('成績データ.csv', csv_grades.encode('utf-8-sig'))
                
                # 学習時間データ
                if progress_count > 0:
                    progress_data = st.session_state.get('progress', {})
                    filtered_progress = filter_progress_for_export(progress_data, list(progress_data.keys()), "すべて")
                    df_progress = create_progress_dataframe(filtered_progress)
                    csv_progress = df_progress.to_csv(index=False, encoding='utf-8-sig')
                    zip_file.writestr('学習時間.csv', csv_progress.encode('utf-8-sig'))
                
                # 目標データ
                if goals_count > 0:
                    goals_data = st.session_state.get('goals', [])
                    df_goals = create_goals_dataframe(goals_data)
                    csv_goals = df_goals.to_csv(index=False, encoding='utf-8-sig')
                    zip_file.writestr('目標データ.csv', csv_goals.encode('utf-8-sig'))
            
            st.download_button(
                label="📥 ZIPファイルをダウンロード",
                data=zip_buffer.getvalue(),
                file_name=f"学習データ一括_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                mime="application/zip"
            )
            
            st.success("✅ ZIPファイルの準備が完了しました!")
            log_info("全データZIPエクスポート完了", "CSV_EXPORT")
    
    else:
        # Excel形式でダウンロード (複数シート)
        if st.button("📥 統合Excelファイルをダウンロード", type="primary"):
            excel_buffer = io.BytesIO()
            
            with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                # 成績データ
                if grades_count > 0:
                    grades_data = st.session_state.get('grades', {})
                    filtered_grades = filter_grades_for_export(grades_data, list(grades_data.keys()), "すべて")
                    df_grades = create_grades_dataframe(filtered_grades)
                    df_grades.to_excel(writer, sheet_name='成績データ', index=False)
                
                # 学習時間データ
                if progress_count > 0:
                    progress_data = st.session_state.get('progress', {})
                    filtered_progress = filter_progress_for_export(progress_data, list(progress_data.keys()), "すべて")
                    df_progress = create_progress_dataframe(filtered_progress)
                    df_progress.to_excel(writer, sheet_name='学習時間', index=False)
                
                # 目標データ
                if goals_count > 0:
                    goals_data = st.session_state.get('goals', [])
                    df_goals = create_goals_dataframe(goals_data)
                    df_goals.to_excel(writer, sheet_name='目標データ', index=False)
            
            st.download_button(
                label="📥 Excelファイルをダウンロード",
                data=excel_buffer.getvalue(),
                file_name=f"学習データ統合_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
            st.success("✅ Excelファイルの準備が完了しました!")
            log_info("全データExcelエクスポート完了", "CSV_EXPORT")
