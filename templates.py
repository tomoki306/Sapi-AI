# templates.py - テンプレート機能

import streamlit as st
import json
import os
from datetime import datetime
from typing import Dict, List, Any
from data import save_grades, save_progress
from logger import log_info, log_error

# テンプレートファイルのパス
GRADE_TEMPLATES_FILE = "grade_templates.json"
PLAN_TEMPLATES_FILE = "plan_templates.json"


# =========================
# テンプレートファイルの読み込み・保存
# =========================

def load_grade_templates() -> List[Dict[str, Any]]:
    """成績テンプレートを読み込む"""
    if os.path.exists(GRADE_TEMPLATES_FILE):
        try:
            with open(GRADE_TEMPLATES_FILE, 'r', encoding='utf-8') as f:
                templates = json.load(f)
                log_info(f"成績テンプレート読み込み成功: {len(templates)}件", "TEMPLATES")
                return templates
        except Exception as e:
            log_error(e, "成績テンプレート読み込みエラー")
            return []
    return []


def save_grade_templates(templates: List[Dict[str, Any]]):
    """成績テンプレートを保存"""
    try:
        with open(GRADE_TEMPLATES_FILE, 'w', encoding='utf-8') as f:
            json.dump(templates, f, ensure_ascii=False, indent=2)
        log_info(f"成績テンプレート保存成功: {len(templates)}件", "TEMPLATES")
    except Exception as e:
        log_error(e, "成績テンプレート保存エラー")


def load_plan_templates() -> List[Dict[str, Any]]:
    """学習計画テンプレートを読み込む"""
    if os.path.exists(PLAN_TEMPLATES_FILE):
        try:
            with open(PLAN_TEMPLATES_FILE, 'r', encoding='utf-8') as f:
                templates = json.load(f)
                log_info(f"学習計画テンプレート読み込み成功: {len(templates)}件", "TEMPLATES")
                return templates
        except Exception as e:
            log_error(e, "学習計画テンプレート読み込みエラー")
            return []
    return []


def save_plan_templates(templates: List[Dict[str, Any]]):
    """学習計画テンプレートを保存"""
    try:
        with open(PLAN_TEMPLATES_FILE, 'w', encoding='utf-8') as f:
            json.dump(templates, f, ensure_ascii=False, indent=2)
        log_info(f"学習計画テンプレート保存成功: {len(templates)}件", "TEMPLATES")
    except Exception as e:
        log_error(e, "学習計画テンプレート保存エラー")


# =========================
# メイン機能
# =========================

def display_template_management():
    """テンプレート管理のメイン画面"""
    st.title("📋 テンプレート管理")
    st.markdown("成績記録や学習計画を効率化するテンプレート機能です。")
    
    # タブで機能を分ける
    tab1, tab2 = st.tabs(["📝 成績テンプレート", "📅 学習計画テンプレート"])
    
    with tab1:
        display_grade_templates()
    
    with tab2:
        display_plan_templates()


# =========================
# 成績テンプレート機能
# =========================

def display_grade_templates():
    """成績テンプレート管理画面"""
    st.subheader("📝 成績テンプレート")
    st.markdown("定期テストなど、複数科目の成績を一括で記録するためのテンプレートです。")
    
    # サブタブ
    sub_tab1, sub_tab2, sub_tab3 = st.tabs(["✨ テンプレートから入力", "➕ テンプレート作成", "📚 テンプレート管理"])
    
    with sub_tab1:
        use_grade_template()
    
    with sub_tab2:
        create_grade_template()
    
    with sub_tab3:
        manage_grade_templates()


def create_grade_template():
    """成績テンプレートを作成"""
    st.markdown("### ➕ 新しいテンプレートを作成")
    
    # テンプレート基本情報
    template_name = st.text_input("テンプレート名", placeholder="例: 定期テスト 数学・英語・国語", key="grade_template_name")
    template_description = st.text_area("説明 (オプション)", placeholder="このテンプレートの用途を説明", key="grade_template_description")
    
    # 科目選択
    st.markdown("#### 📚 科目を選択")
    if 'subjects' not in st.session_state or len(st.session_state.subjects) == 0:
        st.warning("⚠️ 科目が登録されていません。先に科目を登録してください。")
        return
    
    selected_subjects = st.multiselect(
        "テンプレートに含める科目",
        options=st.session_state.subjects,
        default=st.session_state.subjects[:3] if len(st.session_state.subjects) >= 3 else st.session_state.subjects
    )
    
    if not selected_subjects:
        st.info("💡 科目を選択してください。")
        return
    
    # 各科目の設定
    st.markdown("#### ⚙️ 各科目の設定")
    subject_settings = []
    
    for subject in selected_subjects:
        with st.expander(f"📖 {subject} の設定"):
            col1, col2 = st.columns(2)
            with col1:
                grade_type = st.selectbox(
                    "成績の種類",
                    options=["テスト", "課題", "小テスト", "その他"],
                    key=f"type_{subject}"
                )
            with col2:
                weight = st.number_input(
                    "重み",
                    min_value=0.1,
                    max_value=10.0,
                    value=1.0,
                    step=0.1,
                    key=f"weight_{subject}"
                )
            
            subject_settings.append({
                "subject": subject,
                "grade_type": grade_type,
                "weight": weight
            })
    
    # テンプレート保存
    if st.button("💾 テンプレートを保存", type="primary", key="save_grade_template_btn"):
        if not template_name:
            st.error("❌ テンプレート名を入力してください。")
            return
        
        template = {
            "id": datetime.now().strftime("%Y%m%d_%H%M%S"),
            "name": template_name,
            "description": template_description,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "subjects": subject_settings
        }
        
        templates = load_grade_templates()
        templates.append(template)
        save_grade_templates(templates)
        
        st.success(f"✅ テンプレート「{template_name}」を保存しました!")
        log_info(f"成績テンプレート作成: {template_name} ({len(subject_settings)}科目)", "TEMPLATES")


def use_grade_template():
    """テンプレートから成績を入力"""
    st.markdown("### ✨ テンプレートから一括入力")
    
    templates = load_grade_templates()
    
    if not templates:
        st.info("💡 テンプレートが登録されていません。「テンプレート作成」タブから作成してください。")
        return
    
    # テンプレート選択
    template_names = [t['name'] for t in templates]
    selected_template_name = st.selectbox("使用するテンプレート", options=template_names)
    
    if not selected_template_name:
        return
    
    # 選択されたテンプレートを取得
    selected_template = next((t for t in templates if t['name'] == selected_template_name), None)
    
    if not selected_template:
        st.error("❌ テンプレートの読み込みに失敗しました。")
        return
    
    # テンプレート情報表示
    with st.expander("📋 テンプレート詳細", expanded=True):
        st.markdown(f"**名前**: {selected_template['name']}")
        if selected_template.get('description'):
            st.markdown(f"**説明**: {selected_template['description']}")
        st.markdown(f"**科目数**: {len(selected_template['subjects'])}科目")
        st.markdown(f"**作成日時**: {selected_template['created_at']}")
    
    # 日付入力
    test_date = st.date_input("テスト日", value=datetime.now())
    
    # 各科目の点数入力
    st.markdown("#### 📊 各科目の点数を入力")
    
    grade_inputs = []
    
    for subject_setting in selected_template['subjects']:
        subject = subject_setting['subject']
        grade_type = subject_setting['grade_type']
        weight = subject_setting['weight']
        
        col1, col2, col3 = st.columns([2, 2, 3])
        with col1:
            st.markdown(f"**{subject}**")
        with col2:
            st.markdown(f"({grade_type}, 重み: {weight})")
        with col3:
            grade = st.number_input(
                "点数",
                min_value=0,
                max_value=100,
                value=0,
                step=1,
                key=f"grade_{subject}",
                label_visibility="collapsed"
            )
            
            grade_inputs.append({
                "subject": subject,
                "grade": grade,
                "grade_type": grade_type,
                "weight": weight
            })
    
    # コメント入力
    common_comment = st.text_area("コメント (全科目共通、オプション)", placeholder="例: 期末テスト", key="grade_template_common_comment")
    
    # 一括登録ボタン
    if st.button("📝 一括登録", type="primary", key="bulk_register_grades_btn"):
        if not st.session_state.get('grades'):
            st.session_state.grades = {}
        
        registered_count = 0
        
        for grade_input in grade_inputs:
            subject = grade_input['subject']
            grade = grade_input['grade']
            grade_type = grade_input['grade_type']
            weight = grade_input['weight']
            
            # 0点の科目はスキップするか確認
            if grade == 0:
                continue
            
            # 科目がまだない場合は初期化
            if subject not in st.session_state.grades:
                st.session_state.grades[subject] = []
            
            # 成績データを追加
            st.session_state.grades[subject].append({
                "date": test_date.strftime("%Y-%m-%d"),
                "grade": grade,
                "type": grade_type,
                "weight": weight,
                "comment": common_comment
            })
            
            registered_count += 1
        
        # 保存
        save_grades()
        
        st.success(f"✅ {registered_count}科目の成績を一括登録しました!")
        log_info(f"テンプレート使用: {selected_template['name']} - {registered_count}科目登録", "TEMPLATES")


def manage_grade_templates():
    """テンプレート管理 (一覧・編集・削除)"""
    st.markdown("### 📚 テンプレート一覧")
    
    templates = load_grade_templates()
    
    if not templates:
        st.info("💡 テンプレートが登録されていません。")
        return
    
    # テンプレート一覧表示
    for i, template in enumerate(templates):
        with st.expander(f"📋 {template['name']} ({len(template['subjects'])}科目)"):
            st.markdown(f"**ID**: {template['id']}")
            st.markdown(f"**作成日時**: {template['created_at']}")
            if template.get('description'):
                st.markdown(f"**説明**: {template['description']}")
            
            st.markdown("**科目設定**:")
            for subject_setting in template['subjects']:
                st.markdown(f"- {subject_setting['subject']}: {subject_setting['grade_type']} (重み: {subject_setting['weight']})")
            
            # 削除ボタン
            if st.button(f"🗑️ このテンプレートを削除", key=f"delete_grade_template_{i}"):
                templates.pop(i)
                save_grade_templates(templates)
                st.success(f"✅ テンプレート「{template['name']}」を削除しました。")
                st.rerun()


# =========================
# 学習計画テンプレート機能
# =========================

def display_plan_templates():
    """学習計画テンプレート管理画面"""
    st.subheader("📅 学習計画テンプレート")
    st.markdown("週間学習計画や試験対策計画のテンプレートです。")
    
    # サブタブ
    sub_tab1, sub_tab2, sub_tab3 = st.tabs(["✨ テンプレートから作成", "➕ テンプレート作成", "📚 テンプレート管理"])
    
    with sub_tab1:
        use_plan_template()
    
    with sub_tab2:
        create_plan_template()
    
    with sub_tab3:
        manage_plan_templates()


def create_plan_template():
    """学習計画テンプレートを作成"""
    st.markdown("### ➕ 新しい計画テンプレートを作成")
    
    # テンプレート基本情報
    template_name = st.text_input("テンプレート名", placeholder="例: 週間学習計画", key="plan_template_name")
    template_description = st.text_area("説明 (オプション)", placeholder="このテンプレートの用途を説明", key="plan_template_description")
    
    # 計画タイプ
    plan_type = st.radio(
        "計画タイプ",
        options=["週間計画", "試験対策計画", "カスタム"],
        horizontal=True
    )
    
    # 科目と学習内容の設定
    st.markdown("#### 📚 学習項目を追加")
    
    if 'plan_template_items' not in st.session_state:
        st.session_state.plan_template_items = []
    
    # 新規項目追加
    with st.expander("➕ 新しい学習項目を追加", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            new_subject = st.selectbox("科目", options=st.session_state.subjects if 'subjects' in st.session_state else [], key="plan_template_new_subject")
        with col2:
            new_duration = st.number_input("学習時間 (時間)", min_value=0.5, max_value=10.0, value=1.0, step=0.5, key="plan_template_new_duration")
        
        new_content = st.text_input("学習内容", placeholder="例: 数学の問題集 p.20-30", key="plan_template_new_content")
        
        if st.button("➕ 項目を追加", key="add_plan_item_btn"):
            if new_subject and new_content:
                st.session_state.plan_template_items.append({
                    "subject": new_subject,
                    "content": new_content,
                    "duration": new_duration
                })
                st.success("✅ 学習項目を追加しました!")
                st.rerun()
    
    # 現在の項目一覧
    if st.session_state.plan_template_items:
        st.markdown("#### 📋 現在の学習項目")
        for i, item in enumerate(st.session_state.plan_template_items):
            col1, col2, col3, col4 = st.columns([2, 3, 1, 1])
            with col1:
                st.markdown(f"**{item['subject']}**")
            with col2:
                st.markdown(f"{item['content']}")
            with col3:
                st.markdown(f"{item['duration']}時間")
            with col4:
                if st.button("🗑️", key=f"remove_item_{i}"):
                    st.session_state.plan_template_items.pop(i)
                    st.rerun()
    else:
        st.info("💡 学習項目を追加してください。")
    
    # テンプレート保存
    if st.button("💾 テンプレートを保存", type="primary", key="save_plan_template_btn"):
        if not template_name:
            st.error("❌ テンプレート名を入力してください。")
            return
        
        if not st.session_state.plan_template_items:
            st.error("❌ 学習項目を1つ以上追加してください。")
            return
        
        template = {
            "id": datetime.now().strftime("%Y%m%d_%H%M%S"),
            "name": template_name,
            "description": template_description,
            "plan_type": plan_type,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "items": st.session_state.plan_template_items.copy()
        }
        
        templates = load_plan_templates()
        templates.append(template)
        save_plan_templates(templates)
        
        st.success(f"✅ 計画テンプレート「{template_name}」を保存しました!")
        log_info(f"学習計画テンプレート作成: {template_name} ({len(st.session_state.plan_template_items)}項目)", "TEMPLATES")
        
        # リセット
        st.session_state.plan_template_items = []


def use_plan_template():
    """テンプレートから学習計画を作成"""
    st.markdown("### ✨ テンプレートから計画を作成")
    
    templates = load_plan_templates()
    
    if not templates:
        st.info("💡 計画テンプレートが登録されていません。「テンプレート作成」タブから作成してください。")
        return
    
    # テンプレート選択
    template_names = [t['name'] for t in templates]
    selected_template_name = st.selectbox("使用するテンプレート", options=template_names)
    
    if not selected_template_name:
        return
    
    # 選択されたテンプレートを取得
    selected_template = next((t for t in templates if t['name'] == selected_template_name), None)
    
    if not selected_template:
        st.error("❌ テンプレートの読み込みに失敗しました。")
        return
    
    # テンプレート情報表示
    with st.expander("📋 テンプレート詳細", expanded=True):
        st.markdown(f"**名前**: {selected_template['name']}")
        if selected_template.get('description'):
            st.markdown(f"**説明**: {selected_template['description']}")
        st.markdown(f"**計画タイプ**: {selected_template['plan_type']}")
        st.markdown(f"**学習項目数**: {len(selected_template['items'])}項目")
        st.markdown(f"**作成日時**: {selected_template['created_at']}")
    
    # 学習項目プレビュー
    st.markdown("#### 📚 学習項目")
    for item in selected_template['items']:
        st.markdown(f"- **{item['subject']}**: {item['content']} ({item['duration']}時間)")
    
    total_hours = sum([item['duration'] for item in selected_template['items']])
    st.info(f"💡 合計学習時間: {total_hours}時間")
    
    # AI機能で計画を生成する場合のメッセージ
    st.markdown("---")
    st.markdown("#### 🤖 AI機能で計画を作成")
    st.info("💡 このテンプレートを基に、AI機能の「学習計画作成」で詳細な計画を生成できます。メニューの「AI機能」→「学習計画作成」からご利用ください。")
    
    # 手動で計画を記録する場合
    st.markdown("#### 📝 手動で記録")
    if st.button("📝 このテンプレートを使って学習計画を記録", type="primary"):
        st.info("💡 「学習目標設定」メニューから手動で計画を記録できます。")


def manage_plan_templates():
    """計画テンプレート管理 (一覧・編集・削除)"""
    st.markdown("### 📚 計画テンプレート一覧")
    
    templates = load_plan_templates()
    
    if not templates:
        st.info("💡 計画テンプレートが登録されていません。")
        return
    
    # テンプレート一覧表示
    for i, template in enumerate(templates):
        with st.expander(f"📋 {template['name']} ({len(template['items'])}項目)"):
            st.markdown(f"**ID**: {template['id']}")
            st.markdown(f"**計画タイプ**: {template['plan_type']}")
            st.markdown(f"**作成日時**: {template['created_at']}")
            if template.get('description'):
                st.markdown(f"**説明**: {template['description']}")
            
            st.markdown("**学習項目**:")
            total_hours = 0
            for item in template['items']:
                st.markdown(f"- {item['subject']}: {item['content']} ({item['duration']}時間)")
                total_hours += item['duration']
            
            st.markdown(f"**合計学習時間**: {total_hours}時間")
            
            # 削除ボタン
            if st.button(f"🗑️ このテンプレートを削除", key=f"delete_plan_template_{i}"):
                templates.pop(i)
                save_plan_templates(templates)
                st.success(f"✅ テンプレート「{template['name']}」を削除しました。")
                st.rerun()
