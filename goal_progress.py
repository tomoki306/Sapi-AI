# goal_progress.py
"""
学習目標の進捗管理機能
目標と実績の紐付け、達成度の可視化、未達成目標の警告
"""

from datetime import datetime
from typing import Dict, List, Any
import streamlit as st


def calculate_goal_progress(goal: Dict[str, Any], grades_data: Dict[str, List[Dict]], 
                           progress_data: Dict[str, List[Dict]]) -> Dict[str, Any]:
    """
    目標の進捗を計算
    Args:
        goal: 目標の辞書
        grades_data: 成績データ
        progress_data: 進捗データ
    Returns:
        進捗情報の辞書
    """
    goal_type = goal.get('type', '成績目標')
    subject = goal.get('subject', '')
    target_value = goal.get('target_value', 0)
    current_value = 0
    progress_percentage = 0
    
    if goal_type == '成績目標':
        # 成績目標の場合
        if subject in grades_data and grades_data[subject]:
            # 最新の成績を取得
            latest_grades = sorted(
                grades_data[subject],
                key=lambda x: x.get('date', ''),
                reverse=True
            )
            if latest_grades:
                current_value = latest_grades[0].get('grade', 0)
        
        if target_value > 0:
            progress_percentage = min((current_value / target_value) * 100, 100)
    
    elif goal_type == '学習時間目標':
        # 学習時間目標の場合
        if subject in progress_data:
            # 目標期間内の学習時間を集計
            total_study_time = sum(
                p.get('study_time', 0) for p in progress_data[subject]
            )
            current_value = total_study_time
        
        if target_value > 0:
            progress_percentage = min((current_value / target_value) * 100, 100)
    
    # 達成状況の判定
    if progress_percentage >= 100:
        status = "達成"
        status_color = "green"
    elif progress_percentage >= 75:
        status = "もう少し"
        status_color = "blue"
    elif progress_percentage >= 50:
        status = "順調"
        status_color = "orange"
    else:
        status = "要努力"
        status_color = "red"
    
    return {
        'current_value': current_value,
        'target_value': target_value,
        'progress_percentage': progress_percentage,
        'remaining': max(target_value - current_value, 0),
        'status': status,
        'status_color': status_color
    }


def check_goal_deadline(goal: Dict[str, Any]) -> Dict[str, Any]:
    """
    目標の期限をチェック
    Args:
        goal: 目標の辞書
    Returns:
        期限情報の辞書
    """
    deadline = goal.get('deadline', '')
    
    if not deadline:
        return {
            'has_deadline': False,
            'is_overdue': False,
            'is_approaching': False,
            'days_remaining': None,
            'warning_message': ''
        }
    
    try:
        deadline_date = datetime.strptime(deadline, '%Y-%m-%d')
        today = datetime.now()
        days_remaining = (deadline_date - today).days
        
        is_overdue = days_remaining < 0
        is_approaching = 0 <= days_remaining <= 7
        
        if is_overdue:
            warning_message = f"期限を{abs(days_remaining)}日過ぎています"
        elif is_approaching:
            warning_message = f"期限まであと{days_remaining}日です"
        else:
            warning_message = f"期限まで{days_remaining}日"
        
        return {
            'has_deadline': True,
            'is_overdue': is_overdue,
            'is_approaching': is_approaching,
            'days_remaining': days_remaining,
            'warning_message': warning_message
        }
    except ValueError:
        return {
            'has_deadline': False,
            'is_overdue': False,
            'is_approaching': False,
            'days_remaining': None,
            'warning_message': '期限の形式が不正です'
        }


def display_goal_progress_bar(goal: Dict[str, Any], progress_info: Dict[str, Any]):
    """
    目標の進捗バーを表示
    Args:
        goal: 目標の辞書
        progress_info: 進捗情報
    """
    title = goal.get('title', '目標')
    progress = progress_info['progress_percentage']
    current = progress_info['current_value']
    target = progress_info['target_value']
    remaining = progress_info['remaining']
    status = progress_info['status']
    
    # 進捗バーの表示
    st.markdown(f"### 📌 {title}")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # プログレスバー
        st.progress(progress / 100)
        
        # 詳細情報
        goal_type = goal.get('type', '成績目標')
        if goal_type == '成績目標':
            unit = "点"
        elif goal_type == '学習時間目標':
            unit = "時間"
        else:
            unit = ""
        
        st.write(f"**現在:** {current}{unit} / **目標:** {target}{unit}")
        st.write(f"**残り:** {remaining}{unit} ({100 - progress:.1f}%)")
    
    with col2:
        # 達成率とステータス
        st.metric("達成率", f"{progress:.1f}%")
        
        # ステータスバッジ
        status_colors = {
            "green": "🟢",
            "blue": "🔵",
            "orange": "🟠",
            "red": "🔴"
        }
        badge = status_colors.get(progress_info['status_color'], "⚪")
        st.write(f"{badge} **{status}**")


def get_goal_recommendations(goal: Dict[str, Any], progress_info: Dict[str, Any], 
                            deadline_info: Dict[str, Any]) -> List[str]:
    """
    目標達成のための推奨事項を生成
    Args:
        goal: 目標の辞書
        progress_info: 進捗情報
        deadline_info: 期限情報
    Returns:
        推奨事項のリスト
    """
    recommendations = []
    
    progress = progress_info['progress_percentage']
    remaining = progress_info['remaining']
    goal_type = goal.get('type', '成績目標')
    
    # 進捗に基づく推奨
    if progress < 25:
        recommendations.append("⚠️ 進捗が遅れています。学習計画を見直しましょう。")
    elif progress < 50:
        recommendations.append("📚 このペースを維持しながら、もう少し力を入れましょう。")
    elif progress < 75:
        recommendations.append("👍 順調です！この調子で継続しましょう。")
    elif progress < 100:
        recommendations.append("🌟 もう少しで達成です！最後まで頑張りましょう。")
    else:
        recommendations.append("🎉 目標達成おめでとうございます！")
    
    # 期限に基づく推奨
    if deadline_info['has_deadline']:
        days_remaining = deadline_info['days_remaining']
        
        if deadline_info['is_overdue']:
            recommendations.append("⏰ 期限が過ぎています。目標を見直すか、新しい期限を設定しましょう。")
        elif deadline_info['is_approaching'] and progress < 100:
            if goal_type == '成績目標':
                per_day = remaining / max(days_remaining, 1)
                recommendations.append(f"📈 期限まで毎日約{per_day:.1f}点のペースで向上が必要です。")
            elif goal_type == '学習時間目標':
                per_day = remaining / max(days_remaining, 1)
                recommendations.append(f"⏱️ 期限まで毎日約{per_day:.1f}時間の学習が必要です。")
    
    # 具体的なアドバイス
    if goal_type == '成績目標' and remaining > 0:
        if remaining <= 10:
            recommendations.append("💪 小テストや課題で着実に点数を積み重ねましょう。")
        elif remaining <= 20:
            recommendations.append("📝 苦手分野を重点的に復習しましょう。")
        else:
            recommendations.append("🎯 基礎からしっかり学習し直すことをお勧めします。")
    
    return recommendations


def display_all_goals_progress():
    """すべての目標の進捗を表示"""
    st.title("🎯 学習目標の進捗管理")
    
    # データ取得
    goals_data = st.session_state.get('goals', {})
    grades_data = st.session_state.get('grades', {})
    progress_data = st.session_state.get('progress', {})
    
    # 古い形式（辞書の辞書）を新しい形式（リスト）に変換
    goals_list = []
    if isinstance(goals_data, dict):
        for subject, goal_types in goals_data.items():
            if isinstance(goal_types, dict):
                # 短期目標
                for goal_text in goal_types.get('短期', []):
                    goals_list.append({
                        'subject': subject,
                        'type': '短期',
                        'goal': goal_text,
                        'goal_type': '成績目標',  # デフォルト
                        'target_value': 0
                    })
                # 長期目標
                for goal_text in goal_types.get('長期', []):
                    goals_list.append({
                        'subject': subject,
                        'type': '長期',
                        'goal': goal_text,
                        'goal_type': '成績目標',  # デフォルト
                        'target_value': 0
                    })
    elif isinstance(goals_data, list):
        goals_list = goals_data
    
    if not goals_list:
        st.info("📝 まだ目標が設定されていません。「学習目標設定」から目標を登録してください。")
        return
    
    # フィルタオプション
    filter_option = st.selectbox(
        "表示する目標",
        ["すべて", "短期目標のみ", "長期目標のみ"],
        index=0
    )
    
    def _goal_type(goal):
        if not isinstance(goal, dict):
            return '不明'
        goal_type = goal.get('goal_type') or goal.get('type')
        if goal_type in ('短期', '長期'):
            return goal_type
        return '不明'

    # 統計情報
    total_goals = len(goals_list)
    short_term_goals = len([g for g in goals_list if _goal_type(g) == '短期'])
    long_term_goals = len([g for g in goals_list if _goal_type(g) == '長期'])
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("総目標数", total_goals)
    with col2:
        st.metric("短期目標", short_term_goals)
    with col3:
        st.metric("長期目標", long_term_goals)
    
    st.markdown("---")
    
    # 各目標を表示
    displayed_goals = 0
    
    for idx, goal in enumerate(goals_list):
        # フィルタリング
        should_display = False
        
        goal_type_value = _goal_type(goal)

        if filter_option == "すべて":
            should_display = True
        elif filter_option == "短期目標のみ":
            should_display = goal_type_value == '短期'
        elif filter_option == "長期目標のみ":
            should_display = goal_type_value == '長期'
        
        if should_display:
            displayed_goals += 1
            
            # 目標情報を表示
            subject = goal.get('subject', '不明')
            goal_type = goal_type_value
            goal_text = goal.get('goal', '目標内容なし')
            
            # エキスパンダーで表示
            with st.expander(f"📌 【{goal_type}】{subject} - {goal_text[:30]}{'...' if len(goal_text) > 30 else ''}", expanded=False):
                st.markdown(f"**科目:** {subject}")
                st.markdown(f"**タイプ:** {goal_type}")
                st.markdown(f"**内容:** {goal_text}")
                
                # 科目の最新成績を表示
                if subject in grades_data and grades_data[subject]:
                    latest_grade = sorted(
                        grades_data[subject],
                        key=lambda x: x.get('date', ''),
                        reverse=True
                    )[0]
                    st.info(f"📊 最新成績: {latest_grade.get('grade', 'N/A')}点 ({latest_grade.get('date', 'N/A')})")
                
                # 科目の学習時間を表示
                if subject in progress_data and progress_data[subject]:
                    total_time = sum([p.get('time', 0) for p in progress_data[subject]])
                    st.info(f"⏱️ 総学習時間: {total_time:.1f}時間")
    
    if displayed_goals == 0:
        st.warning("表示する目標がありません。")
    else:
        st.success(f"✅ {displayed_goals}件の目標を表示中")
