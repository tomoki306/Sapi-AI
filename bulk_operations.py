# bulk_operations.py
"""
データの一括操作機能
一括編集、一括削除、一括エクスポート機能を提供
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any
import json

from data import normalize_goals_data


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


def display_bulk_operations():
    """一括操作メイン画面"""
    st.header("🔧 データの一括操作")
    
    st.markdown("""
    複数のデータを一度に編集・削除・エクスポートできます。
    """)
    
    # 操作タイプ選択
    operation_type = st.selectbox(
        "操作を選択",
        ["一括編集", "一括削除", "一括エクスポート"],
        key="bulk_operation_type"
    )
    
    if operation_type == "一括編集":
        display_bulk_edit()
    elif operation_type == "一括削除":
        display_bulk_delete()
    elif operation_type == "一括エクスポート":
        display_bulk_export()


def display_bulk_edit():
    """一括編集機能"""
    st.subheader("✏️ 一括編集")
    
    # 編集対象選択
    target_data = st.selectbox(
        "編集するデータ",
        ["科目名の一括変更", "成績データの一括調整", "学習時間の一括調整"],
        key="bulk_edit_target"
    )
    
    if target_data == "科目名の一括変更":
        bulk_edit_subject_names()
    elif target_data == "成績データの一括調整":
        bulk_edit_grades()
    elif target_data == "学習時間の一括調整":
        bulk_edit_study_time()


def bulk_edit_subject_names():
    """科目名の一括変更"""
    st.markdown("### 科目名の一括変更")
    st.info("複数のデータに記録されている科目名を一度に変更できます。")
    
    if not st.session_state.subjects:
        st.warning("科目が登録されていません")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        old_subject = st.selectbox(
            "変更前の科目名",
            st.session_state.subjects,
            key="bulk_old_subject"
        )
    
    with col2:
        new_subject = st.text_input(
            "変更後の科目名",
            key="bulk_new_subject"
        )
    
    if not new_subject:
        st.warning("変更後の科目名を入力してください")
        return
    
    # 影響範囲のプレビュー
    st.markdown("---")
    st.markdown("#### 📊 影響範囲のプレビュー")
    
    affected_data = {
        "成績データ": len(st.session_state.grades.get(old_subject, [])),
        "進捗データ": len(st.session_state.progress.get(old_subject, [])),
        "リマインダー": 0,
        "目標": 0
    }
    
    # リマインダーのカウント
    try:
        with open('reminders.json', 'r', encoding='utf-8') as f:
            reminders = json.load(f)
            affected_data["リマインダー"] = sum(1 for r in reminders if r.get('subject') == old_subject)
    except:
        pass
    
    # 目標のカウント
    if 'goals' in st.session_state:
        normalized_goals = normalize_goals_data(st.session_state.goals)
        affected_data["目標"] = sum(1 for g in normalized_goals if g.get('subject') == old_subject)
        st.session_state.goals = normalized_goals
    
    col_a, col_b, col_c, col_d = st.columns(4)
    col_a.metric("成績データ", f"{affected_data['成績データ']}件")
    col_b.metric("進捗データ", f"{affected_data['進捗データ']}件")
    col_c.metric("リマインダー", f"{affected_data['リマインダー']}件")
    col_d.metric("目標", f"{affected_data['目標']}件")
    
    total_affected = sum(affected_data.values())
    
    if total_affected == 0:
        st.info("この科目に関連するデータが見つかりません")
        return
    
    st.warning(f"⚠️ 合計 {total_affected} 件のデータが影響を受けます")
    
    # 確認チェックボックス
    confirm = st.checkbox(
        f"「{old_subject}」を「{new_subject}」に変更することを理解しました",
        key="bulk_subject_confirm"
    )
    
    if st.button("🔄 一括変更を実行", type="primary", disabled=not confirm):
        success_count = 0
        
        # 科目リストの変更
        if old_subject in st.session_state.subjects:
            idx = st.session_state.subjects.index(old_subject)
            st.session_state.subjects[idx] = new_subject
            success_count += 1
        
        # 成績データの変更
        if old_subject in st.session_state.grades:
            st.session_state.grades[new_subject] = st.session_state.grades.pop(old_subject)
            success_count += affected_data['成績データ']
        
        # 進捗データの変更
        if old_subject in st.session_state.progress:
            st.session_state.progress[new_subject] = st.session_state.progress.pop(old_subject)
            success_count += affected_data['進捗データ']
        
        # リマインダーの変更
        try:
            with open('reminders.json', 'r', encoding='utf-8') as f:
                reminders = json.load(f)
            
            for reminder in reminders:
                if reminder.get('subject') == old_subject:
                    reminder['subject'] = new_subject
                    success_count += 1
            
            with open('reminders.json', 'w', encoding='utf-8') as f:
                json.dump(reminders, f, ensure_ascii=False, indent=4)
        except:
            pass
        
        # 目標の変更
        if 'goals' in st.session_state:
            goals = normalize_goals_data(st.session_state.goals)
            for goal in goals:
                if goal.get('subject') == old_subject:
                    goal['subject'] = new_subject
                    success_count += 1
            st.session_state.goals = goals
        
        # データ保存
        from data import save_subjects, save_grades, save_progress, save_goals
        save_subjects()
        save_grades()
        save_progress()
        save_goals()
        
        st.success(f"✅ {success_count} 件のデータを正常に変更しました")
        st.rerun()


def bulk_edit_grades():
    """成績データの一括調整"""
    st.markdown("### 成績データの一括調整")
    st.info("選択した条件に合う成績データを一括で調整できます。")
    
    if not st.session_state.grades:
        st.warning("成績データが登録されていません")
        return
    
    # フィルター条件
    col1, col2 = st.columns(2)
    
    with col1:
        filter_subject = st.multiselect(
            "科目で絞り込み",
            st.session_state.subjects,
            default=st.session_state.subjects,
            key="bulk_grade_subject"
        )
    
    with col2:
        filter_type = st.multiselect(
            "タイプで絞り込み",
            ["テスト", "課題", "小テスト", "その他"],
            default=["テスト", "課題", "小テスト", "その他"],
            key="bulk_grade_type"
        )
    
    # 調整方法
    st.markdown("---")
    st.markdown("#### 調整方法")
    
    adjustment_type = st.selectbox(
        "調整タイプ",
        ["点数を加算", "点数を減算", "係数を掛ける", "重みを変更"],
        key="bulk_adjustment_type"
    )
    
    if adjustment_type in ["点数を加算", "点数を減算"]:
        adjustment_value = st.number_input(
            "調整値（点）",
            min_value=0,
            max_value=100,
            value=5,
            key="bulk_adjustment_value"
        )
    elif adjustment_type == "係数を掛ける":
        adjustment_value = st.number_input(
            "係数",
            min_value=0.0,
            max_value=2.0,
            value=1.1,
            step=0.1,
            key="bulk_adjustment_coefficient"
        )
    elif adjustment_type == "重みを変更":
        adjustment_value = st.number_input(
            "新しい重み",
            min_value=0.0,
            max_value=10.0,
            value=1.0,
            step=0.5,
            key="bulk_adjustment_weight"
        )
    
    # 影響を受けるデータのプレビュー
    affected_count = 0
    for subject in filter_subject:
        if subject in st.session_state.grades:
            for grade in st.session_state.grades[subject]:
                if grade.get('type') in filter_type:
                    affected_count += 1
    
    st.info(f"📊 {affected_count} 件のデータが影響を受けます")
    
    if st.button("🔄 一括調整を実行", type="primary"):
        adjusted_count = 0
        
        for subject in filter_subject:
            if subject in st.session_state.grades:
                for grade in st.session_state.grades[subject]:
                    if grade.get('type') in filter_type:
                        if adjustment_type == "点数を加算":
                            grade['grade'] = min(100, grade['grade'] + adjustment_value)
                        elif adjustment_type == "点数を減算":
                            grade['grade'] = max(0, grade['grade'] - adjustment_value)
                        elif adjustment_type == "係数を掛ける":
                            grade['grade'] = min(100, int(grade['grade'] * adjustment_value))
                        elif adjustment_type == "重みを変更":
                            grade['weight'] = adjustment_value
                        
                        adjusted_count += 1
        
        # データ保存
        from data import save_grades
        save_grades()
        
        st.success(f"✅ {adjusted_count} 件のデータを調整しました")
        st.rerun()


def bulk_edit_study_time():
    """学習時間の一括調整"""
    st.markdown("### 学習時間の一括調整")
    st.info("選択した条件に合う学習時間を一括で調整できます。")
    
    st.warning("この機能は進捗トラッキングデータに影響します")
    # 実装は成績データと同様のパターン


def display_bulk_delete():
    """一括削除機能"""
    st.subheader("🗑️ 一括削除")
    
    st.warning("⚠️ 削除されたデータは復元できません。慎重に操作してください。")
    
    # 削除対象選択
    delete_target = st.selectbox(
        "削除するデータ",
        ["期間で絞り込んで削除", "タイプで絞り込んで削除", "特定科目のデータを削除"],
        key="bulk_delete_target"
    )
    
    if delete_target == "期間で絞り込んで削除":
        bulk_delete_by_period()
    elif delete_target == "タイプで絞り込んで削除":
        bulk_delete_by_type()
    elif delete_target == "特定科目のデータを削除":
        bulk_delete_by_subject()


def bulk_delete_by_period():
    """期間で絞り込んで削除"""
    st.markdown("### 期間で絞り込んで削除")
    
    col1, col2 = st.columns(2)
    
    with col1:
        start_date = st.date_input(
            "開始日",
            value=datetime.now() - timedelta(days=365),
            key="bulk_delete_start"
        )
    
    with col2:
        end_date = st.date_input(
            "終了日",
            value=datetime.now() - timedelta(days=180),
            key="bulk_delete_end"
        )
    
    # データタイプ選択
    data_types = st.multiselect(
        "削除するデータタイプ",
        ["成績データ", "進捗データ", "リマインダー"],
        default=["成績データ"],
        key="bulk_delete_data_types"
    )
    
    # 影響範囲のプレビュー
    st.markdown("---")
    st.markdown("#### 📊 削除されるデータのプレビュー")
    
    delete_count = 0
    
    if "成績データ" in data_types:
        for subject, grades in st.session_state.grades.items():
            for grade in grades:
                try:
                    grade_date = parse_date_flexible(grade.get('date', '')).date()
                    if start_date <= grade_date <= end_date:
                        delete_count += 1
                except:
                    pass
    
    st.metric("削除されるデータ数", f"{delete_count}件")
    
    if delete_count == 0:
        st.info("指定された期間に該当するデータが見つかりません")
        return
    
    # 確認
    confirm_text = st.text_input(
        f"削除を実行するには「削除する」と入力してください",
        key="bulk_delete_confirm"
    )
    
    if st.button("🗑️ 一括削除を実行", type="secondary", disabled=(confirm_text != "削除する")):
        deleted = 0
        
        if "成績データ" in data_types:
            for subject in list(st.session_state.grades.keys()):
                new_grades = []
                for grade in st.session_state.grades[subject]:
                    try:
                        grade_date = parse_date_flexible(grade.get('date', '')).date()
                        if not (start_date <= grade_date <= end_date):
                            new_grades.append(grade)
                        else:
                            deleted += 1
                    except:
                        new_grades.append(grade)
                
                st.session_state.grades[subject] = new_grades
        
        # データ保存
        from data import save_grades
        save_grades()
        
        st.success(f"✅ {deleted} 件のデータを削除しました")
        st.rerun()


def bulk_delete_by_type():
    """タイプで絞り込んで削除"""
    st.markdown("### タイプで絞り込んで削除")
    
    delete_types = st.multiselect(
        "削除するタイプ",
        ["テスト", "課題", "小テスト", "その他"],
        key="bulk_delete_types"
    )
    
    if not delete_types:
        st.info("削除するタイプを選択してください")
        return
    
    # 影響範囲
    delete_count = 0
    for subject, grades in st.session_state.grades.items():
        for grade in grades:
            if grade.get('type') in delete_types:
                delete_count += 1
    
    st.metric("削除されるデータ数", f"{delete_count}件")
    
    # 削除処理は期間削除と同様のパターン


def bulk_delete_by_subject():
    """特定科目のデータを削除"""
    st.markdown("### 特定科目のすべてのデータを削除")
    
    if not st.session_state.subjects:
        st.warning("科目が登録されていません")
        return
    
    delete_subject = st.selectbox(
        "削除する科目",
        st.session_state.subjects,
        key="bulk_delete_subject"
    )
    
    # 影響範囲
    affected = {
        "成績": len(st.session_state.grades.get(delete_subject, [])),
        "進捗": len(st.session_state.progress.get(delete_subject, []))
    }
    
    st.warning(f"⚠️ 科目「{delete_subject}」に関連する全データが削除されます")
    st.metric("削除される成績データ", f"{affected['成績']}件")
    st.metric("削除される進捗データ", f"{affected['進捗']}件")


def display_bulk_export():
    """一括エクスポート機能"""
    st.subheader("📤 一括エクスポート")
    
    st.info("選択した条件に合うデータをCSV形式でエクスポートできます")
    
    # エクスポート条件
    export_type = st.selectbox(
        "エクスポートタイプ",
        ["特定期間のデータ", "特定科目のデータ", "すべてのデータ"],
        key="bulk_export_type"
    )
    
    if export_type == "特定期間のデータ":
        bulk_export_by_period()
    elif export_type == "特定科目のデータ":
        bulk_export_by_subject()
    elif export_type == "すべてのデータ":
        bulk_export_all()


def bulk_export_by_period():
    """特定期間のデータをエクスポート"""
    st.markdown("### 特定期間のデータをエクスポート")
    
    col1, col2 = st.columns(2)
    
    with col1:
        start_date = st.date_input("開始日", key="export_start")
    
    with col2:
        end_date = st.date_input("終了日", key="export_end")
    
    # エクスポートするデータタイプ
    export_data_types = st.multiselect(
        "エクスポートするデータ",
        ["成績データ", "進捗データ"],
        default=["成績データ"],
        key="export_data_types"
    )
    
    if st.button("📥 CSVを生成", type="primary"):
        if "成績データ" in export_data_types:
            # 成績データの抽出
            export_grades = []
            for subject, grades in st.session_state.grades.items():
                for grade in grades:
                    try:
                        grade_date = parse_date_flexible(grade.get('date', '')).date()
                        if start_date <= grade_date <= end_date:
                            export_grades.append({
                                '科目': subject,
                                '日付': grade.get('date'),
                                'タイプ': grade.get('type'),
                                '点数': grade.get('grade'),
                                '重み': grade.get('weight'),
                                'コメント': grade.get('comment', '')
                            })
                    except:
                        pass
            
            if export_grades:
                df = pd.DataFrame(export_grades)
                csv = df.to_csv(index=False, encoding='utf-8-sig')
                
                st.download_button(
                    label="📥 成績データをダウンロード",
                    data=csv,
                    file_name=f"grades_{start_date}_{end_date}.csv",
                    mime="text/csv"
                )
                
                st.success(f"✅ {len(export_grades)} 件のデータを抽出しました")
            else:
                st.warning("該当するデータが見つかりませんでした")


def bulk_export_by_subject():
    """特定科目のデータをエクスポート"""
    st.markdown("### 特定科目のデータをエクスポート")
    
    if not st.session_state.subjects:
        st.warning("科目が登録されていません")
        return
    
    export_subjects = st.multiselect(
        "エクスポートする科目",
        st.session_state.subjects,
        key="export_subjects"
    )
    
    if st.button("📥 CSVを生成", type="primary"):
        export_data = []
        for subject in export_subjects:
            if subject in st.session_state.grades:
                for grade in st.session_state.grades[subject]:
                    export_data.append({
                        '科目': subject,
                        '日付': grade.get('date'),
                        'タイプ': grade.get('type'),
                        '点数': grade.get('grade'),
                        '重み': grade.get('weight'),
                        'コメント': grade.get('comment', '')
                    })
        
        if export_data:
            df = pd.DataFrame(export_data)
            csv = df.to_csv(index=False, encoding='utf-8-sig')
            
            st.download_button(
                label="📥 データをダウンロード",
                data=csv,
                file_name=f"grades_{'_'.join(export_subjects)}.csv",
                mime="text/csv"
            )
            
            st.success(f"✅ {len(export_data)} 件のデータを抽出しました")


def bulk_export_all():
    """すべてのデータをエクスポート"""
    st.markdown("### すべてのデータをエクスポート")
    
    if st.button("📥 すべてのデータをCSVで生成", type="primary"):
        all_data = []
        for subject, grades in st.session_state.grades.items():
            for grade in grades:
                all_data.append({
                    '科目': subject,
                    '日付': grade.get('date'),
                    'タイプ': grade.get('type'),
                    '点数': grade.get('grade'),
                    '重み': grade.get('weight'),
                    'コメント': grade.get('comment', '')
                })
        
        if all_data:
            df = pd.DataFrame(all_data)
            csv = df.to_csv(index=False, encoding='utf-8-sig')
            
            st.download_button(
                label="📥 全データをダウンロード",
                data=csv,
                file_name=f"all_grades_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
            
            st.success(f"✅ {len(all_data)} 件のデータを抽出しました")
        else:
            st.warning("エクスポートするデータがありません")
