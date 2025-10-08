# notes.py - メモ・ノート機能

import streamlit as st
import json
import os
from datetime import datetime
from typing import Dict, List, Any
from logger import log_info, log_error

# ノートファイルのパス
NOTES_FILE = "notes.json"


# =========================
# ノートファイルの読み込み・保存
# =========================

def load_notes() -> List[Dict[str, Any]]:
    """ノートを読み込む"""
    if os.path.exists(NOTES_FILE):
        try:
            with open(NOTES_FILE, 'r', encoding='utf-8') as f:
                notes = json.load(f)
                log_info(f"ノート読み込み成功: {len(notes)}件", "NOTES")
                return notes
        except Exception as e:
            log_error(e, "ノート読み込みエラー")
            return []
    return []


def save_notes(notes: List[Dict[str, Any]]):
    """ノートを保存"""
    try:
        with open(NOTES_FILE, 'w', encoding='utf-8') as f:
            json.dump(notes, f, ensure_ascii=False, indent=2)
        log_info(f"ノート保存成功: {len(notes)}件", "NOTES")
    except Exception as e:
        log_error(e, "ノート保存エラー")


# =========================
# メイン機能
# =========================

def display_notes_management():
    """ノート管理のメイン画面"""
    st.title("📝 メモ・ノート")
    st.markdown("学習記録や気づきをメモとして残せます。Markdown形式に対応しています。")
    
    # タブで機能を分ける
    tab1, tab2, tab3 = st.tabs(["✏️ ノート作成", "📚 ノート一覧", "🔍 ノート検索"])
    
    with tab1:
        create_note()
    
    with tab2:
        display_notes_list()
    
    with tab3:
        search_notes()


# =========================
# ノート作成
# =========================

def create_note():
    """ノート作成画面"""
    st.subheader("✏️ 新しいノートを作成")
    
    # 基本情報
    col1, col2 = st.columns(2)
    
    with col1:
        note_title = st.text_input("タイトル *", placeholder="例: 数学 二次関数のまとめ")
    
    with col2:
        # 科目選択
        subjects = st.session_state.get('subjects', [])
        if subjects:
            note_subject = st.selectbox("科目 *", options=subjects)
        else:
            st.warning("⚠️ 科目が登録されていません。")
            note_subject = st.text_input("科目 *", placeholder="科目名を入力")
    
    # タグ入力
    note_tags = st.text_input(
        "タグ (カンマ区切り、オプション)",
        placeholder="例: テスト対策, 公式, 重要"
    )
    
    # 本文入力
    st.markdown("#### 📄 ノート本文")
    st.markdown("💡 Markdown記法が使えます: **太字**, *斜体*, # 見出し, - リスト, `コード` など")
    
    note_content = st.text_area(
        "本文 *",
        height=300,
        placeholder="""# 見出し

## 学習内容
- 項目1
- 項目2

**重要**: ここに重要なポイントを記述

```python
# コード例
print("Hello World")
```
"""
    )
    
    # プレビュー
    if note_content:
        with st.expander("👁️ プレビュー", expanded=False):
            st.markdown(note_content)
    
    # 保存ボタン
    if st.button("💾 ノートを保存", type="primary"):
        if not note_title:
            st.error("❌ タイトルを入力してください。")
            return
        
        if not note_subject:
            st.error("❌ 科目を選択してください。")
            return
        
        if not note_content:
            st.error("❌ 本文を入力してください。")
            return
        
        # タグを配列に変換
        tags_list = []
        if note_tags:
            tags_list = [tag.strip() for tag in note_tags.split(',') if tag.strip()]
        
        # ノートデータ作成
        note = {
            "id": datetime.now().strftime("%Y%m%d_%H%M%S"),
            "title": note_title,
            "subject": note_subject,
            "content": note_content,
            "tags": tags_list,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # 保存
        notes = load_notes()
        notes.append(note)
        save_notes(notes)
        
        st.success(f"✅ ノート「{note_title}」を保存しました!")
        log_info(f"ノート作成: {note_title} (科目: {note_subject})", "NOTES")


# =========================
# ノート一覧
# =========================

def display_notes_list():
    """ノート一覧画面"""
    st.subheader("📚 ノート一覧")
    
    notes = load_notes()
    
    if not notes:
        st.info("💡 ノートが登録されていません。「ノート作成」タブから作成してください。")
        return
    
    # フィルタオプション
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # 科目でフィルタ
        all_subjects = list(set([note['subject'] for note in notes]))
        selected_subject = st.selectbox("科目でフィルタ", options=["すべて"] + all_subjects)
    
    with col2:
        # タグでフィルタ
        all_tags = []
        for note in notes:
            all_tags.extend(note.get('tags', []))
        unique_tags = list(set(all_tags))
        selected_tag = st.selectbox("タグでフィルタ", options=["すべて"] + unique_tags)
    
    with col3:
        # ソート
        sort_order = st.selectbox("並び順", options=["新しい順", "古い順", "タイトル順"])
    
    # フィルタリング
    filtered_notes = notes
    
    if selected_subject != "すべて":
        filtered_notes = [n for n in filtered_notes if n['subject'] == selected_subject]
    
    if selected_tag != "すべて":
        filtered_notes = [n for n in filtered_notes if selected_tag in n.get('tags', [])]
    
    # ソート
    if sort_order == "新しい順":
        filtered_notes = sorted(filtered_notes, key=lambda x: x['created_at'], reverse=True)
    elif sort_order == "古い順":
        filtered_notes = sorted(filtered_notes, key=lambda x: x['created_at'])
    elif sort_order == "タイトル順":
        filtered_notes = sorted(filtered_notes, key=lambda x: x['title'])
    
    # 件数表示
    st.markdown(f"**全{len(notes)}件中 {len(filtered_notes)}件を表示**")
    
    # ノート一覧表示
    for i, note in enumerate(filtered_notes):
        with st.expander(f"📝 {note['title']} ({note['subject']})"):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"**科目**: {note['subject']}")
                st.markdown(f"**作成日時**: {note['created_at']}")
                st.markdown(f"**更新日時**: {note.get('updated_at', note['created_at'])}")
                
                if note.get('tags'):
                    tags_display = ", ".join([f"`{tag}`" for tag in note['tags']])
                    st.markdown(f"**タグ**: {tags_display}")
                
                st.markdown("---")
                st.markdown("### 📄 内容")
                st.markdown(note['content'])
            
            with col2:
                # 編集ボタン
                if st.button("✏️ 編集", key=f"edit_{note['id']}"):
                    st.session_state.editing_note_id = note['id']
                    st.rerun()
                
                # 削除ボタン
                if st.button("🗑️ 削除", key=f"delete_{note['id']}"):
                    notes.remove(note)
                    save_notes(notes)
                    st.success(f"✅ ノート「{note['title']}」を削除しました。")
                    st.rerun()
    
    # 編集モード
    if 'editing_note_id' in st.session_state:
        edit_note(st.session_state.editing_note_id)


def edit_note(note_id: str):
    """ノート編集"""
    st.markdown("---")
    st.subheader("✏️ ノート編集")
    
    notes = load_notes()
    note = next((n for n in notes if n['id'] == note_id), None)
    
    if not note:
        st.error("❌ ノートが見つかりません。")
        del st.session_state.editing_note_id
        return
    
    # 編集フォーム
    col1, col2 = st.columns(2)
    
    with col1:
        edited_title = st.text_input("タイトル *", value=note['title'], key="edit_title")
    
    with col2:
        subjects = st.session_state.get('subjects', [note['subject']])
        default_index = subjects.index(note['subject']) if note['subject'] in subjects else 0
        edited_subject = st.selectbox("科目 *", options=subjects, index=default_index, key="edit_subject")
    
    edited_tags_str = ", ".join(note.get('tags', []))
    edited_tags = st.text_input("タグ (カンマ区切り)", value=edited_tags_str, key="edit_tags")
    
    edited_content = st.text_area("本文 *", value=note['content'], height=300, key="edit_content")
    
    # プレビュー
    if edited_content:
        with st.expander("👁️ プレビュー", expanded=False):
            st.markdown(edited_content)
    
    col_btn1, col_btn2 = st.columns(2)
    
    with col_btn1:
        if st.button("💾 更新を保存", type="primary"):
            if not edited_title or not edited_subject or not edited_content:
                st.error("❌ すべての必須項目を入力してください。")
                return
            
            # タグを配列に変換
            tags_list = []
            if edited_tags:
                tags_list = [tag.strip() for tag in edited_tags.split(',') if tag.strip()]
            
            # ノート更新
            note['title'] = edited_title
            note['subject'] = edited_subject
            note['content'] = edited_content
            note['tags'] = tags_list
            note['updated_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            save_notes(notes)
            
            st.success(f"✅ ノート「{edited_title}」を更新しました!")
            log_info(f"ノート更新: {edited_title}", "NOTES")
            
            del st.session_state.editing_note_id
            st.rerun()
    
    with col_btn2:
        if st.button("❌ キャンセル"):
            del st.session_state.editing_note_id
            st.rerun()


# =========================
# ノート検索
# =========================

def search_notes():
    """ノート検索画面"""
    st.subheader("🔍 ノート検索")
    
    notes = load_notes()
    
    if not notes:
        st.info("💡 ノートが登録されていません。")
        return
    
    # 検索キーワード
    search_keyword = st.text_input("キーワードを入力", placeholder="タイトル、本文、タグから検索")
    
    if not search_keyword:
        st.info("💡 キーワードを入力して検索してください。")
        return
    
    # 検索実行
    search_results = []
    keyword_lower = search_keyword.lower()
    
    for note in notes:
        # タイトル検索
        if keyword_lower in note['title'].lower():
            search_results.append(note)
            continue
        
        # 本文検索
        if keyword_lower in note['content'].lower():
            search_results.append(note)
            continue
        
        # タグ検索
        for tag in note.get('tags', []):
            if keyword_lower in tag.lower():
                search_results.append(note)
                break
        
        # 科目検索
        if keyword_lower in note['subject'].lower():
            if note not in search_results:
                search_results.append(note)
    
    # 検索結果表示
    st.markdown(f"**検索結果: {len(search_results)}件**")
    
    if not search_results:
        st.warning("⚠️ 該当するノートが見つかりませんでした。")
        return
    
    # 結果一覧
    for note in search_results:
        with st.expander(f"📝 {note['title']} ({note['subject']})"):
            st.markdown(f"**科目**: {note['subject']}")
            st.markdown(f"**作成日時**: {note['created_at']}")
            
            if note.get('tags'):
                tags_display = ", ".join([f"`{tag}`" for tag in note['tags']])
                st.markdown(f"**タグ**: {tags_display}")
            
            st.markdown("---")
            st.markdown("### 📄 内容")
            
            # ハイライト表示 (簡易版)
            content_preview = note['content'][:500]  # 最初の500文字
            if len(note['content']) > 500:
                content_preview += "..."
            
            st.markdown(content_preview)
            
            # 詳細表示ボタン
            if st.button("📖 全文を表示", key=f"view_{note['id']}"):
                st.markdown(note['content'])


# =========================
# 統計情報
# =========================

def display_notes_statistics():
    """ノートの統計情報を表示 (サイドバーなどで使用可能)"""
    notes = load_notes()
    
    if not notes:
        return
    
    total_notes = len(notes)
    
    # 科目別カウント
    subject_count = {}
    for note in notes:
        subject = note['subject']
        subject_count[subject] = subject_count.get(subject, 0) + 1
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📝 ノート統計")
    st.sidebar.markdown(f"**全ノート数**: {total_notes}件")
    
    if subject_count:
        st.sidebar.markdown("**科目別**:")
        for subject, count in sorted(subject_count.items(), key=lambda x: x[1], reverse=True)[:5]:
            st.sidebar.markdown(f"- {subject}: {count}件")
