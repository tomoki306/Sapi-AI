# enhanced_visualization.py
"""
グラフ・可視化の強化
インタラクティブグラフ、複数科目比較、カスタマイズ可能なダッシュボード
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from typing import List, Dict, Any


def display_enhanced_visualization():
    """強化された可視化メイン画面"""
    st.header("📊 高度なデータ可視化")
    
    st.markdown("""
    インタラクティブなグラフで学習データを多角的に分析できます。
    """)
    
    # タブで機能を分ける
    tab1, tab2, tab3, tab4 = st.tabs([
        "📈 複数科目比較",
        "📊 時系列比較",
        "🎯 目標達成分析",
        "🎨 カスタムダッシュボード"
    ])
    
    with tab1:
        display_multi_subject_comparison()
    
    with tab2:
        display_time_series_comparison()
    
    with tab3:
        display_goal_achievement_analysis()
    
    with tab4:
        display_custom_dashboard()


def display_multi_subject_comparison():
    """複数科目の成績比較"""
    st.subheader("📈 複数科目の成績比較")
    
    if not st.session_state.subjects:
        st.warning("科目が登録されていません")
        return
    
    # 科目選択
    selected_subjects = st.multiselect(
        "比較する科目を選択（最大5科目）",
        st.session_state.subjects,
        default=st.session_state.subjects[:min(3, len(st.session_state.subjects))],
        key="compare_subjects"
    )
    
    if len(selected_subjects) == 0:
        st.info("比較する科目を選択してください")
        return
    
    if len(selected_subjects) > 5:
        st.warning("最大5科目まで選択できます")
        selected_subjects = selected_subjects[:5]
    
    # グラフタイプ選択
    chart_type = st.selectbox(
        "グラフタイプ",
        ["折れ線グラフ（推移）", "棒グラフ（平均比較）", "レーダーチャート", "箱ひげ図（分布）"],
        key="compare_chart_type"
    )
    
    st.markdown("---")
    
    if chart_type == "折れ線グラフ（推移）":
        display_multi_line_chart(selected_subjects)
    elif chart_type == "棒グラフ（平均比較）":
        display_bar_comparison(selected_subjects)
    elif chart_type == "レーダーチャート":
        display_radar_chart(selected_subjects)
    elif chart_type == "箱ひげ図（分布）":
        display_box_plot(selected_subjects)


def display_multi_line_chart(subjects: List[str]):
    """複数科目の折れ線グラフ"""
    st.markdown("### 成績推移の比較")
    
    fig = go.Figure()
    
    for subject in subjects:
        if subject not in st.session_state.grades or not st.session_state.grades[subject]:
            continue
        
        df = pd.DataFrame(st.session_state.grades[subject])
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')

        if 'type' not in df.columns:
            df['type'] = '不明'
        if 'weight' not in df.columns:
            df['weight'] = 1

        df['order_in_day'] = df.groupby(df['date'].dt.date).cumcount()
        df['date_adjusted'] = df['date'] + pd.to_timedelta(df['order_in_day'] * 5, unit='m')

        customdata = np.stack([
            df['date'].dt.strftime('%Y-%m-%d'),
            df['type'].fillna('不明'),
            df['weight'].fillna(1)
        ], axis=-1)
        
        fig.add_trace(go.Scatter(
            x=df['date_adjusted'],
            y=df['grade'],
            mode='lines+markers',
            name=subject,
            hovertemplate=(
                '<b>%{fullData.name}</b><br>' +
                '日付: %{customdata[0]}<br>' +
                '点数: %{y}点<br>' +
                'タイプ: %{customdata[1]}<br>' +
                '重み: %{customdata[2]}<extra></extra>'
            ),
            customdata=customdata
        ))
    
    fig.update_layout(
        title='科目別成績推移',
        xaxis_title='日付',
        yaxis_title='成績（点）',
        hovermode='x unified',
        height=500,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    fig.update_xaxes(tickformat='%Y-%m-%d')
    
    # インタラクティブ機能の説明
    with st.expander("💡 グラフの使い方"):
        st.markdown("""
        - **ズーム**: ドラッグして範囲を選択
        - **パン**: Shiftキーを押しながらドラッグ
        - **リセット**: 右上のホームアイコンをクリック
        - **データポイント**: カーソルを合わせると詳細情報を表示
        - **凡例**: クリックで科目の表示/非表示を切り替え
        """)
    
    st.plotly_chart(fig, use_container_width=True)
    
    # 統計サマリー
    st.markdown("---")
    st.markdown("### 📊 統計サマリー")
    
    summary_data = []
    for subject in subjects:
        if subject not in st.session_state.grades or not st.session_state.grades[subject]:
            continue
        
        grades = [g['grade'] for g in st.session_state.grades[subject]]
        weights = [g.get('weight', 1) for g in st.session_state.grades[subject]]
        
        weighted_avg = sum(g*w for g, w in zip(grades, weights)) / sum(weights)
        
        summary_data.append({
            "科目": subject,
            "データ数": len(grades),
            "平均点": f"{sum(grades)/len(grades):.1f}",
            "加重平均": f"{weighted_avg:.1f}",
            "最高点": max(grades),
            "最低点": min(grades),
            "標準偏差": f"{pd.Series(grades).std():.1f}"
        })
    
    summary_df = pd.DataFrame(summary_data)
    st.dataframe(summary_df, use_container_width=True, hide_index=True)


def display_bar_comparison(subjects: List[str]):
    """棒グラフで科目別平均を比較"""
    st.markdown("### 科目別平均点の比較")
    
    comparison_data = []
    
    for subject in subjects:
        if subject not in st.session_state.grades or not st.session_state.grades[subject]:
            continue
        
        grades = [g['grade'] for g in st.session_state.grades[subject]]
        weights = [g.get('weight', 1) for g in st.session_state.grades[subject]]
        
        simple_avg = sum(grades) / len(grades)
        weighted_avg = sum(g*w for g, w in zip(grades, weights)) / sum(weights)
        
        comparison_data.append({
            "科目": subject,
            "単純平均": simple_avg,
            "加重平均": weighted_avg
        })
    
    df = pd.DataFrame(comparison_data)
    
    # グラフ作成
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        name='単純平均',
        x=df['科目'],
        y=df['単純平均'],
        text=df['単純平均'].apply(lambda x: f"{x:.1f}"),
        textposition='outside',
        marker_color='lightblue'
    ))
    
    fig.add_trace(go.Bar(
        name='加重平均',
        x=df['科目'],
        y=df['加重平均'],
        text=df['加重平均'].apply(lambda x: f"{x:.1f}"),
        textposition='outside',
        marker_color='darkblue'
    ))
    
    fig.update_layout(
        title='科目別平均点比較',
        xaxis_title='科目',
        yaxis_title='平均点（点）',
        barmode='group',
        height=500,
        hovermode='x unified'
    )
    
    st.plotly_chart(fig, use_container_width=True)


def display_radar_chart(subjects: List[str]):
    """レーダーチャートで科目を比較"""
    st.markdown("### レーダーチャート")
    
    if len(subjects) > 6:
        st.warning("レーダーチャートは最大6科目まで表示できます")
        subjects = subjects[:6]
    
    # データ準備
    categories = []
    values = []
    
    for subject in subjects:
        if subject not in st.session_state.grades or not st.session_state.grades[subject]:
            continue
        
        grades = [g['grade'] for g in st.session_state.grades[subject]]
        avg = sum(grades) / len(grades)
        
        categories.append(subject)
        values.append(avg)
    
    # レーダーチャート作成
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself',
        name='平均点',
        line_color='blue',
        fillcolor='rgba(0, 0, 255, 0.3)'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )
        ),
        title='科目別能力レーダーチャート',
        height=500
    )
    
    st.plotly_chart(fig, use_container_width=True)


def display_box_plot(subjects: List[str]):
    """箱ひげ図で成績分布を比較"""
    st.markdown("### 成績分布の比較（箱ひげ図）")
    
    fig = go.Figure()
    
    for subject in subjects:
        if subject not in st.session_state.grades or not st.session_state.grades[subject]:
            continue
        
        grades = [g['grade'] for g in st.session_state.grades[subject]]
        
        fig.add_trace(go.Box(
            y=grades,
            name=subject,
            boxmean='sd'  # 平均と標準偏差を表示
        ))
    
    fig.update_layout(
        title='科目別成績分布',
        yaxis_title='成績（点）',
        height=500,
        showlegend=True
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    st.info("""
    **箱ひげ図の見方:**
    - 箱: 第1四分位数（25%）〜第3四分位数（75%）
    - 箱の中の線: 中央値
    - ひげ: 最小値〜最大値（外れ値を除く）
    - 点: 外れ値
    - ×印: 平均値
    """)


def display_time_series_comparison():
    """時系列比較（今月vs先月など）"""
    st.subheader("📊 時系列比較")
    
    if not st.session_state.subjects:
        st.warning("科目が登録されていません")
        return
    
    # 科目選択
    subject = st.selectbox(
        "科目を選択",
        st.session_state.subjects,
        key="timeseries_subject"
    )
    
    if subject not in st.session_state.grades or not st.session_state.grades[subject]:
        st.info("この科目の成績データがありません")
        return
    
    # 比較期間選択
    comparison_type = st.selectbox(
        "比較タイプ",
        ["今月 vs 先月", "今週 vs 先週", "最近3ヶ月 vs 過去3ヶ月", "カスタム期間"],
        key="comparison_type"
    )
    
    st.markdown("---")
    
    # 期間の計算
    today = datetime.now()
    
    if comparison_type == "今月 vs 先月":
        period1_start = today.replace(day=1)
        period1_end = today
        period2_start = (period1_start - timedelta(days=1)).replace(day=1)
        period2_end = period1_start - timedelta(days=1)
        period1_label = "今月"
        period2_label = "先月"
    
    elif comparison_type == "今週 vs 先週":
        period1_start = today - timedelta(days=today.weekday())
        period1_end = today
        period2_start = period1_start - timedelta(weeks=1)
        period2_end = period1_start - timedelta(days=1)
        period1_label = "今週"
        period2_label = "先週"
    
    elif comparison_type == "最近3ヶ月 vs 過去3ヶ月":
        period1_end = today
        period1_start = today - timedelta(days=90)
        period2_end = period1_start - timedelta(days=1)
        period2_start = period2_end - timedelta(days=90)
        period1_label = "最近3ヶ月"
        period2_label = "過去3ヶ月"
    
    else:  # カスタム期間
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### 期間1")
            period1_start = st.date_input("開始日", key="period1_start")
            period1_end = st.date_input("終了日", key="period1_end")
            period1_label = "期間1"
        
        with col2:
            st.markdown("#### 期間2")
            period2_start = st.date_input("開始日", key="period2_start")
            period2_end = st.date_input("終了日", key="period2_end")
            period2_label = "期間2"
        
        period1_start = datetime.combine(period1_start, datetime.min.time())
        period1_end = datetime.combine(period1_end, datetime.max.time())
        period2_start = datetime.combine(period2_start, datetime.min.time())
        period2_end = datetime.combine(period2_end, datetime.max.time())
    
    # データの抽出と比較
    df = pd.DataFrame(st.session_state.grades[subject])
    df['date'] = pd.to_datetime(df['date'])
    
    period1_data = df[(df['date'] >= period1_start) & (df['date'] <= period1_end)]
    period2_data = df[(df['date'] >= period2_start) & (df['date'] <= period2_end)]
    
    # 統計計算
    if len(period1_data) > 0 and len(period2_data) > 0:
        period1_avg = period1_data['grade'].mean()
        period2_avg = period2_data['grade'].mean()
        diff = period1_avg - period2_avg
        
        # メトリクス表示
        col_a, col_b, col_c = st.columns(3)
        col_a.metric(period1_label, f"{period1_avg:.1f}点", f"{diff:+.1f}点")
        col_b.metric(period2_label, f"{period2_avg:.1f}点")
        col_c.metric("データ数比較", f"{len(period1_data)}件 vs {len(period2_data)}件")
        
        # 比較グラフ
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=(period1_label, period2_label)
        )
        
        fig.add_trace(
            go.Box(y=period1_data['grade'], name=period1_label, marker_color='lightblue'),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Box(y=period2_data['grade'], name=period2_label, marker_color='lightcoral'),
            row=1, col=2
        )
        
        fig.update_layout(
            title=f'{subject} の成績比較',
            showlegend=False,
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    else:
        st.warning("比較するデータが不足しています")


def display_goal_achievement_analysis():
    """目標達成分析"""
    st.subheader("🎯 目標達成分析")
    
    st.info("目標値との比較を可視化します")
    
    if not st.session_state.subjects:
        st.warning("科目が登録されていません")
        return
    
    # 科目選択
    subject = st.selectbox(
        "科目を選択",
        st.session_state.subjects,
        key="goal_analysis_subject"
    )
    
    if subject not in st.session_state.grades or not st.session_state.grades[subject]:
        st.info("この科目の成績データがありません")
        return
    
    # 目標値設定
    goal_value = st.number_input(
        "目標点数",
        min_value=0,
        max_value=100,
        value=80,
        key="goal_value"
    )
    
    # データ準備
    df = pd.DataFrame(st.session_state.grades[subject])
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')
    
    # グラフ作成
    fig = go.Figure()
    
    # 実際の成績
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['grade'],
        mode='lines+markers',
        name='実際の成績',
        line=dict(color='blue', width=3),
        marker=dict(size=10)
    ))
    
    # 目標ライン
    fig.add_hline(
        y=goal_value,
        line_dash="dash",
        line_color="red",
        line_width=2,
        annotation_text=f"目標: {goal_value}点",
        annotation_position="right"
    )
    
    # 目標達成領域を塗りつぶし
    fig.add_hrect(
        y0=goal_value,
        y1=100,
        fillcolor="green",
        opacity=0.1,
        line_width=0,
        annotation_text="目標達成領域",
        annotation_position="top right"
    )
    
    fig.update_layout(
        title=f'{subject} の目標達成状況',
        xaxis_title='日付',
        yaxis_title='成績（点）',
        height=500,
        hovermode='x unified'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # 達成率計算
    above_goal = len(df[df['grade'] >= goal_value])
    total = len(df)
    achievement_rate = (above_goal / total) * 100 if total > 0 else 0
    
    col1, col2, col3 = st.columns(3)
    col1.metric("目標達成回数", f"{above_goal}回")
    col2.metric("総テスト数", f"{total}回")
    col3.metric("達成率", f"{achievement_rate:.1f}%")


def display_custom_dashboard():
    """カスタマイズ可能なダッシュボード"""
    st.subheader("🎨 カスタムダッシュボード")
    
    st.info("表示する情報をカスタマイズできます")
    
    # ウィジェット選択
    st.markdown("### ダッシュボードの構成")
    
    widgets = st.multiselect(
        "表示するウィジェットを選択",
        [
            "総合統計",
            "最近の成績推移",
            "科目別平均",
            "学習時間サマリー",
            "目標達成状況"
        ],
        default=["総合統計", "最近の成績推移", "科目別平均"],
        key="dashboard_widgets"
    )
    
    st.markdown("---")
    
    # ウィジェットの表示
    if "総合統計" in widgets:
        display_overall_stats()
    
    if "最近の成績推移" in widgets:
        display_recent_trends()
    
    if "科目別平均" in widgets:
        display_subject_averages()
    
    if "学習時間サマリー" in widgets:
        display_study_time_summary()
    
    if "目標達成状況" in widgets:
        display_goal_status()


def display_overall_stats():
    """総合統計ウィジェット"""
    st.markdown("### 📊 総合統計")
    
    total_records = sum(len(grades) for grades in st.session_state.grades.values())
    total_subjects = len(st.session_state.subjects)
    
    if total_records > 0:
        all_grades = [g['grade'] for grades in st.session_state.grades.values() for g in grades]
        overall_avg = sum(all_grades) / len(all_grades)
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("総成績記録数", f"{total_records}件")
        col2.metric("登録科目数", f"{total_subjects}科目")
        col3.metric("全体平均", f"{overall_avg:.1f}点")
        col4.metric("最高点", f"{max(all_grades)}点")


def display_recent_trends():
    """最近の成績推移ウィジェット"""
    st.markdown("### 📈 最近の成績推移（全科目）")
    
    # 直近30日のデータを集計
    cutoff_date = datetime.now() - timedelta(days=30)
    
    fig = go.Figure()
    
    for subject in st.session_state.subjects:
        if subject not in st.session_state.grades:
            continue
        
        df = pd.DataFrame(st.session_state.grades[subject])
        df['date'] = pd.to_datetime(df['date'])
        recent_df = df[df['date'] >= cutoff_date].sort_values('date')
        
        if len(recent_df) > 0:
            fig.add_trace(go.Scatter(
                x=recent_df['date'],
                y=recent_df['grade'],
                mode='lines+markers',
                name=subject
            ))
    
    fig.update_layout(
        title='過去30日間の成績推移',
        height=400,
        hovermode='x unified'
    )
    
    st.plotly_chart(fig, use_container_width=True)


def display_subject_averages():
    """科目別平均ウィジェット"""
    st.markdown("### 📊 科目別平均点")
    
    subject_avgs = []
    for subject in st.session_state.subjects:
        if subject in st.session_state.grades and st.session_state.grades[subject]:
            grades = [g['grade'] for g in st.session_state.grades[subject]]
            avg = sum(grades) / len(grades)
            subject_avgs.append({"科目": subject, "平均点": avg})
    
    if subject_avgs:
        df = pd.DataFrame(subject_avgs)
        fig = px.bar(df, x='科目', y='平均点', text='平均点')
        fig.update_traces(texttemplate='%{text:.1f}', textposition='outside')
        fig.update_layout(height=350)
        st.plotly_chart(fig, use_container_width=True)


def display_study_time_summary():
    """学習時間サマリーウィジェット"""
    st.markdown("### ⏰ 学習時間サマリー")
    
    # 進捗データから学習時間を集計
    if 'progress' not in st.session_state or not st.session_state.progress:
        st.info("進捗データがありません")
        return
    
    total_time = 0
    for subject_progress in st.session_state.progress.values():
        for record in subject_progress:
            total_time += record.get('time', 0)
    
    col1, col2 = st.columns(2)
    col1.metric("総学習時間", f"{total_time:.1f}時間")
    col2.metric("平均学習時間/日", f"{total_time/max(1, len(st.session_state.progress)):.1f}時間")


def display_goal_status():
    """目標達成状況ウィジェット"""
    st.markdown("### 🎯 目標達成状況")
    
    if 'goals' not in st.session_state or not st.session_state.goals:
        st.info("目標が設定されていません")
        return
    
    achieved = sum(1 for g in st.session_state.goals if g.get('achieved', False))
    total = len(st.session_state.goals)
    
    col1, col2, col3 = st.columns(3)
    col1.metric("総目標数", f"{total}件")
    col2.metric("達成数", f"{achieved}件")
    col3.metric("達成率", f"{(achieved/total*100):.1f}%" if total > 0 else "0%")
