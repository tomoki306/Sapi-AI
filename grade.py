# grade.py

import streamlit as st
import pandas as pd  # pandasのインポート
import plotly.express as px  # plotly.expressのインポート
from data import record_grade
from datetime import datetime
from grade_filters import (
    apply_all_filters, convert_grades_to_dataframe, 
    get_filter_statistics
)
from validators import validate_grade, validate_subject_name, ValidationError
from logger import log_user_action, log_error
from pagination import paginate_data, display_pagination_controls  # ページネーション追加

def record_grades():
    # 成績記録の処理
    st.header("成績記録")
    
    # 科目が存在するか確認
    if 'subjects' not in st.session_state or not st.session_state.subjects:
        st.error("まず科目を登録してください")
        return
    
    subject = st.selectbox("科目を選択", st.session_state.subjects)
    grade_type = st.selectbox("成績タイプ", ["テスト", "課題"])
    grade = st.number_input("成績 (0-100)", min_value=0, max_value=100)
    weight_type = st.selectbox("重みのタイプ", ["期末テスト", "中間テスト", "小テスト"])
    weight_dict = {"期末テスト": 15.0, "中間テスト": 10.0, "小テスト": 1.0}
    weight = weight_dict[weight_type]
    comment = st.text_area("コメント")
    
    if st.button("成績を記録"):
        if record_grade(subject, grade_type, grade, weight, comment):
            # ここでのデータ追加は不要
            st.success("成績が記録されました")
    
    # 記録済み成績の表示
    st.subheader("記録済み成績")
    if 'grades' in st.session_state and st.session_state.grades:
        for subj, grades in st.session_state.grades.items():
            st.markdown(f"<h2>{subj}</h2>", unsafe_allow_html=True)
            df = pd.DataFrame(grades)
            if not df.empty:
                # 欠損している列を補完する
                for col in ['weight', 'comment']:
                    if col not in df.columns:
                        df[col] = ''
                
                # テストと課題のデータを分離
                test_data = df[df['type'] == 'テスト']
                assignment_data = df[df['type'] == '課題']
                
                # インデックスを追加して記録順序を表現
                test_data_reset = test_data.reset_index()
                assignment_data_reset = assignment_data.reset_index()
                
                if not test_data.empty:
                    # テスト成績のグラフ
                    test_fig = px.line(
                        test_data_reset,
                        x=range(1, len(test_data) + 1),
                        y='grade',
                        title=f"{subj}のテスト成績推移",
                        markers=True,
                        color_discrete_sequence=['#FF6B6B']
                    )
                    
                    test_fig.update_layout(
                        xaxis=dict(title="記録順序", dtick=1),
                        yaxis=dict(title="成績", range=[0, 100]),
                        height=400
                    )
                    
                    test_avg = test_data['grade'].mean()
                    
                    st.subheader("📊 テスト成績")
                    st.plotly_chart(test_fig)
                    st.metric(label="テスト平均成績", value=f"{test_avg:.1f}")
                
                if not assignment_data.empty:
                    # 課題成績のグラフ
                    assignment_fig = px.line(
                        assignment_data_reset,
                        x=range(1, len(assignment_data) + 1),
                        y='grade',
                        title=f"{subj}の課題成績推移",
                        markers=True,
                        color_discrete_sequence=['#4ECDC4']
                    )
                    
                    assignment_fig.update_layout(
                        xaxis=dict(title="記録順序", dtick=1),
                        yaxis=dict(title="成績", range=[0, 100]),
                        height=400
                    )
                    
                    assignment_avg = assignment_data['grade'].mean()
                    
                    st.subheader("📝 課題成績")
                    st.plotly_chart(assignment_fig)
                    st.metric(label="課題平均成績", value=f"{assignment_avg:.1f}")
                
                # 全体の平均成績
                avg_grade = df['grade'].mean()
                st.subheader("📈 全体成績")
                st.metric(label="全体平均成績", value=f"{avg_grade:.1f}")
                
                # 成績の詳細テーブル（ページネーション付き）
                df_renamed = df.rename(columns={
                    'date': '日付',
                    'type': '種類',
                    'grade': '成績', 
                    'weight': '重み',
                    'comment': 'コメント'
                })
                
                # データ量が多い場合はページネーション
                display_columns = ['日付', '種類', '成績', '重み', 'コメント']
                table_data = df_renamed[display_columns].to_dict('records')
                
                if len(table_data) > 20:
                    st.subheader("📋 成績詳細テーブル（ページネーション）")
                    page_data, page_info = paginate_data(
                        table_data, 
                        page_size=20,
                        session_key=f"grade_table_{subj}"
                    )
                    st.dataframe(pd.DataFrame(page_data))
                    display_pagination_controls(page_info, key_prefix=f"grade_table_{subj}")
                else:
                    st.write(df_renamed[display_columns])
    else:
        st.write("記録済みの成績はありません。")


def display_grade_search():
    """成績記録のフィルタリング・検索画面"""
    st.header("🔍 成績記録の検索・フィルタリング")
    
    # 成績データが存在するか確認
    if 'grades' not in st.session_state or not st.session_state.grades:
        st.warning("成績データがありません。まず成績を記録してください。")
        return
    
    # フィルタ設定エリア
    with st.expander("🔧 フィルタ設定", expanded=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # 期間フィルタ
            period = st.selectbox(
                "期間",
                ["全期間", "今週", "今月", "3ヶ月", "6ヶ月", "1年", "カスタム"],
                index=0
            )
            
            # カスタム期間の設定
            custom_start = None
            custom_end = None
            if period == "カスタム":
                custom_start = st.date_input("開始日").strftime("%Y-%m-%d")
                custom_end = st.date_input("終了日").strftime("%Y-%m-%d")
        
        with col2:
            # 科目フィルタ
            all_subjects = ["すべて"] + st.session_state.subjects
            selected_subjects = st.multiselect(
                "科目",
                all_subjects,
                default=["すべて"]
            )
            
            # タイプフィルタ
            grade_types = st.multiselect(
                "タイプ",
                ["すべて", "テスト", "課題"],
                default=["すべて"]
            )
        
        with col3:
            # 点数範囲フィルタ
            min_score = st.number_input("最小点数", min_value=0, max_value=100, value=0)
            max_score = st.number_input("最大点数", min_value=0, max_value=100, value=100)
            
            # ソート設定
            sort_by = st.selectbox(
                "並び替え",
                ["日付（新しい順）", "日付（古い順）", "点数（高い順）", "点数（低い順）"],
                index=0
            )
    
    # キーワード検索
    keyword = st.text_input("🔍 キーワード検索（コメント内を検索）", "")
    
    # フィルタ適用ボタン
    if st.button("フィルタを適用", type="primary"):
        # ソート設定の解析
        if "日付" in sort_by:
            sort_key = "date"
            ascending = "古い順" in sort_by
        elif "点数" in sort_by:
            sort_key = "grade"
            ascending = "低い順" in sort_by
        else:
            sort_key = "date"
            ascending = False
        
        # フィルタ設定を辞書にまとめる
        filters = {
            'period': period,
            'custom_start': custom_start,
            'custom_end': custom_end,
            'subjects': selected_subjects,
            'types': grade_types,
            'min_score': int(min_score),
            'max_score': int(max_score),
            'keyword': keyword,
            'sort_by': sort_key,
            'ascending': ascending
        }
        
        # フィルタを適用
        filtered_grades = apply_all_filters(st.session_state.grades, filters)
        
        # 統計情報の取得
        stats = get_filter_statistics(filtered_grades)
        
        # 統計情報の表示
        st.subheader("📊 検索結果の統計")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("総記録数", stats['total_records'])
        
        with col2:
            st.metric("科目数", stats['subjects_count'])
        
        with col3:
            st.metric("平均点", f"{stats['average_score']:.1f}")
        
        with col4:
            st.metric("最高点 / 最低点", f"{stats['max_score']} / {stats['min_score']}")
        
        col5, col6 = st.columns(2)
        
        with col5:
            st.metric("テスト数", stats['test_count'])
        
        with col6:
            st.metric("課題数", stats['assignment_count'])
        
        # 検索結果の表示
        st.subheader("📋 検索結果")
        
        if filtered_grades:
            # DataFrameに変換
            df = convert_grades_to_dataframe(filtered_grades)
            
            # 表示用に列名を日本語化
            df_display = df.copy()
            
            # データテーブルで表示
            st.dataframe(
                df_display,
                use_container_width=True,
                hide_index=True
            )
            
            # グラフ表示オプション
            if st.checkbox("グラフで表示"):
                chart_type = st.radio("グラフの種類", ["折れ線グラフ", "棒グラフ", "散布図"])
                
                if chart_type == "折れ線グラフ":
                    fig = px.line(
                        df,
                        x='日付',
                        y='点数',
                        color='科目',
                        title="成績推移",
                        markers=True
                    )
                elif chart_type == "棒グラフ":
                    fig = px.bar(
                        df,
                        x='科目',
                        y='点数',
                        color='タイプ',
                        title="科目別平均成績",
                        barmode='group'
                    )
                else:  # 散布図
                    fig = px.scatter(
                        df,
                        x='日付',
                        y='点数',
                        color='科目',
                        size='重み',
                        title="成績分布",
                        hover_data=['コメント']
                    )
                
                fig.update_layout(height=500)
                st.plotly_chart(fig, use_container_width=True)
            
            # CSVダウンロードボタン
            csv = df.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="📥 CSVでダウンロード",
                data=csv,
                file_name=f"成績データ_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        else:
            st.info("検索条件に一致する成績データが見つかりませんでした。")
    else:
        st.info("フィルタ条件を設定して「フィルタを適用」ボタンを押してください。")