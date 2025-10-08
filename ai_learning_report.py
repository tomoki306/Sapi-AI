"""
学習レポート生成AI機能モジュール
期間別学習データの分析とレポート生成
"""
import streamlit as st
from datetime import datetime, timedelta
from ai_config import get_ai_response, call_api_with_retry, DEFAULT_MAX_COMPLETION_TOKENS, COMPLEX_REASONING_EFFORT
from data import get_user_profile


def generate_learning_report(period, grades_data, progress_data):
    """AIによる学習レポートの生成
    
    Args:
        period: 期間（"今週", "今月", "全期間"）
        grades_data: 成績データ
        progress_data: 進捗データ
    
    Returns:
        str: 生成された学習レポート
    """
    try:
        # ユーザープロフィールを取得
        user_profile = get_user_profile()
        age = user_profile.get('age', '不明')
        education_level = user_profile.get('education_level', '不明')
        
        # データのサマリーを作成（GPT-5-mini向けに詳細化）
        prompt = f"""【学習者プロフィール】
年齢: {age}歳
現在の学歴/学習段階: {education_level}

【対象期間】
{period}

【成績データの概要】
"""
        # 成績データの詳細な要約
        if grades_data:
            for subject, grades in grades_data.items():
                if grades:
                    avg = sum(g['grade'] for g in grades) / len(grades)
                    max_grade = max(g['grade'] for g in grades)
                    min_grade = min(g['grade'] for g in grades)
                    prompt += f"- {subject}: 平均{avg:.1f}点（最高{max_grade}点、最低{min_grade}点、{len(grades)}件）\n"
        else:
            prompt += "成績データなし\n"
        
        prompt += "\n【学習時間の概要】\n"
        
        # 進捗データの詳細な要約
        if progress_data:
            for subject, progress in progress_data.items():
                if progress:
                    total_hours = sum(p['time'] for p in progress)
                    avg_hours = total_hours / len(progress)
                    prompt += f"- {subject}: 合計{total_hours:.1f}時間（平均{avg_hours:.1f}時間/回、{len(progress)}回）\n"
        else:
            prompt += "進捗データなし\n"
        
        prompt += f"""

学習者の年齢（{age}歳）と学習段階（{education_level}）を考慮した、詳細で建設的な学習レポートを作成してください。

以下の形式で回答してください：

# 📊 学習レポート（{period}）

## 1. 学習の総括
この期間の学習全体を振り返り、主な成果と特徴を2-3段落で詳しく記載してください。具体的な数値を用いて分析してください。

## 2. 各科目の詳細分析
科目ごとに、以下の観点から評価とコメントを記載してください：
- 成績の傾向と特徴
- 学習時間の配分と効率
- 強みと改善点
- 具体的な推奨事項

## 3. 強みと成長ポイント
この期間で特に良かった点や成長が見られた点を、具体的な根拠とともに4-5個箇条書きで記載してください。

## 4. 改善すべき点と対策
今後改善が必要な点と、その具体的な対策を4-5個箇条書きで記載してください。

## 5. 次期への具体的提言
学習者の年齢（{age}歳）と学習段階（{education_level}）に適した、実践的で具体的なアドバイスを4-5個記載してください。

学習者の年齢と学習段階を十分に考慮し、理解しやすく、励ましを含む建設的な内容にしてください。

【重要な指示】
※入力データを読み込んだら、できるだけ少ない推論で直接的に出力を作成すること。
※長時間の推論や複雑な思考プロセスは不要です。データを見て即座に分析結果を生成してください。
※効率的で簡潔な推論を最優先し、データに基づく具体的な洞察を直接的に記述すること。"""
        
        # AIレスポンス生成（GPT-5推論モデル用に最適化）
        # 学習レポート生成は包括的な分析タスクなのでreasoning_effort='medium'を使用
        response = call_api_with_retry(
            lambda: get_ai_response(
                prompt,
                system_content=f"あなたは{education_level}の学習者向けに詳細な分析とアドバイスを行う専門的な教育アナリストです。データに基づいた客観的な評価と、年齢に配慮した励ましと具体的な指導を提供してください。",
                max_tokens=DEFAULT_MAX_COMPLETION_TOKENS,
                reasoning_effort=COMPLEX_REASONING_EFFORT
            )
        )
        
        return response
        
    except Exception as e:
        st.error(f"レポートの生成に失敗しました: {str(e)}")
        return None


def display_learning_report_in_ai():
    """AI機能内での学習レポート生成UI"""
    st.subheader("📊 AI学習レポート生成")
    st.info("💡 ユーザープロフィール（年齢・学歴）を考慮した学習レポートを作成します")
    
    # ユーザープロフィール表示
    user_profile = get_user_profile()
    if user_profile.get('age') and user_profile.get('education_level'):
        st.success(f"👤 {user_profile['age']}歳 / {user_profile['education_level']}")
    else:
        st.warning("⚠️ ユーザープロフィールが未設定です。より適切なレポートのため、科目登録画面でプロフィールを設定してください。")
    
    # 期間選択
    st.markdown("### 📅 レポート期間を選択")
    
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
    from report import filter_grades_by_period, filter_progress_by_period
    filtered_grades = filter_grades_by_period(start, end)
    filtered_progress = filter_progress_by_period(start, end)
    
    # データサマリー表示
    st.markdown("---")
    st.markdown("### 📈 データサマリー")
    
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
                    st.session_state.temp_report = {
                        "period": period_label,
                        "content": report_content,
                        "data_summary": {
                            "subjects": subjects_count,
                            "grades": grades_count,
                            "progress": progress_count,
                            "total_hours": total_hours
                        }
                    }
    
    # 生成されたレポートの表示
    if 'temp_report' in st.session_state and st.session_state.temp_report:
        st.markdown("---")
        st.subheader("✨ 生成されたレポート")
        
        report = st.session_state.temp_report
        
        # レポート内容
        st.markdown(report['content'])
        
        # ダウンロードボタン
        st.markdown("---")
        report_text = f"""
======================================
学習レポート
======================================

対象期間: {report['period']}

【データサマリー】
- 科目数: {report['data_summary']['subjects']}
- 成績データ数: {report['data_summary']['grades']}件
- 学習記録数: {report['data_summary']['progress']}件
- 総学習時間: {report['data_summary']['total_hours']:.1f}時間

======================================

{report['content']}

======================================
"""
        st.download_button(
            label="📥 レポートをダウンロード",
            data=report_text,
            file_name=f"learning_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain",
            type="primary"
        )
