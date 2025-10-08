# progress.py

import streamlit as st
from data import record_progress
from datetime import datetime
import pandas as pd

def track_progress():
    # 進捗トラッキングの処理
    st.header("進捗トラッキング")
    
    # 科目が存在するか確認
    if 'subjects' not in st.session_state or not st.session_state.subjects:
        st.error("まず科目を登録してください")
        return
    
    subject = st.selectbox("科目を選択", st.session_state.subjects)
    study_time = st.number_input("学習時間（時間）", min_value=0.0, step=0.5)
    task = st.text_input("感想コメント")
    motivation = st.slider("学習のやる気（1〜5）", min_value=1, max_value=5, step=1)
    
    if st.button("進捗を記録"):
        if record_progress(subject, study_time, task, motivation):
            st.success("進捗が記録されました")
        else:
            st.error("有効なデータを入力してください")
    
    # 記録済み進捗の表示
    st.subheader("記録済み進捗")
    if 'progress' in st.session_state and st.session_state.progress:
        data = []
        for subj, progress in st.session_state.progress.items():
            for p in progress:
                data.append({
                    '科目': subj,
                    '日付': p['date'],
                    '学習時間（時間）': p['time'],
                    'やる気': p.get('motivation', 'N/A'),
                    '感想コメント': p['task'],
                })
        df = pd.DataFrame(data)
        st.table(df)
    else:
        st.write("記録済みの進捗はありません。")