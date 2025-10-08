# subject.py

import streamlit as st
import altair as alt
import pandas as pd
from data import (
    add_subject, load_subjects, get_latest_grades, get_total_study_time, 
    get_motivation_data, get_all_grades_data, get_user_profile, 
    update_user_profile, get_education_levels
)

def register_subject():
    # セッションステートの初期化
    if 'subjects' not in st.session_state:
        load_subjects()

    # ユーザープロフィールセクション（最上部に追加）
    with st.expander("👤 ユーザープロフィール設定", expanded=False):
        st.markdown("### プロフィール情報")
        st.info("年齢と学歴を設定すると、AI機能がより適切なアドバイスを提供します")
        
        profile = get_user_profile()
        
        col_p1, col_p2 = st.columns(2)
        
        with col_p1:
            # 現在のプロフィール表示
            if profile.get("age") and profile.get("education_level"):
                st.success("✅ プロフィール設定済み")
                st.write(f"**年齢:** {profile['age']}歳")
                st.write(f"**学歴:** {profile['education_level']}")
                if profile.get("updated_at"):
                    st.caption(f"最終更新: {profile['updated_at']}")
            else:
                st.warning("⚠️ プロフィール未設定")
                st.write("AI機能を最大限活用するため、プロフィールを設定してください")
        
        with col_p2:
            # プロフィール編集フォーム
            st.markdown("#### プロフィール編集")
            
            age_input = st.number_input(
                "年齢",
                min_value=6,
                max_value=100,
                value=profile.get("age") if profile.get("age") else 18,
                step=1,
                help="あなたの現在の年齢を入力してください"
            )
            
            education_levels = get_education_levels()
            current_education = profile.get("education_level")
            default_index = education_levels.index(current_education) if current_education in education_levels else 2
            
            education_input = st.selectbox(
                "学歴",
                options=education_levels,
                index=default_index,
                help="あなたの現在の学歴を選択してください"
            )
            
            if st.button("💾 プロフィールを保存", type="primary"):
                if update_user_profile(age_input, education_input):
                    st.success("✅ プロフィールを更新しました！")
                    st.balloons()
                    st.rerun()
                else:
                    st.error("❌ プロフィールの更新に失敗しました")
    
    st.markdown("---")  # 区切り線

    # 3列レイアウトの設定（比率を調整）
    col1, col2, col3 = st.columns([1, 1, 2])

    # 左列: やる気と科目登録
    with col1:
        # やる気データ
        st.header("学習のやる気")
        motivation_data = get_motivation_data()
        for subject, motivation in motivation_data.items():
            st.write(f"{subject}: {motivation}")

        st.markdown("---")  # 区切り線

        # 科目登録
        st.header("科目登録")
        new_subject = st.text_input("新しい科目を入力してください")
        if st.button("科目を追加"):
            if add_subject(new_subject):
                st.success(f"{new_subject}が追加されました")
            else:
                st.error("有効な科目名を入力してください")
        
        st.subheader("登録済み科目")
        for subject in st.session_state.subjects:
            st.write(subject)

    # 中央列: 学習時間と最新成績
    with col2:
        # 総学習時間
        st.header("総学習時間")
        total_study_time = get_total_study_time()
        for subject, time in total_study_time.items():
            st.write(f"{subject}: {time}時間")

        st.markdown("---")  # 区切り線

        # 最新成績
        st.header("最新の成績")
        latest_grades = get_latest_grades()
        for subject, grade in latest_grades.items():
            st.write(f"{subject}: {grade}点")

    # 右列: グラフ表示
    with col3:
        st.header("成績推移")
        all_grades_data = get_all_grades_data()
        all_records = []
        
        # 各科目の最新5回分のデータのみを取得
        for subject, grades_list in all_grades_data.items():
            # 最新5回分のみを使用
            recent_grades = grades_list[-5:] if len(grades_list) >= 5 else grades_list
            for i, g in enumerate(recent_grades, 1):
                all_records.append({
                    "subject": subject,
                    "date": g["date"],
                    "grade": g["grade"],
                    "試験回数": i  # 1から始まる連番
                })
        
        if all_records:
            df = pd.DataFrame(all_records)
            df["date"] = pd.to_datetime(df["date"])
            # 日付でソート
            df = df.sort_values("date")

            # 成績グラフ（最新5回分）
            st.subheader("最新5回の成績推移")
            st.write("💡 凡例の科目名をクリックすると表示/非表示を切り替えできます")
            
            # 科目選択のためのselection
            subject_selection = alt.selection_multi(fields=['subject'])
            
            chart = alt.Chart(df).mark_line(
                point=alt.OverlayMarkDef(size=150, filled=True)
            ).add_selection(
                subject_selection
            ).encode(
                x=alt.X("試験回数:Q", 
                       title="試験回数（新しい順）",
                       scale=alt.Scale(domain=[1, 5]),
                       axis=alt.Axis(tickCount=5, format='d')),  # 整数表示に変更
                y=alt.Y("grade:Q", 
                       title="成績", 
                       scale=alt.Scale(domain=[0, 100])),
                color=alt.Color("subject:N", title="科目"),
                opacity=alt.condition(subject_selection, alt.value(1.0), alt.value(0.2)),
                tooltip=[
                    alt.Tooltip("subject", title="科目"),
                    alt.Tooltip("grade", title="成績"),
                    alt.Tooltip("date", title="実施日", format="%Y-%m-%d")
                ]
            ).properties(
                height=400,
                width="container"
            ).configure_axis(
                labelFontSize=12,
                titleFontSize=14
            ).configure_legend(
                labelFontSize=12
            )
            st.altair_chart(chart, use_container_width=True)
        else:
            st.write("まだ成績データがありません")