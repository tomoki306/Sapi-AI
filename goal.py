# goal.py

import streamlit as st
from data import save_goals, normalize_goals_data

def set_goals():
    # 学習目標設定の処理
    st.header("学習目標設定")
    
    # 科目が存在するか確認
    if 'subjects' not in st.session_state or not st.session_state.subjects:
        st.error("まず科目を登録してください")
        return
    
    # 目標の初期化（リスト形式を保証）
    if 'goals' not in st.session_state:
        st.session_state.goals = []
    else:
        st.session_state.goals = normalize_goals_data(st.session_state.goals)
    
    subject = st.selectbox("科目を選択", st.session_state.subjects)
    goal_type = st.radio("目標タイプ", ["短期", "長期"])
    goal = st.text_area("目標を入力")
    deadline = st.date_input("期限（オプション）")
    
    if st.button("目標を保存"):
        if subject and goal:
            new_goal = {
                'subject': subject,
                'goal_type': goal_type,
                'goal': goal,
                'deadline': str(deadline) if deadline else '',
                'status': '進行中'
            }
            st.session_state.goals.append(new_goal)
            
            # 保存
            save_goals()
            
            st.success("目標が保存されました")
            st.rerun()  # 画面を再読み込みして更新を反映
    
    # 設定済み目標の表示
    st.subheader("設定済み目標")

    if 'goals' in st.session_state and st.session_state.goals:
        # 科目ごとにグループ化
        goals_by_subject = {}
        for goal in st.session_state.goals:
            if isinstance(goal, dict):
                subj = goal.get('subject', '不明')
                if subj not in goals_by_subject:
                    goals_by_subject[subj] = {'短期': [], '長期': []}
                goal_type = goal.get('goal_type', '短期')
                goals_by_subject[subj][goal_type].append(goal)
        
        # 表示
        for subj, types in goals_by_subject.items():
            st.write(f"### **{subj}**")
            for type_name, goal_list in types.items():
                if goal_list:
                    st.write(f"**{type_name}目標:**")
                    for g in goal_list:
                        deadline_text = f" (期限: {g.get('deadline')})" if g.get('deadline') else ""
                        status = g.get('status', '進行中')
                        st.markdown(f"- {g.get('goal', '')} {deadline_text} [{status}]")
    else:
        st.write("設定済みの目標はありません。")