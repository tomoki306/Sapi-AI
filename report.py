# report.py
# 学習レポート生成機能

import streamlit as st
from datetime import datetime, timedelta
from ai_learning_report import generate_learning_report

def display_learning_report():
    """学習レポート生成画面"""
    st.header("📊 学習レポート生成")
    
    st.info("💡 蓄積された成績と進捗データから、AIが総合的な学習レポートを作成します")
    
    # 期間選択
    st.subheader("📅 レポート期間を選択")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        period_type = st.selectbox(
            "期間タイプ",
            ["今週", "今月", "全期間", "カスタム"]
        )
    
    with col2:
        if period_type == "カスタム":
            col_a, col_b = st.columns(2)
            with col_a:
                start_date = st.date_input(
                    "開始日",
                    value=datetime.now() - timedelta(days=30)
                )
            with col_b:
                end_date = st.date_input(
                    "終了日",
                    value=datetime.now()
                )
    
    # データの準備
    if period_type == "今週":
        period_label = "今週"
        start = datetime.now() - timedelta(days=datetime.now().weekday())
        end = datetime.now()
    elif period_type == "今月":
        period_label = "今月"
        start = datetime.now().replace(day=1)
        end = datetime.now()
    elif period_type == "全期間":
        period_label = "全期間"
        start = None
        end = None
    else:  # カスタム
        period_label = f"{start_date.strftime('%Y/%m/%d')} - {end_date.strftime('%Y/%m/%d')}"
        start = datetime.combine(start_date, datetime.min.time())
        end = datetime.combine(end_date, datetime.max.time())
    
    # データのフィルタリング
    filtered_grades = filter_grades_by_period(start, end)
    filtered_progress = filter_progress_by_period(start, end)
    
    # データサマリー表示
    st.markdown("---")
    st.subheader("📈 データサマリー")
    
    col1, col2, col3, col4 = st.columns(4)
    
    # 科目数
    with col1:
        subjects_count = len(set(list(filtered_grades.keys()) + list(filtered_progress.keys())))
        st.metric("科目数", subjects_count)
    
    # 成績データ数
    with col2:
        grades_count = sum(len(grades) for grades in filtered_grades.values())
        st.metric("成績データ数", f"{grades_count}件")
    
    # 進捗データ数
    with col3:
        progress_count = sum(len(progress) for progress in filtered_progress.values())
        st.metric("学習記録数", f"{progress_count}件")
    
    # 総学習時間
    with col4:
        total_hours = sum(
            sum(p['time'] for p in progress)
            for progress in filtered_progress.values()
        )
        st.metric("総学習時間", f"{total_hours:.1f}時間")
    
    # レポート生成ボタン
    st.markdown("---")
    if st.button("🤖 AIレポートを生成", type="primary", disabled=grades_count == 0 and progress_count == 0):
        if grades_count == 0 and progress_count == 0:
            st.warning("この期間のデータがありません")
        else:
            with st.spinner("AIがレポートを作成しています..."):
                report_content = generate_learning_report(
                    period=period_label,
                    grades_data=filtered_grades,
                    progress_data=filtered_progress
                )
                
                if report_content:
                    st.session_state.generated_report = {
                        "period": period_label,
                        "content": report_content,
                        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "data_summary": {
                            "subjects": subjects_count,
                            "grades": grades_count,
                            "progress": progress_count,
                            "total_hours": total_hours
                        }
                    }
    
    # 生成されたレポートの表示
    if 'generated_report' in st.session_state and st.session_state.generated_report:
        st.markdown("---")
        st.subheader("✨ 生成されたレポート")
        
        report = st.session_state.generated_report
        
        # レポート情報
        st.caption(f"作成日時: {report['created_at']} | 対象期間: {report['period']}")
        
        # レポート内容
        st.markdown(report['content'])
        
        # ダウンロードボタン
        st.markdown("---")
        col1, col2 = st.columns(2)
        
        with col1:
            report_text = format_report_for_download(report)
            st.download_button(
                label="📥 レポートをダウンロード",
                data=report_text,
                file_name=f"learning_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain",
                type="primary"
            )
        
        with col2:
            if st.button("🔄 新しいレポートを作成", type="secondary"):
                del st.session_state.generated_report
                st.rerun()

# =============== ヘルパー関数 ===============

def filter_grades_by_period(start, end):
    """期間でフィルタリングした成績データを返す"""
    if 'grades' not in st.session_state:
        return {}
    
    filtered = {}
    
    for subject, grades in st.session_state.grades.items():
        if not grades:
            continue
        
        filtered_grades = []
        for grade in grades:
            if start is None and end is None:
                # 全期間
                filtered_grades.append(grade)
            else:
                try:
                    grade_date = datetime.strptime(grade['date'], "%Y-%m-%d %H:%M:%S")
                    if start <= grade_date <= end:
                        filtered_grades.append(grade)
                except Exception:
                    # 日付パースエラーはスキップ
                    continue
        
        if filtered_grades:
            filtered[subject] = filtered_grades
    
    return filtered

def filter_progress_by_period(start, end):
    """期間でフィルタリングした進捗データを返す"""
    if 'progress' not in st.session_state:
        return {}
    
    filtered = {}
    
    for subject, progress in st.session_state.progress.items():
        if not progress:
            continue
        
        filtered_progress = []
        for prog in progress:
            if start is None and end is None:
                # 全期間
                filtered_progress.append(prog)
            else:
                try:
                    prog_date = datetime.strptime(prog['date'], "%Y-%m-%d")
                    if start.date() <= prog_date.date() <= end.date():
                        filtered_progress.append(prog)
                except Exception:
                    # 日付パースエラーはスキップ
                    continue
        
        if filtered_progress:
            filtered[subject] = filtered_progress
    
    return filtered

def format_report_for_download(report):
    """ダウンロード用にテキスト形式にフォーマット"""
    text = f"""
======================================
学習レポート
======================================

作成日時: {report['created_at']}
対象期間: {report['period']}

【データサマリー】
- 科目数: {report['data_summary']['subjects']}
- 成績データ数: {report['data_summary']['grades']}件
- 学習記録数: {report['data_summary']['progress']}件
- 総学習時間: {report['data_summary']['total_hours']:.1f}時間

======================================

{report['content']}

======================================
この学習レポートは学習管理システムで生成されました
======================================
"""
    return text
