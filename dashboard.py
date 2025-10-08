# dashboard.py

import streamlit as st
import pandas as pd
import plotly.express as px
import json  # リマインダーを読み込むために追加

def display_dashboard():
    # 進捗ダッシュボードの処理
    st.header("進捗ダッシュボード")
    
    # 科目が存在するか確認
    if 'subjects' not in st.session_state or not st.session_state.subjects:
        st.error("まず科目を登録してください")
        return
    
    subject = st.selectbox("科目を選択", st.session_state.subjects)
    
    # 進捗データが存在するか確認
    if subject in st.session_state.progress:
        df = pd.DataFrame(st.session_state.progress[subject])
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        
        # 学習時間の推移をプロット
        fig = px.line(df, x='date', y='time', title=f"{subject}の学習時間推移")
        st.plotly_chart(fig)
        
        # 総学習時間の表示
        total_time = df['time'].sum()
        st.metric(label="総学習時間", value=f"{total_time:.1f}時間")
        
        # 完了したタスクの表示
        st.subheader("完了したタスク")
        for task in df['task'].unique():
            if task:
                st.write(f"- {task}")
    else:
        st.write("この科目の進捗データはありません。")

    # リマインダーの表示
    st.subheader("リマインダー")
    try:
        with open('reminders.json', 'r', encoding='utf-8') as f:
            reminders = json.load(f)
        # 選択された科目のリマインダーを抽出
        subject_reminders = [r for r in reminders if r['subject'] == subject]
        if subject_reminders:
            for reminder in subject_reminders:
                st.write(f"**タイプ**: {reminder['type']}, **期日**: {reminder['date']}, **内容**: {reminder['text']}")
        else:
            st.write("この教科の予定はありません。")
    except (FileNotFoundError, json.JSONDecodeError):
        st.write("リマインダー情報を読み込めませんでした。")