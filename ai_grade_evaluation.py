"""
成績評価AI機能モジュール
成績データの統計分析とAIによる詳細評価
"""
import json
import time
import streamlit as st
from ai_config import get_ai_response, call_api_with_retry, DEFAULT_MAX_COMPLETION_TOKENS, COMPLEX_REASONING_EFFORT
from data import get_user_profile


def load_grade_criteria():
    """成績評価基準の読み込み"""
    try:
        with open('grade_criteria.json', 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        return {
            "S": {"min": 90, "max": 100, "description": "極めて優秀"},
            "A": {"min": 80, "max": 89, "description": "優秀"},
            "B": {"min": 70, "max": 79, "description": "良好"},
            "C": {"min": 60, "max": 69, "description": "合格"},
            "D": {"min": 0, "max": 59, "description": "不合格"}
        }


def load_grades():
    """成績データの読み込み"""
    try:
        with open('grades.json', 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        return {}


def calculate_average_grade(grades_data):
    """加重平均の計算"""
    if not grades_data:
        return 0
    total_weighted_grade = sum(grade["grade"] * grade["weight"] for grade in grades_data)
    total_weight = sum(grade["weight"] for grade in grades_data)
    return round(total_weighted_grade / total_weight if total_weight > 0 else 0, 2)


def get_grade_evaluation(score, criteria):
    """点数から評価を取得"""
    for grade, info in criteria.items():
        if info["min"] <= score <= info["max"]:
            return grade, info["description"]
    return "評価不能", "点数が評価範囲外です"


def analyze_grade_statistics(grades_data, num_recent=30):
    """成績データの詳細な統計分析（最適化版）"""
    if not grades_data:
        return None
    
    # 最新N件を取得（日付でソート）
    sorted_grades = sorted(grades_data, key=lambda x: x.get("date", ""), reverse=True)
    recent_grades = sorted_grades[:num_recent]
    
    # 基本統計
    scores = [g["grade"] for g in recent_grades]
    
    stats = {
        "count": len(recent_grades),
        "average": round(sum(scores) / len(scores), 2) if scores else 0,
        "weighted_average": calculate_average_grade(recent_grades),
        "max_score": max(scores) if scores else 0,
        "min_score": min(scores) if scores else 0,
        "max_grade_detail": max(recent_grades, key=lambda x: x["grade"]) if recent_grades else None,
        "min_grade_detail": min(recent_grades, key=lambda x: x["grade"]) if recent_grades else None,
    }
    
    # 標準偏差の計算
    if len(scores) > 1:
        mean_score = stats["average"]
        variance = sum((x - mean_score) ** 2 for x in scores) / len(scores)
        stats["std_deviation"] = round(variance ** 0.5, 2)
    else:
        stats["std_deviation"] = 0
    
    # トレンド分析（最近5件 vs その前5件）
    if len(recent_grades) >= 10:
        recent_5 = [g["grade"] for g in recent_grades[:5]]
        previous_5 = [g["grade"] for g in recent_grades[5:10]]
        recent_avg = sum(recent_5) / len(recent_5)
        previous_avg = sum(previous_5) / len(previous_5)
        stats["trend"] = "上昇" if recent_avg > previous_avg else "下降" if recent_avg < previous_avg else "安定"
        stats["trend_diff"] = round(recent_avg - previous_avg, 2)
    else:
        stats["trend"] = "データ不足"
        stats["trend_diff"] = 0
    
    # タイプ別の集計
    type_summary = {}
    for g in recent_grades:
        g_type = g.get("type", "不明")
        if g_type not in type_summary:
            type_summary[g_type] = {"count": 0, "scores": [], "avg": 0}
        type_summary[g_type]["count"] += 1
        type_summary[g_type]["scores"].append(g["grade"])
    
    for g_type, data in type_summary.items():
        data["avg"] = round(sum(data["scores"]) / len(data["scores"]), 2)
    
    stats["type_summary"] = type_summary
    
    # コメント履歴
    comments = [g.get("comment", "") for g in recent_grades if g.get("comment")]
    stats["recent_comments"] = comments[:10]  # 最新10件のコメント
    
    return stats


def display_grade_evaluation():
    """成績評価UIの表示"""
    st.subheader("📊 成績評価（最適化版）")
    grades_data = load_grades()
    if not grades_data:
        st.error("成績データが見つかりません")
        return
    
    subject = st.selectbox("科目を選択してください", list(grades_data.keys()))
    
    # 分析する成績件数の設定
    col1, col2 = st.columns([2, 1])
    with col1:
        num_records = st.slider("分析する成績件数", min_value=5, max_value=50, value=30, step=5,
                               help="より多くのデータを分析することで、詳細な傾向が把握できます")
    with col2:
        show_details = st.checkbox("詳細統計を表示", value=True)
    
    if subject and st.button("🔍 詳細な成績分析を実行", type="primary"):
        subject_grades = grades_data[subject]
        
        # データ件数の事前チェック
        if len(subject_grades) < 3:
            st.error("⚠️ **データが不足しています**")
            st.warning(f"現在の成績データ: **{len(subject_grades)}件**")
            st.info("""
            📝 **AI分析には最低3件の成績データが必要です**
            
            以下の方法でデータを追加してください：
            1. 「成績記録」ページで新しい成績を入力
            2. データが3件以上になったら再度分析を実行
            
            💡 より詳細な分析には5件以上のデータを推奨します
            """)
            return
        
        # データが少ない場合の警告
        if len(subject_grades) < 5:
            st.warning(f"""
            ⚠️ **データ件数が少なめです（{len(subject_grades)}件）**
            
            現在の状態でも基本的な分析は可能ですが、より正確な傾向分析やトレンド判定には
            **5件以上のデータ**を推奨します。
            """)
        
        # 統計分析の実行
        with st.spinner("成績データを分析中..."):
            stats = analyze_grade_statistics(subject_grades, num_records)
        
        if not stats:
            st.warning("分析可能な成績データがありません")
            return
        
        # === 統計情報の表示 ===
        st.markdown("---")
        st.markdown("### 📈 統計サマリー")
        
        metric_cols = st.columns(5)
        with metric_cols[0]:
            # データ件数に応じた表示
            count_label = f"{stats['count']}件"
            if stats['count'] < 5:
                count_label += " ⚠️"
            st.metric("分析件数", count_label)
        with metric_cols[1]:
            st.metric("加重平均", f"{stats['weighted_average']}点")
        with metric_cols[2]:
            st.metric("最高点", f"{stats['max_score']}点")
        with metric_cols[3]:
            st.metric("最低点", f"{stats['min_score']}点")
        with metric_cols[4]:
            trend_icon = "📈" if stats['trend'] == "上昇" else "📉" if stats['trend'] == "下降" else "➡️"
            trend_label = stats['trend']
            # データ不足の場合は「参考値」と表示
            if stats['count'] < 5 and stats['trend'] == "データ不足":
                trend_label = "データ不足"
            st.metric("トレンド", f"{trend_icon} {trend_label}", 
                     delta=f"{stats['trend_diff']:+.1f}点" if stats['trend_diff'] != 0 and stats['count'] >= 5 else None)
        
        # 詳細統計の表示
        if show_details:
            with st.expander("📊 詳細統計情報", expanded=True):
                detail_cols = st.columns(2)
                
                with detail_cols[0]:
                    st.markdown("**基本統計**")
                    st.write(f"- 単純平均: {stats['average']}点")
                    st.write(f"- 標準偏差: {stats['std_deviation']}点")
                    st.write(f"- 点数範囲: {stats['min_score']}～{stats['max_score']}点")
                    
                    if stats['max_grade_detail']:
                        st.markdown("**最高得点記録**")
                        max_g = stats['max_grade_detail']
                        st.write(f"- {max_g['date']}: {max_g['grade']}点 ({max_g['type']})")
                        if max_g.get('comment'):
                            st.write(f"- コメント: {max_g['comment']}")
                
                with detail_cols[1]:
                    st.markdown("**タイプ別分析**")
                    for g_type, data in stats['type_summary'].items():
                        st.write(f"**{g_type}** ({data['count']}回)")
                        st.write(f"  平均: {data['avg']}点")
        
        # === 最新10件のコメント表示 ===
        if stats['recent_comments']:
            with st.expander("💬 最近のコメント（最新10件）", expanded=False):
                for idx, comment in enumerate(stats['recent_comments'], 1):
                    st.markdown(f"{idx}. {comment}")
        
        # === AI分析の実行 ===
        st.markdown("---")
        st.markdown("### 🤖 AI による個別最適化分析")
        
        # ユーザープロフィールの取得
        user_profile = get_user_profile()
        if user_profile.get("age") and user_profile.get("education_level"):
            st.info(f"👤 プロフィール情報を活用: {user_profile['age']}歳 / {user_profile['education_level']}")
        else:
            st.warning("💡 プロフィールを設定すると、より適切なアドバイスが得られます（科目登録ページで設定可能）")
        
        with st.spinner("AIが詳細な分析とアドバイスを生成中..."):
            # 個別最適化されたプロンプトの構築（GPT-5-mini向けに簡潔化）
            tone_guidance = ""
            if user_profile.get("education_level"):
                edu_level = user_profile["education_level"]
                if edu_level in ["小学生", "中学生"]:
                    tone_guidance = "優しく、わかりやすい言葉で説明。"
                elif edu_level == "高校生":
                    tone_guidance = "分かりやすさを保ち、やや専門的な用語も交える。"
                elif edu_level == "大学生":
                    tone_guidance = "論理的で専門的な説明。学術的観点を含む。"
                elif edu_level == "大学院生":
                    tone_guidance = "高度な分析と専門的洞察。研究的視点を含む。"
            
            # プロフィール情報の簡潔化
            profile_str = ""
            if user_profile.get("age") and user_profile.get("education_level"):
                profile_str = f"[学習者: {user_profile['age']}歳・{user_profile['education_level']}]"
            
            # データ件数に応じた注意書き
            data_note = ""
            if stats['count'] < 5:
                data_note = f"\n⚠️ 注意: データ件数が{stats['count']}件と少なめです。基本的な分析に留め、今後のデータ蓄積の重要性を説明してください。"
            
            prompt = f"""{profile_str}{data_note}

【科目】{subject}

【統計（過去{stats['count']}件）】
加重平均:{stats['weighted_average']}点 最高:{stats['max_score']}点 最低:{stats['min_score']}点
標準偏差:{stats['std_deviation']}点 トレンド:{stats['trend']}({stats['trend_diff']:+.1f}点)

【タイプ別】
"""
            # タイプ別データの追加（簡潔化）
            for g_type, data in stats['type_summary'].items():
                prompt += f"{g_type}:{data['avg']}点({data['count']}回) "
            
            prompt += "\n\n"
            
            # 最近のコメント履歴を追加（最大5件に制限）
            if stats['recent_comments']:
                prompt += "【最近のコメント】\n"
                for idx, comment in enumerate(stats['recent_comments'][:5], 1):
                    prompt += f"{idx}. {comment}\n"
                prompt += "\n"
            
            # GPT-5-mini向けに簡潔化した分析指示（データ件数を考慮）
            if stats['count'] < 5:
                # データが少ない場合は簡潔な分析
                prompt += f"""【分析依頼】{tone_guidance if tone_guidance else ''}
データ件数が{stats['count']}件と少ないため、以下を簡潔に作成:

1. 現状評価（現在の成績レベルと特徴）
2. 見られる傾向（タイプ別の得意/苦手）
3. 今後のアドバイス（改善のヒント、今後のデータ蓄積の重要性）
4. 励まし（ポジティブメッセージ）

※データが少ないことを考慮し、断定的な表現は避け「現時点では〜」といった表現を使用。
※長時間の推論は行わず、効率的に要点を押さえた分析を実施すること。"""
            else:
                # データが十分な場合は詳細な分析
                prompt += f"""【分析依頼】{tone_guidance if tone_guidance else ''}
以下を含む詳細な成績分析レポートを作成:

1. 総合評価（加重平均{stats['weighted_average']}点、偏差{stats['std_deviation']}点、トレンド{stats['trend']}の解釈）
2. 強みと課題（タイプ別の得意/苦手分野、具体的な改善ポイント）
3. 具体的アドバイス（短期的改善策、タイプ別対策、効果的な勉強法）
4. 励ましと目標（ポジティブメッセージ、到達可能な次の目標）

数値データを根拠に、個別具体的で建設的な分析を。
※長時間の推論は行わず、効率的に要点を押さえた分析を実施すること。"""
            
            # AIレスポンスの生成（リトライ機能付き）
            try:
                st.info("🔄 AI分析を開始します...")
                
                # システムプロンプトにトーン指示を統合
                system_prompt = "成績を分析し、詳細で建設的なアドバイスを提供する教育カウンセラー。"
                if tone_guidance:
                    system_prompt += f" {tone_guidance}"
                
                # GPT-5推論モデル用に最適化（推論トークン + 出力トークンを考慮）
                # 成績分析は複雑なタスクなのでreasoning_effort='medium'を使用
                response = call_api_with_retry(
                    lambda: get_ai_response(
                        prompt,
                        system_content=system_prompt,
                        max_tokens=DEFAULT_MAX_COMPLETION_TOKENS,
                        reasoning_effort=COMPLEX_REASONING_EFFORT
                    )
                )
                
                # 応答チェック
                if not response or response.strip() == "":
                    st.error("⚠️ AIから空の応答が返されました。")
                    response = "申し訳ありません。分析の生成に失敗しました。データを確認して再試行してください。"
                elif "申し訳ありません" in response and "エラー" in response:
                    st.error(f"⚠️ AI応答にエラーメッセージが含まれています: {response}")
                else:
                    st.success("✅ AI分析が完了しました！")
                    
            except Exception as e:
                st.error(f"❌ 分析中にエラーが発生しました: {str(e)}")
                st.error(f"エラーの種類: {type(e).__name__}")
                import traceback
                st.code(traceback.format_exc())
                response = "申し訳ありません。分析の生成に失敗しました。後ほど再試行してください。"
        
        # === 分析結果の表示 ===
        st.markdown(response)
        
        # === ダウンロード機能 ===
        st.markdown("---")
        report_text = f"""
# {subject} 成績分析レポート

## 統計サマリー
- 分析件数: {stats['count']}件
- 加重平均: {stats['weighted_average']}点
- トレンド: {stats['trend']}

## AI分析結果
{response}

生成日時: {time.strftime('%Y-%m-%d %H:%M:%S')}
"""
        st.download_button(
            label="📥 分析レポートをダウンロード",
            data=report_text,
            file_name=f"{subject}_成績分析_{time.strftime('%Y%m%d')}.txt",
            mime="text/plain"
        )
