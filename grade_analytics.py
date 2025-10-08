# grade_analytics.py
# 成績分析機能の拡張（統計分析・可視化）

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
try:
    from scipy import stats
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    st.warning("⚠️ scipy未インストール。トレンド分析を使用するには `pip install scipy` を実行してください")

def display_advanced_analytics():
    """高度な成績分析画面"""
    st.header("📊 高度な成績分析")
    
    if 'grades' not in st.session_state or not st.session_state.grades:
        st.warning("成績データがありません")
        return
    
    # タブで分析を分ける
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "統計サマリー",
        "トレンド分析",
        "成績分布",
        "テストvs課題比較",
        "全科目比較"
    ])
    
    with tab1:
        display_statistics_summary()
    
    with tab2:
        display_trend_analysis()
    
    with tab3:
        display_grade_distribution()
    
    with tab4:
        display_test_vs_assignment()
    
    with tab5:
        display_all_subjects_comparison()

# =============== 統計サマリー ===============

def display_statistics_summary():
    """統計指標の表示"""
    st.subheader("📈 統計サマリー")
    
    subject = st.selectbox("科目を選択", list(st.session_state.grades.keys()), key="stats_subject")
    
    if subject not in st.session_state.grades or not st.session_state.grades[subject]:
        st.info("この科目の成績データはありません")
        return
    
    df = pd.DataFrame(st.session_state.grades[subject])
    
    # 統計指標の計算
    stats_data = {
        "指標": ["平均点", "中央値", "最高点", "最低点", "標準偏差", "データ数"],
        "全体": [
            f"{df['grade'].mean():.2f}",
            f"{df['grade'].median():.2f}",
            f"{df['grade'].max():.2f}",
            f"{df['grade'].min():.2f}",
            f"{df['grade'].std():.2f}",
            f"{len(df)}"
        ]
    }
    
    # タイプ別統計
    for grade_type in df['type'].unique():
        type_df = df[df['type'] == grade_type]
        stats_data[grade_type] = [
            f"{type_df['grade'].mean():.2f}",
            f"{type_df['grade'].median():.2f}",
            f"{type_df['grade'].max():.2f}",
            f"{type_df['grade'].min():.2f}",
            f"{type_df['grade'].std():.2f}",
            f"{len(type_df)}"
        ]
    
    stats_df = pd.DataFrame(stats_data)
    st.dataframe(stats_df, use_container_width=True)
    
    # メトリクス表示
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("平均点", f"{df['grade'].mean():.1f}点")
    with col2:
        st.metric("中央値", f"{df['grade'].median():.1f}点")
    with col3:
        st.metric("最高点", f"{df['grade'].max():.0f}点")
    with col4:
        st.metric("標準偏差", f"{df['grade'].std():.2f}")
    
    # 加重平均の計算
    if 'weight' in df.columns:
        weighted_avg = (df['grade'] * df['weight']).sum() / df['weight'].sum()
        st.metric("加重平均", f"{weighted_avg:.2f}点", help="重み付けを考慮した平均点")

# =============== トレンド分析 ===============

def display_trend_analysis():
    """線形回帰による成績トレンド分析"""
    st.subheader("📉 トレンド分析（線形回帰）")
    
    if not SCIPY_AVAILABLE:
        st.error("📦 この機能を使用するには scipy のインストールが必要です")
        st.code("pip install scipy", language="bash")
        return
    
    subject = st.selectbox("科目を選択", list(st.session_state.grades.keys()), key="trend_subject")
    
    if subject not in st.session_state.grades or not st.session_state.grades[subject]:
        st.info("この科目の成績データはありません")
        return
    
    df = pd.DataFrame(st.session_state.grades[subject])
    
    if len(df) < 2:
        st.warning("トレンド分析には2件以上のデータが必要です")
        return
    
    # インデックスを追加
    df['index'] = range(1, len(df) + 1)
    
    # 線形回帰
    slope, intercept, r_value, p_value, std_err = stats.linregress(df['index'], df['grade'])
    
    # トレンド判定
    if slope > 1:
        trend = "📈 上昇傾向"
        trend_color = "green"
    elif slope < -1:
        trend = "📉 下降傾向"
        trend_color = "red"
    else:
        trend = "➡️ 安定"
        trend_color = "blue"
    
    # グラフ作成
    fig = go.Figure()
    
    # 実際のデータ
    fig.add_trace(go.Scatter(
        x=df['index'],
        y=df['grade'],
        mode='markers+lines',
        name='実際の成績',
        marker=dict(size=10, color='#FF6B6B'),
        line=dict(color='#FF6B6B', width=2)
    ))
    
    # 回帰直線
    regression_line = slope * df['index'] + intercept
    fig.add_trace(go.Scatter(
        x=df['index'],
        y=regression_line,
        mode='lines',
        name='トレンドライン',
        line=dict(color=trend_color, width=3, dash='dash')
    ))
    
    fig.update_layout(
        title=f"{subject}の成績トレンド",
        xaxis_title="記録順序",
        yaxis_title="成績",
        height=500,
        yaxis=dict(range=[0, 100])
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # 統計情報
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("トレンド", trend)
    with col2:
        st.metric("傾き（1回あたりの変化）", f"{slope:.2f}点")
    with col3:
        st.metric("決定係数 (R²)", f"{r_value**2:.3f}", help="1に近いほど直線的な変化")

# =============== 成績分布 ===============

def display_grade_distribution():
    """ヒストグラムによる成績分布の可視化"""
    st.subheader("📊 成績分布（ヒストグラム）")
    
    subject = st.selectbox("科目を選択", list(st.session_state.grades.keys()), key="dist_subject")
    
    if subject not in st.session_state.grades or not st.session_state.grades[subject]:
        st.info("この科目の成績データはありません")
        return
    
    df = pd.DataFrame(st.session_state.grades[subject])
    
    # ヒストグラム
    fig = px.histogram(
        df,
        x='grade',
        nbins=10,
        title=f"{subject}の成績分布",
        labels={'grade': '成績', 'count': '件数'},
        color_discrete_sequence=['#4ECDC4']
    )
    
    # 平均線を追加
    mean_grade = df['grade'].mean()
    fig.add_vline(
        x=mean_grade,
        line_dash="dash",
        line_color="red",
        annotation_text=f"平均: {mean_grade:.1f}",
        annotation_position="top"
    )
    
    fig.update_layout(
        height=500,
        xaxis=dict(range=[0, 100]),
        bargap=0.1
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # 成績区分の集計
    st.markdown("### 成績区分")
    grade_ranges = {
        "優秀 (90-100点)": len(df[df['grade'] >= 90]),
        "良好 (80-89点)": len(df[(df['grade'] >= 80) & (df['grade'] < 90)]),
        "普通 (70-79点)": len(df[(df['grade'] >= 70) & (df['grade'] < 80)]),
        "要改善 (60-69点)": len(df[(df['grade'] >= 60) & (df['grade'] < 70)]),
        "不合格 (60点未満)": len(df[df['grade'] < 60])
    }
    
    col1, col2 = st.columns(2)
    with col1:
        for label, count in list(grade_ranges.items())[:3]:
            st.metric(label, f"{count}件")
    with col2:
        for label, count in list(grade_ranges.items())[3:]:
            st.metric(label, f"{count}件")

# =============== テストvs課題比較 ===============

def display_test_vs_assignment():
    """箱ひげ図によるテストと課題の比較"""
    st.subheader("📦 テストと課題の比較（箱ひげ図）")
    
    subject = st.selectbox("科目を選択", list(st.session_state.grades.keys()), key="compare_subject")
    
    if subject not in st.session_state.grades or not st.session_state.grades[subject]:
        st.info("この科目の成績データはありません")
        return
    
    df = pd.DataFrame(st.session_state.grades[subject])
    
    # 箱ひげ図
    fig = px.box(
        df,
        x='type',
        y='grade',
        title=f"{subject}のタイプ別成績比較",
        labels={'type': 'タイプ', 'grade': '成績'},
        color='type',
        points="all"
    )
    
    fig.update_layout(
        height=500,
        yaxis=dict(range=[0, 100])
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # タイプ別統計
    st.markdown("### タイプ別統計")
    for grade_type in df['type'].unique():
        type_df = df[df['type'] == grade_type]
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric(f"{grade_type} 平均", f"{type_df['grade'].mean():.1f}")
        with col2:
            st.metric(f"{grade_type} 中央値", f"{type_df['grade'].median():.1f}")
        with col3:
            st.metric(f"{grade_type} 最高", f"{type_df['grade'].max():.0f}")
        with col4:
            st.metric(f"{grade_type} 最低", f"{type_df['grade'].min():.0f}")

# =============== 全科目比較 ===============

def display_all_subjects_comparison():
    """全科目の比較（棒グラフ・レーダーチャート）"""
    st.subheader("🎯 全科目比較")
    
    if not st.session_state.grades:
        st.info("成績データがありません")
        return
    
    # 各科目の平均を計算
    subjects = []
    averages = []
    counts = []
    
    for subject, grades in st.session_state.grades.items():
        if grades:
            df = pd.DataFrame(grades)
            subjects.append(subject)
            averages.append(df['grade'].mean())
            counts.append(len(grades))
    
    if not subjects:
        st.info("成績データがありません")
        return
    
    # 棒グラフ
    st.markdown("### 📊 科目別平均点")
    fig_bar = go.Figure(data=[
        go.Bar(
            x=subjects,
            y=averages,
            text=[f"{avg:.1f}" for avg in averages],
            textposition='auto',
            marker_color='#FF6B6B'
        )
    ])
    
    fig_bar.update_layout(
        title="科目別平均成績",
        xaxis_title="科目",
        yaxis_title="平均点",
        height=400,
        yaxis=dict(range=[0, 100])
    )
    
    st.plotly_chart(fig_bar, use_container_width=True)
    
    # レーダーチャート
    st.markdown("### 🎯 レーダーチャート")
    fig_radar = go.Figure()
    
    fig_radar.add_trace(go.Scatterpolar(
        r=averages,
        theta=subjects,
        fill='toself',
        name='平均点',
        line_color='#4ECDC4'
    ))
    
    fig_radar.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )
        ),
        showlegend=True,
        title="科目別成績レーダー",
        height=500
    )
    
    st.plotly_chart(fig_radar, use_container_width=True)
    
    # 科目別データ数
    st.markdown("### 📝 科目別データ数")
    data_summary = pd.DataFrame({
        "科目": subjects,
        "平均点": [f"{avg:.2f}" for avg in averages],
        "データ数": counts
    })
    st.dataframe(data_summary, use_container_width=True)
