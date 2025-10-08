# data.py

import streamlit as st
from datetime import datetime
import json
import os
from typing import Any, Dict, List

def initialize_session_state():
    # セッションステートを初期化する関数
    if 'subjects' not in st.session_state:
        load_subjects()  # 科目データを読み込む
    if 'goals' not in st.session_state:
        load_goals()  # 目標データを読み込む
    if 'progress' not in st.session_state:
        load_progress()  # 進捗データを読み込む
    if 'grades' not in st.session_state:
        load_grades()  # 成績データを読み込む
    if 'user_profile' not in st.session_state:
        load_user_profile()  # ユーザープロフィールを読み込む
    if 'reminders' not in st.session_state:
        load_reminders()  # リマインダーデータを読み込む
    if 'current_date' not in st.session_state:
        st.session_state.current_date = datetime.now().strftime("%Y-%m-%d")

def add_subject(subject):
    # 科目をセッションステートに追加する関数
    if subject and subject not in st.session_state.subjects:
        st.session_state.subjects.append(subject)
        save_subjects()  # 科目データを保存
        return True
    return False

def load_subjects():
    # 科目データをファイルから読み込む関数
    if os.path.exists('subjects.json'):
        with open('subjects.json', 'r', encoding='utf-8') as f:
            st.session_state.subjects = json.load(f)
    else:
        st.session_state.subjects = []

def save_subjects():
    # 科目データをファイルに保存する関数
    with open('subjects.json', 'w', encoding='utf-8') as f:
        json.dump(st.session_state.subjects, f, ensure_ascii=False, indent=4)

def add_goal(subject: str, goal_type: str, goal: str, *, deadline: str = '', status: str = '進行中') -> bool:
    """学習目標をセッションステートに追加する関数"""
    if not (subject and goal):
        return False

    goals_data = st.session_state.get('goals', [])
    normalized = normalize_goals_data(goals_data)
    normalized.append({
        'subject': subject,
        'goal_type': goal_type or '短期',
        'goal': goal,
        'deadline': deadline,
        'status': status or '進行中'
    })

    st.session_state.goals = normalized
    save_goals()  # 目標データを保存
    return True

def _normalize_goal_record(subject: str, goal_type: str, goal_payload: Any) -> Dict[str, Any] | None:
    """目標レコードを統一フォーマットに変換"""
    subject = subject or "不明な科目"
    goal_type = goal_type or "短期"

    if isinstance(goal_payload, dict):
        goal_text = (
            goal_payload.get('goal')
            or goal_payload.get('title')
            or goal_payload.get('content')
            or ""
        )
        deadline = goal_payload.get('deadline', '')
        status = goal_payload.get('status') or goal_payload.get('state') or '進行中'
    else:
        goal_text = str(goal_payload).strip()
        deadline = ''
        status = '進行中'

    if not goal_text:
        return None

    return {
        'subject': subject,
        'goal_type': goal_type,
        'goal': goal_text,
        'deadline': deadline,
        'status': status
    }


def normalize_goals_data(data: Any) -> List[Dict[str, Any]]:
    """
    目標データの正規化（最新フォーマット専用）
    
    注意: このメソッドはリスト形式のみをサポートします。
    旧形式（辞書形式）のデータがある場合は、migrate_goals.py を実行してください。
    
    Args:
        data: 目標データ（リスト形式）
        
    Returns:
        正規化された目標データ
        
    Raises:
        ValueError: データがリスト形式でない場合
    """
    if not isinstance(data, list):
        from logger import log_error
        log_error(
            ValueError("目標データはリスト形式である必要があります"),
            "DATA_NORMALIZATION",
            details={"data_type": type(data).__name__}
        )
        raise ValueError(
            "目標データはリスト形式である必要があります。\n"
            "旧形式のデータを使用している場合は、migrate_goals.py を実行してください。"
        )
    
    # データの検証と正規化
    normalized: List[Dict[str, Any]] = []
    
    for i, item in enumerate(data):
        if not isinstance(item, dict):
            from logger import log_warning
            log_warning(f"目標データのインデックス {i} がdictではありません", "DATA_NORMALIZATION")
            continue
        
        # 必須フィールドのチェックと補完
        normalized_item = {
            'subject': item.get('subject', '不明な科目'),
            'goal_type': item.get('goal_type', '短期'),
            'goal': item.get('goal', ''),
            'deadline': item.get('deadline', ''),
            'status': item.get('status', '進行中')
        }
        
        normalized.append(normalized_item)
    
    return normalized



def load_goals():
    # 目標データをファイルから読み込む関数
    if os.path.exists('goals.json'):
        with open('goals.json', 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)
            normalized = normalize_goals_data(loaded_data)
            st.session_state.goals = normalized
    else:
        st.session_state.goals = []

def save_goals():
    # 目標データをファイルに保存する関数
    with open('goals.json', 'w', encoding='utf-8') as f:
        json.dump(st.session_state.goals, f, ensure_ascii=False, indent=4)

def record_progress(subject, study_time, task, motivation):
    # 進捗をセッションステートに記録する関数
    if subject and study_time and task:
        if subject not in st.session_state.progress:
            st.session_state.progress[subject] = []
        st.session_state.progress[subject].append({
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "time": study_time,
            "task": task,
            "motivation": motivation
        })
        save_progress()  # 進捗データを保存
        return True
    return False

def load_progress():
    # 進捗データをファイルから読み込む関数
    if os.path.exists('progress.json'):
        with open('progress.json', 'r', encoding='utf-8') as f:
            st.session_state.progress = json.load(f)
    else:
        st.session_state.progress = {}

def save_progress():
    # 進捗データをファイルに保存する関数
    with open('progress.json', 'w', encoding='utf-8') as f:
        json.dump(st.session_state.progress, f, ensure_ascii=False, indent=4)

def record_grade(subject, grade_type, grade, weight, comment):
    if 'grades' not in st.session_state:
        st.session_state.grades = {}
    if subject not in st.session_state.grades:
        st.session_state.grades[subject] = []
    st.session_state.grades[subject].append({
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "type": grade_type,
        "grade": grade,
        "weight": weight,
        "comment": comment
    })
    save_grades()  # 成績データを保存
    return True

def load_grades():
    # 成績データをファイルから読み込む関数
    if os.path.exists('grades.json'):
        with open('grades.json', 'r', encoding='utf-8') as f:
            st.session_state.grades = json.load(f)
    else:
        st.session_state.grades = {}

def save_grades():
    # 成績データをファイルに保存する関数
    with open('grades.json', 'w', encoding='utf-8') as f:
        json.dump(st.session_state.grades, f, ensure_ascii=False, indent=4)

def get_latest_grades():
    # 最新の成績データを返す
    latest_grades = {}
    for subject, grades in st.session_state.grades.items():
        if grades:
            latest_grades[subject] = grades[-1]['grade']
    return latest_grades

def get_total_study_time():
    # 総学習時間を返す
    total_study_time = {}
    for subject, progress in st.session_state.progress.items():
        total_time = sum(item['time'] for item in progress)
        total_study_time[subject] = total_time
    return total_study_time

def get_motivation_data():
    # 教科ごとの最新のやる気のデータを返す
    motivation_data = {}
    for subject, progress in st.session_state.progress.items():
        if progress:
            motivation_data[subject] = progress[-1].get('motivation', 'データなし')
    return motivation_data

def get_all_grades_data():
    all_grades = {}
    for subject, grades in st.session_state.grades.items():
        if grades:
            all_grades[subject] = [
                {
                    "date": g["date"],
                    "grade": g["grade"]
                }
                for g in grades
            ]
    return all_grades

# =============== ユーザープロフィール管理機能 ===============

def load_user_profile():
    """ユーザープロフィールをファイルから読み込む"""
    if os.path.exists('user_profile.json'):
        with open('user_profile.json', 'r', encoding='utf-8') as f:
            st.session_state.user_profile = json.load(f)
    else:
        # デフォルト値
        st.session_state.user_profile = {
            "age": None,
            "education_level": None,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": None
        }

def save_user_profile():
    """ユーザープロフィールをファイルに保存"""
    st.session_state.user_profile["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open('user_profile.json', 'w', encoding='utf-8') as f:
        json.dump(st.session_state.user_profile, f, ensure_ascii=False, indent=4)

def update_user_profile(age, education_level):
    """ユーザープロフィールを更新"""
    if age is not None and education_level:
        st.session_state.user_profile["age"] = age
        st.session_state.user_profile["education_level"] = education_level
        save_user_profile()
        return True
    return False

def get_user_profile():
    """ユーザープロフィールを取得"""
    if 'user_profile' not in st.session_state:
        load_user_profile()
    return st.session_state.user_profile

def get_education_levels():
    """学歴の選択肢を返す"""
    return ["小学生", "中学生", "高校生", "大学生", "大学院生"]

# =============== リマインダー管理機能 ===============

def load_reminders():
    """リマインダーをファイルから読み込む"""
    if os.path.exists('reminders.json'):
        with open('reminders.json', 'r', encoding='utf-8') as f:
            st.session_state.reminders = json.load(f)
    else:
        st.session_state.reminders = []

def save_reminders():
    """リマインダーをファイルに保存"""
    with open('reminders.json', 'w', encoding='utf-8') as f:
        json.dump(st.session_state.reminders, f, ensure_ascii=False, indent=4)

# =============== データ編集・削除機能 ===============

def delete_grades(subject, indices):
    """指定されたインデックスの成績データを削除"""
    if subject in st.session_state.grades:
        # インデックスを降順にソートして削除（後ろから削除することでインデックスのズレを防ぐ）
        for index in sorted(indices, reverse=True):
            if 0 <= index < len(st.session_state.grades[subject]):
                del st.session_state.grades[subject][index]
        save_grades()
        return True
    return False

def update_grade(subject, index, grade_type, grade, weight, comment):
    """指定されたインデックスの成績データを更新"""
    if subject in st.session_state.grades and 0 <= index < len(st.session_state.grades[subject]):
        st.session_state.grades[subject][index].update({
            "type": grade_type,
            "grade": grade,
            "weight": weight,
            "comment": comment
        })
        save_grades()
        return True
    return False

def delete_progress(subject, indices):
    """指定されたインデックスの進捗データを削除"""
    if subject in st.session_state.progress:
        for index in sorted(indices, reverse=True):
            if 0 <= index < len(st.session_state.progress[subject]):
                del st.session_state.progress[subject][index]
        save_progress()
        return True
    return False

def update_progress(subject, index, date, time, task, motivation):
    """指定されたインデックスの進捗データを更新"""
    if subject in st.session_state.progress and 0 <= index < len(st.session_state.progress[subject]):
        st.session_state.progress[subject][index].update({
            "date": date,
            "time": time,
            "task": task,
            "motivation": motivation
        })
        save_progress()
        return True
    return False

def delete_reminders(indices):
    """指定されたインデックスのリマインダーを削除"""
    try:
        with open('reminders.json', 'r', encoding='utf-8') as f:
            reminders = json.load(f)
        
        for index in sorted(indices, reverse=True):
            if 0 <= index < len(reminders):
                del reminders[index]
        
        with open('reminders.json', 'w', encoding='utf-8') as f:
            json.dump(reminders, f, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        st.error(f"リマインダーの削除に失敗しました: {str(e)}")
        return False

def update_reminder(index, subject, reminder_type, date, text):
    """指定されたインデックスのリマインダーを更新"""
    try:
        with open('reminders.json', 'r', encoding='utf-8') as f:
            reminders = json.load(f)
        
        if 0 <= index < len(reminders):
            reminders[index].update({
                "subject": subject,
                "type": reminder_type,
                "date": date,
                "text": text
            })
            
            with open('reminders.json', 'w', encoding='utf-8') as f:
                json.dump(reminders, f, ensure_ascii=False, indent=4)
            return True
    except Exception as e:
        st.error(f"リマインダーの更新に失敗しました: {str(e)}")
        return False
    return False

def delete_subject(subject):
    """科目と関連する全データを削除"""
    if subject in st.session_state.subjects:
        # 科目を削除
        st.session_state.subjects.remove(subject)
        save_subjects()
        
        # 関連する目標を削除
        if subject in st.session_state.goals:
            del st.session_state.goals[subject]
            save_goals()
        
        # 関連する進捗を削除
        if subject in st.session_state.progress:
            del st.session_state.progress[subject]
            save_progress()
        
        # 関連する成績を削除
        if subject in st.session_state.grades:
            del st.session_state.grades[subject]
            save_grades()
        
        return True
    return False