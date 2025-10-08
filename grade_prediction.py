# grade_prediction.py
"""
成績の予測機能
最終成績の予測、目標達成に必要な点数の計算、シミュレーション機能
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import plotly.express as px
import plotly.graph_objects as go


def display_grade_prediction():
    """成績予測メイン画面"""
    st.header("🔮 成績予測・シミュレーション")
    
    st.markdown("""
    現在の成績データから最終成績を予測したり、目標達成に必要な点数を計算できます。
    """)
    
    # 機能選択
    tab1, tab2, tab3 = st.tabs([
        "📊 最終成績予測",
        "🎯 目標達成シミュレーション",
        "📈 成績トレンド分析"
    ])
    
    with tab1:
        display_final_grade_prediction()
    
    with tab2:
        display_goal_simulation()
    
    with tab3:
        display_trend_analysis()


def display_final_grade_prediction():
    """最終成績の予測"""
    st.subheader("📊 最終成績予測")
    
    if not st.session_state.subjects:
        st.warning("科目が登録されていません")
        return
    
    # 科目選択
    subject = st.selectbox(
        "科目を選択",
        st.session_state.subjects,
        key="prediction_subject"
    )
    
    if subject not in st.session_state.grades or not st.session_state.grades[subject]:
        st.info("この科目の成績データがありません")
        return
    
    grades_list = st.session_state.grades[subject]
    
    # 現在の成績分析
    st.markdown("---")
    st.markdown("### 📈 現在の成績状況")
    
    # データフレーム作成
    df = pd.DataFrame(grades_list)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')
    
    # 加重平均の計算
    current_weighted_avg = calculate_weighted_average(grades_list)
    
    # 統計情報
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("現在の加重平均", f"{current_weighted_avg:.1f}点")
    col2.metric("記録数", f"{len(grades_list)}件")
    col3.metric("最高点", f"{df['grade'].max():.0f}点")
    col4.metric("最低点", f"{df['grade'].min():.0f}点")
    
    # 成績の推移グラフ（同一日の複数記録が重ならないよう微小な時間を付与）
    df_for_plot = df.copy()
    df_for_plot['order_in_day'] = df_for_plot.groupby(df_for_plot['date'].dt.date).cumcount()
    df_for_plot['date_adjusted'] = df_for_plot['date'] + pd.to_timedelta(
        df_for_plot['order_in_day'] * 5, unit='m'
    )

    if 'type' not in df_for_plot.columns:
        df_for_plot['type'] = '不明'
    if 'weight' not in df_for_plot.columns:
        df_for_plot['weight'] = 1

    custom_hover = np.stack([
        df_for_plot['date'].dt.strftime('%Y-%m-%d'),
        df_for_plot['type'].fillna('不明'),
        df_for_plot['weight'].fillna(1)
    ], axis=-1)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_for_plot['date_adjusted'],
        y=df_for_plot['grade'],
        mode='lines+markers',
        name='成績',
        hovertemplate=(
            '<b>日付:</b> %{customdata[0]}<br>'
            '<b>点数:</b> %{y}点<br>'
            '<b>タイプ:</b> %{customdata[1]}<br>'
            '<b>重み:</b> %{customdata[2]}<extra></extra>'
        ),
        customdata=custom_hover
    ))

    fig.add_hline(
        y=current_weighted_avg,
        line_dash="dash",
        line_color="red",
        annotation_text=f"加重平均: {current_weighted_avg:.1f}点"
    )

    fig.update_layout(
        title='成績推移',
        xaxis_title='日付',
        yaxis_title='成績（点）',
        hovermode='x unified'
    )
    fig.update_xaxes(tickformat='%Y-%m-%d')

    st.plotly_chart(fig, use_container_width=True)
    
    # 予測設定
    st.markdown("---")
    st.markdown("### 🔮 最終成績予測")
    
    col1, col2 = st.columns(2)
    
    with col1:
        remaining_tests = st.number_input(
            "残りのテスト数",
            min_value=0,
            max_value=20,
            value=1,
            key="prediction_remaining_tests"
        )
    
    with col2:
        test_weight = st.number_input(
            "テストの重み",
            min_value=0.0,
            max_value=10.0,
            value=2.0,
            step=0.5,
            key="prediction_test_weight"
        )
    
    # 予測方法選択
    prediction_method = st.selectbox(
        "予測方法",
        ["現在の平均を維持", "線形トレンド予測", "最近の傾向で予測"],
        key="prediction_method"
    )
    
    if remaining_tests > 0:
        # 予測実行
        predicted_score = predict_future_score(
            grades_list,
            prediction_method
        )
        
        # 最終成績の予測計算
        total_weight = sum(g['weight'] for g in grades_list) + (remaining_tests * test_weight)
        current_weighted_sum = sum(g['grade'] * g['weight'] for g in grades_list)
        future_weighted_sum = remaining_tests * test_weight * predicted_score
        
        predicted_final_avg = (current_weighted_sum + future_weighted_sum) / total_weight
        
        # 予測結果表示
        st.markdown("---")
        st.markdown("### 📊 予測結果")
        
        col_a, col_b, col_c = st.columns(3)
        
        col_a.metric(
            "現在の加重平均",
            f"{current_weighted_avg:.1f}点"
        )
        
        col_b.metric(
            "残りテストの予測点数",
            f"{predicted_score:.1f}点",
            help=f"予測方法: {prediction_method}"
        )
        
        col_c.metric(
            "予測される最終成績",
            f"{predicted_final_avg:.1f}点",
            delta=f"{predicted_final_avg - current_weighted_avg:+.1f}点"
        )
        
        # シナリオ分析
        st.markdown("---")
        st.markdown("### 📈 シナリオ分析")
        
        scenarios = {
            "楽観的（95点）": 95,
            "やや良い（85点）": 85,
            "予測値": predicted_score,
            "やや悪い（70点）": 70,
            "悲観的（60点）": 60
        }
        
        scenario_results = []
        for scenario_name, score in scenarios.items():
            future_sum = remaining_tests * test_weight * score
            final_avg = (current_weighted_sum + future_sum) / total_weight
            scenario_results.append({
                "シナリオ": scenario_name,
                "残りテストの点数": score,
                "最終成績": final_avg,
                "現在との差": final_avg - current_weighted_avg
            })
        
        scenario_df = pd.DataFrame(scenario_results)
        display_df = scenario_df.copy()
        display_df["残りテストの点数"] = display_df["残りテストの点数"].map(lambda v: f"{v:.0f}点")
        display_df["最終成績"] = display_df["最終成績"].map(lambda v: f"{v:.1f}点")
        display_df["現在との差"] = display_df["現在との差"].map(lambda v: f"{v:+.1f}点")
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        # ビジュアル表示
        fig_scenario = go.Figure()
        
        color_map = {}
        for scenario in scenario_df["シナリオ"]:
            if "悲観" in scenario:
                color_map[scenario] = "red"
            elif "悪い" in scenario:
                color_map[scenario] = "orange"
            elif "予測" in scenario:
                color_map[scenario] = "blue"
            elif "良い" in scenario:
                color_map[scenario] = "lightgreen"
            else:
                color_map[scenario] = "green"
        
        fig_scenario.add_trace(go.Bar(
            y=scenario_df["シナリオ"],
            x=scenario_df["最終成績"],
            orientation='h',
            marker_color=[color_map[name] for name in scenario_df["シナリオ"]],
            text=scenario_df["最終成績"].map(lambda v: f"{v:.1f}点"),
            textposition='outside'
        ))
        
        fig_scenario.add_hline(
            y=current_weighted_avg,
            line_dash="dash",
            line_color="gray",
            annotation_text=f"現在: {current_weighted_avg:.1f}点"
        )
        
        fig_scenario.update_layout(
            title="シナリオ別最終成績予測",
            xaxis_title="成績（点）",
            yaxis_title="シナリオ",
            showlegend=False,
            height=400,
            margin=dict(l=120, r=40, t=60, b=40)
        )
        
        st.plotly_chart(fig_scenario, use_container_width=True)


def display_goal_simulation():
    """目標達成シミュレーション"""
    st.subheader("🎯 目標達成シミュレーション")
    
    st.info("目標の成績を達成するために、残りのテストで何点必要かを計算します")
    
    if not st.session_state.subjects:
        st.warning("科目が登録されていません")
        return
    
    # 科目選択
    subject = st.selectbox(
        "科目を選択",
        st.session_state.subjects,
        key="simulation_subject"
    )
    
    if subject not in st.session_state.grades or not st.session_state.grades[subject]:
        st.info("この科目の成績データがありません")
        return
    
    grades_list = st.session_state.grades[subject]
    current_weighted_avg = calculate_weighted_average(grades_list)
    
    # 現在の状況表示
    col1, col2 = st.columns(2)
    col1.metric("現在の加重平均", f"{current_weighted_avg:.1f}点")
    col2.metric("記録数", f"{len(grades_list)}件")
    
    # 目標設定
    st.markdown("---")
    st.markdown("### 🎯 目標設定")
    
    col_a, col_b, col_c = st.columns(3)
    
    with col_a:
        target_grade = st.number_input(
            "目標成績",
            min_value=0,
            max_value=100,
            value=int(current_weighted_avg) + 10,
            key="simulation_target"
        )
    
    with col_b:
        remaining_tests = st.number_input(
            "残りのテスト数",
            min_value=1,
            max_value=20,
            value=1,
            key="simulation_remaining"
        )
    
    with col_c:
        test_weight = st.number_input(
            "テストの重み",
            min_value=0.0,
            max_value=10.0,
            value=2.0,
            step=0.5,
            key="simulation_weight"
        )
    
    # 必要点数の計算
    st.markdown("---")
    st.markdown("### 🧮 必要点数の計算")
    
    required_score = calculate_required_score(
        grades_list,
        target_grade,
        remaining_tests,
        test_weight
    )
    
    if required_score is not None:
        if required_score > 100:
            st.error(f"❌ 目標達成は不可能です（必要点数: {required_score:.1f}点 > 100点）")
            st.warning("目標を下げるか、テストの数を増やすことを検討してください")
        elif required_score < 0:
            st.success(f"🎉 すでに目標を達成しています！")
        else:
            # 達成難易度の判定
            if required_score >= 95:
                difficulty = "⭐⭐⭐⭐⭐ 非常に難しい"
                color = "red"
            elif required_score >= 85:
                difficulty = "⭐⭐⭐⭐ 難しい"
                color = "orange"
            elif required_score >= 75:
                difficulty = "⭐⭐⭐ 普通"
                color = "blue"
            elif required_score >= 60:
                difficulty = "⭐⭐ やや簡単"
                color = "lightgreen"
            else:
                difficulty = "⭐ 簡単"
                color = "green"
            
            st.markdown(f"""
            ### 📊 計算結果
            
            目標成績 **{target_grade}点** を達成するには、残り{remaining_tests}回のテストで
            
            ### <span style="color:{color}; font-size:36px;">{required_score:.1f}点</span>
            
            が必要です。
            
            **達成難易度**: {difficulty}
            """, unsafe_allow_html=True)
            
            # 詳細内訳
            with st.expander("📝 詳細内訳"):
                current_weighted_sum = sum(g['grade'] * g['weight'] for g in grades_list)
                current_total_weight = sum(g['weight'] for g in grades_list)
                future_total_weight = remaining_tests * test_weight
                total_weight = current_total_weight + future_total_weight
                
                st.markdown(f"""
                - 現在の加重合計点: {current_weighted_sum:.1f}点
                - 現在の総重み: {current_total_weight:.1f}
                - 残りテストの総重み: {future_total_weight:.1f}
                - 全体の総重み: {total_weight:.1f}
                - 目標の加重合計点: {target_grade * total_weight:.1f}点
                - 残りで必要な加重合計点: {target_grade * total_weight - current_weighted_sum:.1f}点
                """)
            
            # 複数テストの場合の配分
            if remaining_tests > 1:
                st.markdown("---")
                st.markdown("### 📊 点数配分のシミュレーション")
                
                st.info("すべてのテストで同じ点数を取ると仮定した場合の必要点数です")
                
                # 異なる配分パターン
                patterns = {
                    "均等": [required_score] * remaining_tests,
                    "前半重視": [required_score + 10] + [required_score - 10/(remaining_tests-1)] * (remaining_tests - 1),
                    "後半重視": [required_score - 10/(remaining_tests-1)] * (remaining_tests - 1) + [required_score + 10]
                }
                
                pattern_results = []
                for pattern_name, scores in patterns.items():
                    avg_score = np.mean(scores)
                    pattern_results.append({
                        "パターン": pattern_name,
                        **{f"テスト{i+1}": f"{score:.1f}点" for i, score in enumerate(scores)},
                        "平均": f"{avg_score:.1f}点"
                    })
                
                pattern_df = pd.DataFrame(pattern_results)
                st.dataframe(pattern_df, use_container_width=True, hide_index=True)


def display_trend_analysis():
    """成績トレンド分析"""
    st.subheader("📈 成績トレンド分析")
    
    st.info("過去の成績データから傾向を分析し、今後の成績を予測します")
    
    if not st.session_state.subjects:
        st.warning("科目が登録されていません")
        return
    
    # 科目選択
    subject = st.selectbox(
        "科目を選択",
        st.session_state.subjects,
        key="trend_subject"
    )
    
    if subject not in st.session_state.grades or not st.session_state.grades[subject]:
        st.info("この科目の成績データがありません")
        return
    
    grades_list = st.session_state.grades[subject]
    
    if len(grades_list) < 3:
        st.warning("トレンド分析には最低3件の成績データが必要です")
        return
    
    # データフレーム作成
    df = pd.DataFrame(grades_list)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')
    df['days_from_start'] = (df['date'] - df['date'].min()).dt.days
    
    # 線形回帰
    from numpy.polynomial import Polynomial
    
    x = df['days_from_start'].values
    y = df['grade'].values
    
    # 1次多項式でフィット（線形回帰）
    p = Polynomial.fit(x, y, 1)
    trend_line = p(x)
    
    # トレンドの判定
    slope = p.convert().coef[1] if len(p.convert().coef) > 1 else 0
    
    if slope > 0.1:
        trend_status = "📈 上昇傾向"
        trend_color = "green"
        trend_message = "成績が向上しています！この調子で頑張りましょう。"
    elif slope < -0.1:
        trend_status = "📉 下降傾向"
        trend_color = "red"
        trend_message = "成績が下がっています。学習方法を見直しましょう。"
    else:
        trend_status = "➡️ 横ばい"
        trend_color = "blue"
        trend_message = "成績が安定しています。"
    
    # 結果表示
    col1, col2, col3 = st.columns(3)
    col1.metric("トレンド", trend_status)
    col2.metric("変化率", f"{slope:.2f}点/日")
    col3.metric("データ数", f"{len(grades_list)}件")
    
    st.markdown(f"**{trend_message}**")
    
    # グラフ表示
    fig = go.Figure()
    
    # 実際のデータ
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['grade'],
        mode='markers+lines',
        name='実際の成績',
        marker=dict(size=10),
        line=dict(width=2)
    ))
    
    # トレンドライン
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=trend_line,
        mode='lines',
        name='トレンドライン',
        line=dict(dash='dash', color=trend_color, width=3)
    ))
    
    fig.update_layout(
        title='成績トレンド分析',
        xaxis_title='日付',
        yaxis_title='成績（点）',
        height=500
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # 統計情報
    st.markdown("---")
    st.markdown("### 📊 統計情報")
    
    col_a, col_b, col_c, col_d = st.columns(4)
    col_a.metric("平均点", f"{df['grade'].mean():.1f}点")
    col_b.metric("標準偏差", f"{df['grade'].std():.1f}点")
    col_c.metric("最高点", f"{df['grade'].max():.0f}点")
    col_d.metric("最低点", f"{df['grade'].min():.0f}点")


# ユーティリティ関数

def calculate_weighted_average(grades_list: List[Dict[str, Any]]) -> float:
    """加重平均を計算"""
    if not grades_list:
        return 0.0
    
    total_weighted_sum = sum(g['grade'] * g.get('weight', 1) for g in grades_list)
    total_weight = sum(g.get('weight', 1) for g in grades_list)
    
    return total_weighted_sum / total_weight if total_weight > 0 else 0.0


def predict_future_score(grades_list: List[Dict[str, Any]], method: str) -> float:
    """将来の成績を予測"""
    if not grades_list:
        return 70.0  # デフォルト値
    
    df = pd.DataFrame(grades_list)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')
    
    if method == "現在の平均を維持":
        return calculate_weighted_average(grades_list)
    
    elif method == "線形トレンド予測":
        if len(grades_list) < 2:
            return calculate_weighted_average(grades_list)
        
        # 線形回帰
        from numpy.polynomial import Polynomial
        x = np.arange(len(df))
        y = df['grade'].values
        
        p = Polynomial.fit(x, y, 1)
        # 次の点を予測
        next_pred = p(len(df))
        
        return min(100, max(0, next_pred))
    
    elif method == "最近の傾向で予測":
        # 最近3件の平均
        recent_grades = df.tail(min(3, len(df)))
        return recent_grades['grade'].mean()
    
    return calculate_weighted_average(grades_list)


def calculate_required_score(
    grades_list: List[Dict[str, Any]],
    target_grade: float,
    remaining_tests: int,
    test_weight: float
) -> Optional[float]:
    """目標達成に必要な点数を計算"""
    if remaining_tests <= 0:
        return None
    
    # 現在の加重合計と総重み
    current_weighted_sum = sum(g['grade'] * g.get('weight', 1) for g in grades_list)
    current_total_weight = sum(g.get('weight', 1) for g in grades_list)
    
    # 残りテストの総重み
    future_total_weight = remaining_tests * test_weight
    
    # 全体の総重み
    total_weight = current_total_weight + future_total_weight
    
    # 目標の加重合計
    target_weighted_sum = target_grade * total_weight
    
    # 残りで必要な加重合計
    required_weighted_sum = target_weighted_sum - current_weighted_sum
    
    # 残り1テストあたりの必要点数
    required_score = required_weighted_sum / future_total_weight
    
    return required_score
