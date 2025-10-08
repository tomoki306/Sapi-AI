# auto_reports.py - 統計レポート自動生成機能

import streamlit as st
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
import pandas as pd
from logger import log_info, log_error

# レポート保存ディレクトリ
REPORTS_DIR = "reports"

# レポート設定ファイル
REPORT_SETTINGS_FILE = "report_settings.json"


# =========================
# ヘルパー関数
# =========================

def parse_date_flexible(date_str: str) -> datetime:
    """
    柔軟な日付パース（YYYY-MM-DD または YYYY-MM-DD HH:MM:SS に対応）
    
    Args:
        date_str: 日付文字列
    
    Returns:
        datetimeオブジェクト
    """
    try:
        # 時刻付きの場合
        if ' ' in date_str:
            return datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
        else:
            return datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        # デフォルト値を返す
        return datetime.now()


# =========================
# レポート設定の読み込み・保存
# =========================

def load_report_settings() -> Dict[str, Any]:
    """レポート設定を読み込む"""
    if os.path.exists(REPORT_SETTINGS_FILE):
        try:
            with open(REPORT_SETTINGS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            log_error(e, "レポート設定読み込みエラー")
    
    # デフォルト設定
    return {
        "auto_generate_weekly": True,
        "auto_generate_monthly": True,
        "last_weekly_report": None,
        "last_monthly_report": None
    }


def save_report_settings(settings: Dict[str, Any]):
    """レポート設定を保存"""
    try:
        with open(REPORT_SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
    except Exception as e:
        log_error(e, "レポート設定保存エラー")


# =========================
# レポート生成関数
# =========================

def generate_weekly_report() -> str:
    """週次レポートを生成"""
    today = datetime.now()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    
    report_lines = []
    report_lines.append("=" * 50)
    report_lines.append("📊 週次学習レポート")
    report_lines.append("=" * 50)
    report_lines.append(f"期間: {week_start.strftime('%Y年%m月%d日')} 〜 {week_end.strftime('%Y年%m月%d日')}")
    report_lines.append(f"作成日時: {today.strftime('%Y年%m月%d日 %H:%M:%S')}")
    report_lines.append("")
    
    # 成績データの取得
    grades_data = st.session_state.get('grades', {})
    week_grades = []
    
    for subject, records in grades_data.items():
        for record in records:
            record_date = parse_date_flexible(record['date'])
            if week_start <= record_date <= week_end:
                week_grades.append({
                    'subject': subject,
                    'date': record['date'],
                    'grade': record['grade'],
                    'type': record['type']
                })
    
    # 成績サマリー
    report_lines.append("## 📝 今週の成績サマリー")
    report_lines.append("-" * 50)
    
    if week_grades:
        total_grades = len(week_grades)
        avg_grade = sum([g['grade'] for g in week_grades]) / total_grades
        max_grade = max([g['grade'] for g in week_grades])
        min_grade = min([g['grade'] for g in week_grades])
        
        report_lines.append(f"記録数: {total_grades}件")
        report_lines.append(f"平均点: {avg_grade:.1f}点")
        report_lines.append(f"最高点: {max_grade}点")
        report_lines.append(f"最低点: {min_grade}点")
        report_lines.append("")
        
        # 科目別サマリー
        report_lines.append("### 科目別内訳")
        subject_summary = {}
        for grade in week_grades:
            subject = grade['subject']
            if subject not in subject_summary:
                subject_summary[subject] = []
            subject_summary[subject].append(grade['grade'])
        
        for subject, grades_list in subject_summary.items():
            avg = sum(grades_list) / len(grades_list)
            report_lines.append(f"  • {subject}: 平均 {avg:.1f}点 ({len(grades_list)}件)")
        
        report_lines.append("")
    else:
        report_lines.append("今週は成績の記録がありません。")
        report_lines.append("")
    
    # 学習時間サマリー
    report_lines.append("## ⏱️ 今週の学習時間")
    report_lines.append("-" * 50)
    
    progress_data = st.session_state.get('progress', {})
    week_progress = []
    
    for subject, records in progress_data.items():
        for record in records:
            record_date = parse_date_flexible(record['date'])
            if week_start <= record_date <= week_end:
                week_progress.append({
                    'subject': subject,
                    'date': record['date'],
                    'time': record['time']
                })
    
    if week_progress:
        total_time = sum([p['time'] for p in week_progress])
        report_lines.append(f"合計学習時間: {total_time:.1f}時間")
        report_lines.append("")
        
        # 科目別学習時間
        report_lines.append("### 科目別学習時間")
        subject_time = {}
        for progress in week_progress:
            subject = progress['subject']
            if subject not in subject_time:
                subject_time[subject] = 0
            subject_time[subject] += progress['time']
        
        for subject, time in sorted(subject_time.items(), key=lambda x: x[1], reverse=True):
            percentage = (time / total_time) * 100
            report_lines.append(f"  • {subject}: {time:.1f}時間 ({percentage:.1f}%)")
        
        report_lines.append("")
    else:
        report_lines.append("今週は学習時間の記録がありません。")
        report_lines.append("")
    
    # 目標達成状況
    report_lines.append("## 🎯 目標達成状況")
    report_lines.append("-" * 50)
    
    goals_data = st.session_state.get('goals', [])
    active_goals = [g for g in goals_data if g.get('status', 'active') == 'active']
    
    if active_goals:
        report_lines.append(f"現在のアクティブ目標: {len(active_goals)}件")
        for goal in active_goals[:5]:  # 最大5件表示
            report_lines.append(f"  • {goal.get('subject', '不明')}: {goal.get('goal', '目標内容なし')}")
        report_lines.append("")
    else:
        report_lines.append("アクティブな目標がありません。")
        report_lines.append("")
    
    # リマインダー状況
    report_lines.append("## 🔔 リマインダー状況")
    report_lines.append("-" * 50)
    
    reminders = st.session_state.get('reminders', [])
    overdue_reminders = []
    
    for reminder in reminders:
        if not reminder.get('completed', False):
            reminder_date = parse_date_flexible(reminder['date'])
            if reminder_date < today:
                overdue_reminders.append(reminder)
    
    if overdue_reminders:
        report_lines.append(f"⚠️ 期限切れリマインダー: {len(overdue_reminders)}件")
        for reminder in overdue_reminders[:5]:
            report_lines.append(f"  • {reminder.get('text', '内容なし')} (期限: {reminder.get('date', '不明')})")
    else:
        report_lines.append("期限切れのリマインダーはありません。")
    
    report_lines.append("")
    report_lines.append("=" * 50)
    report_lines.append("レポート生成完了")
    report_lines.append("=" * 50)
    
    return "\n".join(report_lines)


def generate_monthly_report() -> str:
    """月次レポートを生成"""
    today = datetime.now()
    month_start = datetime(today.year, today.month, 1)
    
    # 翌月の1日から1日引いて月末を取得
    if today.month == 12:
        next_month = datetime(today.year + 1, 1, 1)
    else:
        next_month = datetime(today.year, today.month + 1, 1)
    month_end = next_month - timedelta(days=1)
    
    report_lines = []
    report_lines.append("=" * 50)
    report_lines.append("📊 月次学習レポート")
    report_lines.append("=" * 50)
    report_lines.append(f"期間: {month_start.strftime('%Y年%m月%d日')} 〜 {month_end.strftime('%Y年%m月%d日')}")
    report_lines.append(f"作成日時: {today.strftime('%Y年%m月%d日 %H:%M:%S')}")
    report_lines.append("")
    
    # 成績データの取得
    grades_data = st.session_state.get('grades', {})
    month_grades = []
    
    for subject, records in grades_data.items():
        for record in records:
            record_date = parse_date_flexible(record['date'])
            if month_start <= record_date <= month_end:
                month_grades.append({
                    'subject': subject,
                    'date': record['date'],
                    'grade': record['grade'],
                    'type': record['type'],
                    'weight': record.get('weight', 1.0)
                })
    
    # 成績サマリー
    report_lines.append("## 📝 今月の成績サマリー")
    report_lines.append("-" * 50)
    
    if month_grades:
        total_grades = len(month_grades)
        avg_grade = sum([g['grade'] for g in month_grades]) / total_grades
        max_grade = max([g['grade'] for g in month_grades])
        min_grade = min([g['grade'] for g in month_grades])
        
        report_lines.append(f"記録数: {total_grades}件")
        report_lines.append(f"平均点: {avg_grade:.1f}点")
        report_lines.append(f"最高点: {max_grade}点")
        report_lines.append(f"最低点: {min_grade}点")
        report_lines.append("")
        
        # 科目別サマリー
        report_lines.append("### 📚 科目別統計")
        subject_summary = {}
        for grade in month_grades:
            subject = grade['subject']
            if subject not in subject_summary:
                subject_summary[subject] = []
            subject_summary[subject].append(grade['grade'])
        
        for subject, grades_list in sorted(subject_summary.items()):
            avg = sum(grades_list) / len(grades_list)
            max_g = max(grades_list)
            min_g = min(grades_list)
            report_lines.append(f"  • {subject}:")
            report_lines.append(f"    - 平均: {avg:.1f}点")
            report_lines.append(f"    - 最高: {max_g}点")
            report_lines.append(f"    - 最低: {min_g}点")
            report_lines.append(f"    - 記録数: {len(grades_list)}件")
        
        report_lines.append("")
        
        # 種類別統計
        report_lines.append("### 📋 種類別統計")
        type_summary = {}
        for grade in month_grades:
            grade_type = grade['type']
            if grade_type not in type_summary:
                type_summary[grade_type] = []
            type_summary[grade_type].append(grade['grade'])
        
        for grade_type, grades_list in sorted(type_summary.items()):
            avg = sum(grades_list) / len(grades_list)
            report_lines.append(f"  • {grade_type}: 平均 {avg:.1f}点 ({len(grades_list)}件)")
        
        report_lines.append("")
    else:
        report_lines.append("今月は成績の記録がありません。")
        report_lines.append("")
    
    # 学習時間サマリー
    report_lines.append("## ⏱️ 今月の学習時間")
    report_lines.append("-" * 50)
    
    progress_data = st.session_state.get('progress', {})
    month_progress = []
    
    for subject, records in progress_data.items():
        for record in records:
            record_date = parse_date_flexible(record['date'])
            if month_start <= record_date <= month_end:
                month_progress.append({
                    'subject': subject,
                    'date': record['date'],
                    'time': record['time']
                })
    
    if month_progress:
        total_time = sum([p['time'] for p in month_progress])
        report_lines.append(f"合計学習時間: {total_time:.1f}時間")
        report_lines.append(f"1日平均: {total_time / month_end.day:.1f}時間")
        report_lines.append("")
        
        # 科目別学習時間
        report_lines.append("### 📚 科目別学習時間")
        subject_time = {}
        for progress in month_progress:
            subject = progress['subject']
            if subject not in subject_time:
                subject_time[subject] = 0
            subject_time[subject] += progress['time']
        
        for subject, time in sorted(subject_time.items(), key=lambda x: x[1], reverse=True):
            percentage = (time / total_time) * 100
            report_lines.append(f"  • {subject}: {time:.1f}時間 ({percentage:.1f}%)")
        
        report_lines.append("")
    else:
        report_lines.append("今月は学習時間の記録がありません。")
        report_lines.append("")
    
    # 前月比較 (データがある場合)
    report_lines.append("## 📈 前月比較")
    report_lines.append("-" * 50)
    
    # 前月のデータ取得
    if month_start.month == 1:
        prev_month_start = datetime(month_start.year - 1, 12, 1)
        prev_month_end = datetime(month_start.year, 1, 1) - timedelta(days=1)
    else:
        prev_month_start = datetime(month_start.year, month_start.month - 1, 1)
        prev_month_end = month_start - timedelta(days=1)
    
    prev_month_grades = []
    for subject, records in grades_data.items():
        for record in records:
            record_date = parse_date_flexible(record['date'])
            if prev_month_start <= record_date <= prev_month_end:
                prev_month_grades.append({'grade': record['grade']})
    
    if prev_month_grades and month_grades:
        prev_avg = sum([g['grade'] for g in prev_month_grades]) / len(prev_month_grades)
        current_avg = sum([g['grade'] for g in month_grades]) / len(month_grades)
        diff = current_avg - prev_avg
        
        report_lines.append(f"前月平均: {prev_avg:.1f}点")
        report_lines.append(f"今月平均: {current_avg:.1f}点")
        
        if diff > 0:
            report_lines.append(f"変化: +{diff:.1f}点 (📈 改善)")
        elif diff < 0:
            report_lines.append(f"変化: {diff:.1f}点 (📉 低下)")
        else:
            report_lines.append(f"変化: 変化なし (➡️)")
    else:
        report_lines.append("前月のデータがないため比較できません。")
    
    report_lines.append("")
    
    # 目標達成状況
    report_lines.append("## 🎯 目標達成状況")
    report_lines.append("-" * 50)
    
    goals_data = st.session_state.get('goals', [])
    
    if goals_data:
        completed_goals = [g for g in goals_data if g.get('status') == 'completed']
        active_goals = [g for g in goals_data if g.get('status', 'active') == 'active']
        
        report_lines.append(f"達成済み目標: {len(completed_goals)}件")
        report_lines.append(f"進行中目標: {len(active_goals)}件")
        report_lines.append("")
    else:
        report_lines.append("目標が設定されていません。")
        report_lines.append("")
    
    report_lines.append("=" * 50)
    report_lines.append("レポート生成完了")
    report_lines.append("=" * 50)
    
    return "\n".join(report_lines)


def save_report_to_file(report_content: str, report_type: str) -> str:
    """レポートをファイルに保存"""
    # reportsディレクトリがなければ作成
    if not os.path.exists(REPORTS_DIR):
        os.makedirs(REPORTS_DIR)
    
    # ファイル名生成
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{report_type}_report_{timestamp}.txt"
    filepath = os.path.join(REPORTS_DIR, filename)
    
    # ファイル保存
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report_content)
        log_info(f"{report_type}レポート保存: {filename}", "AUTO_REPORTS")
        return filepath
    except Exception as e:
        log_error(e, f"{report_type}レポート保存エラー")
        return None


def check_and_generate_auto_reports():
    """自動レポート生成のチェック (起動時に呼び出す)"""
    settings = load_report_settings()
    today = datetime.now()
    
    # 週次レポートのチェック
    if settings.get('auto_generate_weekly', True):
        last_weekly = settings.get('last_weekly_report')
        if last_weekly:
            last_date = datetime.strptime(last_weekly, '%Y-%m-%d')
            # 1週間以上経過していればレポート生成
            if (today - last_date).days >= 7:
                report_content = generate_weekly_report()
                save_report_to_file(report_content, "weekly")
                settings['last_weekly_report'] = today.strftime('%Y-%m-%d')
                save_report_settings(settings)
                log_info("週次レポート自動生成完了", "AUTO_REPORTS")
        else:
            # 初回実行
            report_content = generate_weekly_report()
            save_report_to_file(report_content, "weekly")
            settings['last_weekly_report'] = today.strftime('%Y-%m-%d')
            save_report_settings(settings)
    
    # 月次レポートのチェック
    if settings.get('auto_generate_monthly', True):
        last_monthly = settings.get('last_monthly_report')
        if last_monthly:
            last_date = datetime.strptime(last_monthly, '%Y-%m-%d')
            # 月が変わっていればレポート生成
            if last_date.month != today.month or last_date.year != today.year:
                report_content = generate_monthly_report()
                save_report_to_file(report_content, "monthly")
                settings['last_monthly_report'] = today.strftime('%Y-%m-%d')
                save_report_settings(settings)
                log_info("月次レポート自動生成完了", "AUTO_REPORTS")
        else:
            # 初回実行
            report_content = generate_monthly_report()
            save_report_to_file(report_content, "monthly")
            settings['last_monthly_report'] = today.strftime('%Y-%m-%d')
            save_report_settings(settings)


# =========================
# UI機能
# =========================

def display_auto_reports():
    """自動レポート管理画面"""
    st.title("📊 統計レポート自動生成")
    st.markdown("週次・月次の学習レポートを自動生成します。")
    
    # タブで機能を分ける
    tab1, tab2, tab3 = st.tabs(["📅 レポート生成", "📁 レポート履歴", "⚙️ 設定"])
    
    with tab1:
        display_report_generation()
    
    with tab2:
        display_report_history()
    
    with tab3:
        display_report_settings()


def display_report_generation():
    """レポート生成タブ"""
    st.subheader("📅 レポートを生成")
    
    report_type = st.radio(
        "生成するレポートの種類",
        options=["週次レポート", "月次レポート"],
        horizontal=True
    )
    
    if st.button("📊 レポートを生成", type="primary"):
        with st.spinner("レポートを生成中..."):
            if report_type == "週次レポート":
                report_content = generate_weekly_report()
                filepath = save_report_to_file(report_content, "weekly")
            else:
                report_content = generate_monthly_report()
                filepath = save_report_to_file(report_content, "monthly")
            
            if filepath:
                st.success(f"✅ {report_type}を生成しました!")
                
                # レポート内容のプレビュー
                with st.expander("📄 レポート内容をプレビュー", expanded=True):
                    st.text(report_content)
                
                # ダウンロードボタン
                st.download_button(
                    label="📥 レポートをダウンロード",
                    data=report_content,
                    file_name=os.path.basename(filepath),
                    mime="text/plain"
                )
            else:
                st.error("❌ レポートの保存に失敗しました。")


def display_report_history():
    """レポート履歴タブ"""
    st.subheader("📁 過去のレポート")
    
    if not os.path.exists(REPORTS_DIR):
        st.info("💡 レポート履歴がありません。")
        return
    
    # レポートファイル一覧取得
    report_files = [f for f in os.listdir(REPORTS_DIR) if f.endswith('.txt')]
    
    if not report_files:
        st.info("💡 レポート履歴がありません。")
        return
    
    # 新しい順にソート
    report_files.sort(reverse=True)
    
    st.markdown(f"**全レポート数**: {len(report_files)}件")
    
    # フィルタ
    filter_type = st.selectbox(
        "フィルタ",
        options=["すべて", "週次レポート", "月次レポート"]
    )
    
    filtered_files = report_files
    if filter_type == "週次レポート":
        filtered_files = [f for f in report_files if "weekly" in f]
    elif filter_type == "月次レポート":
        filtered_files = [f for f in report_files if "monthly" in f]
    
    # レポート一覧表示
    for filename in filtered_files[:20]:  # 最大20件表示
        filepath = os.path.join(REPORTS_DIR, filename)
        
        # ファイル情報
        file_stat = os.stat(filepath)
        file_size = file_stat.st_size
        file_date = datetime.fromtimestamp(file_stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
        
        report_type_label = "📅 週次" if "weekly" in filename else "📊 月次"
        
        with st.expander(f"{report_type_label} - {filename} ({file_date})"):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**ファイル名**: {filename}")
                st.markdown(f"**作成日時**: {file_date}")
                st.markdown(f"**ファイルサイズ**: {file_size} bytes")
            
            with col2:
                # プレビューボタン
                if st.button("👁️ プレビュー", key=f"preview_{filename}"):
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    st.text(content)
                
                # ダウンロードボタン
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                st.download_button(
                    label="📥 ダウンロード",
                    data=content,
                    file_name=filename,
                    mime="text/plain",
                    key=f"download_{filename}"
                )
                
                # 削除ボタン
                if st.button("🗑️ 削除", key=f"delete_{filename}"):
                    os.remove(filepath)
                    st.success(f"✅ {filename} を削除しました。")
                    st.rerun()


def display_report_settings():
    """レポート設定タブ"""
    st.subheader("⚙️ レポート設定")
    
    settings = load_report_settings()
    
    st.markdown("#### 自動生成設定")
    
    auto_weekly = st.checkbox(
        "週次レポートを自動生成",
        value=settings.get('auto_generate_weekly', True)
    )
    
    auto_monthly = st.checkbox(
        "月次レポートを自動生成",
        value=settings.get('auto_generate_monthly', True)
    )
    
    if st.button("💾 設定を保存"):
        settings['auto_generate_weekly'] = auto_weekly
        settings['auto_generate_monthly'] = auto_monthly
        save_report_settings(settings)
        st.success("✅ 設定を保存しました!")
    
    # 最終生成日時表示
    st.markdown("---")
    st.markdown("#### 📅 最終生成日時")
    
    last_weekly = settings.get('last_weekly_report')
    last_monthly = settings.get('last_monthly_report')
    
    if last_weekly:
        st.markdown(f"**週次レポート**: {last_weekly}")
    else:
        st.markdown("**週次レポート**: まだ生成されていません")
    
    if last_monthly:
        st.markdown(f"**月次レポート**: {last_monthly}")
    else:
        st.markdown("**月次レポート**: まだ生成されていません")
    
    # 手動で自動生成チェック実行
    st.markdown("---")
    st.markdown("#### 🔄 手動チェック")
    if st.button("🔄 自動生成をチェック"):
        check_and_generate_auto_reports()
        st.success("✅ チェックが完了しました。")
        st.rerun()
