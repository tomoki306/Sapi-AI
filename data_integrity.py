# data_integrity.py
"""
データ整合性チェック機能
JSONファイル破損時の自動修復、データ構造の検証、不正データの修正
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Tuple
import streamlit as st


class DataIntegrityManager:
    """データ整合性管理クラス"""
    
    def __init__(self):
        self.issues_found = []
        self.repairs_made = []
    
    def check_and_repair_all_data(self) -> Tuple[List[str], List[str]]:
        """
        全データの整合性チェックと修復
        Returns:
            Tuple[List[str], List[str]]: (見つかった問題, 修復内容)
        """
        self.issues_found = []
        self.repairs_made = []
        
        # セッションステートのデータをチェック
        self._check_grades_data()
        self._check_subjects_data()
        self._check_progress_data()
        self._check_goals_data()
        self._check_reminders_data()
        
        # JSONファイルの整合性もチェック
        self._check_json_files()
        
        return self.issues_found, self.repairs_made
    
    def _check_grades_data(self):
        """成績データの整合性チェック"""
        if 'grades' not in st.session_state:
            st.session_state.grades = {}
            self.repairs_made.append("成績データを初期化しました")
            return
        
        if not isinstance(st.session_state.grades, dict):
            st.session_state.grades = {}
            self.repairs_made.append("破損した成績データを修復しました")
            return
        
        for subject, grades_list in list(st.session_state.grades.items()):
            if not isinstance(grades_list, list):
                st.session_state.grades[subject] = []
                self.repairs_made.append(f"科目「{subject}」の成績データを修復しました")
                continue
            
            # 各成績レコードをチェック
            repaired_grades = []
            for grade_record in grades_list:
                if isinstance(grade_record, dict):
                    repaired_record = self._repair_grade_record(grade_record, subject)
                    repaired_grades.append(repaired_record)
                else:
                    self.repairs_made.append(f"科目「{subject}」の破損した成績レコードを削除しました")
            
            st.session_state.grades[subject] = repaired_grades
    
    def _repair_grade_record(self, record: Dict, subject: str) -> Dict:
        """個別の成績レコードを修復"""
        repaired = record.copy()
        
        # 成績値のチェック
        if 'grade' not in repaired or repaired['grade'] is None:
            repaired['grade'] = 0
            self.repairs_made.append(f"科目「{subject}」の成績値を0に設定しました")
        else:
            try:
                grade_value = float(repaired['grade'])
                if grade_value < 0:
                    repaired['grade'] = 0
                    self.repairs_made.append(f"科目「{subject}」の負の成績を0に修正しました")
                elif grade_value > 100:
                    repaired['grade'] = 100
                    self.repairs_made.append(f"科目「{subject}」の成績を100に制限しました")
                else:
                    repaired['grade'] = int(grade_value)
            except (ValueError, TypeError):
                repaired['grade'] = 0
                self.repairs_made.append(f"科目「{subject}」の不正な成績値を0に修正しました")
        
        # 日付のチェック
        if 'date' not in repaired or not repaired['date']:
            repaired['date'] = datetime.now().strftime('%Y-%m-%d')
            self.repairs_made.append(f"科目「{subject}」の日付を今日に設定しました")
        else:
            try:
                # 文字列の日付をdatetimeに変換して検証
                if isinstance(repaired['date'], str):
                    datetime.strptime(repaired['date'], '%Y-%m-%d')
            except ValueError:
                repaired['date'] = datetime.now().strftime('%Y-%m-%d')
                self.repairs_made.append(f"科目「{subject}」の不正な日付を今日に修正しました")
        
        # タイプのチェック
        if 'type' not in repaired:
            repaired['type'] = 'テスト'
        elif repaired['type'] not in ['テスト', '課題']:
            repaired['type'] = 'テスト'
            self.repairs_made.append(f"科目「{subject}」の不正なタイプを修正しました")
        
        # 重みのチェック
        if 'weight' not in repaired:
            repaired['weight'] = 1.0
        else:
            try:
                weight_value = float(repaired['weight'])
                if weight_value <= 0:
                    repaired['weight'] = 1.0
                    self.repairs_made.append(f"科目「{subject}」の重みを1.0に修正しました")
                else:
                    repaired['weight'] = weight_value
            except (ValueError, TypeError):
                repaired['weight'] = 1.0
                self.repairs_made.append(f"科目「{subject}」の不正な重み値を1.0に修正しました")
        
        # コメントのチェック
        if 'comment' not in repaired:
            repaired['comment'] = ''
        
        return repaired
    
    def _check_subjects_data(self):
        """科目データの整合性チェック"""
        if 'subjects' not in st.session_state:
            st.session_state.subjects = []
            self.repairs_made.append("科目データを初期化しました")
            return
        
        if not isinstance(st.session_state.subjects, list):
            st.session_state.subjects = []
            self.repairs_made.append("破損した科目データを修復しました")
            return
        
        # 重複する科目名と不正な科目名をチェック
        seen_subjects = set()
        unique_subjects = []
        
        for subject in st.session_state.subjects:
            if not isinstance(subject, str) or not subject.strip():
                self.repairs_made.append("空または不正な科目名を削除しました")
                continue
            
            subject = subject.strip()
            if subject not in seen_subjects:
                seen_subjects.add(subject)
                unique_subjects.append(subject)
            else:
                self.repairs_made.append(f"重複する科目「{subject}」を削除しました")
        
        st.session_state.subjects = unique_subjects
    
    def _check_progress_data(self):
        """進捗データの整合性チェック"""
        if 'progress' not in st.session_state:
            st.session_state.progress = {}
            self.repairs_made.append("進捗データを初期化しました")
            return
        
        if not isinstance(st.session_state.progress, dict):
            st.session_state.progress = {}
            self.repairs_made.append("破損した進捗データを修復しました")
            return
        
        # 各科目の進捗データをチェック
        for subject in list(st.session_state.progress.keys()):
            progress_list = st.session_state.progress[subject]
            
            if not isinstance(progress_list, list):
                st.session_state.progress[subject] = []
                self.repairs_made.append(f"科目「{subject}」の進捗データを修復しました")
                continue
            
            # 各進捗レコードをチェック
            repaired_progress = []
            for progress_record in progress_list:
                if isinstance(progress_record, dict):
                    # 学習時間のチェック
                    if 'study_time' not in progress_record:
                        progress_record['study_time'] = 0.0
                    else:
                        try:
                            time_value = float(progress_record['study_time'])
                            if time_value < 0:
                                progress_record['study_time'] = 0.0
                                self.repairs_made.append(f"科目「{subject}」の負の学習時間を0に修正しました")
                            elif time_value > 24:
                                progress_record['study_time'] = 24.0
                                self.repairs_made.append(f"科目「{subject}」の学習時間を24時間に制限しました")
                            else:
                                progress_record['study_time'] = time_value
                        except (ValueError, TypeError):
                            progress_record['study_time'] = 0.0
                            self.repairs_made.append(f"科目「{subject}」の不正な学習時間を0に修正しました")
                    
                    repaired_progress.append(progress_record)
                else:
                    self.repairs_made.append(f"科目「{subject}」の破損した進捗レコードを削除しました")
            
            st.session_state.progress[subject] = repaired_progress
    
    def _check_goals_data(self):
        """目標データの整合性チェック"""
        if 'goals' not in st.session_state:
            st.session_state.goals = []
            self.repairs_made.append("目標データを初期化しました")
            return
        
        from data import normalize_goals_data

        raw_goals = st.session_state.goals

        try:
            normalized_goals = normalize_goals_data(raw_goals)
        except Exception:
            st.session_state.goals = []
            self.repairs_made.append("破損した目標データを初期化しました")
            return

        if not isinstance(raw_goals, list):
            self.repairs_made.append("目標データを最新フォーマットに変換しました")
        elif len(normalized_goals) < len(raw_goals):
            self.repairs_made.append("不正な目標データを削除しました")

        st.session_state.goals = normalized_goals
    
    def _check_reminders_data(self):
        """リマインダーデータの整合性チェック"""
        if 'reminders' not in st.session_state:
            st.session_state.reminders = []
            self.repairs_made.append("リマインダーデータを初期化しました")
            return
        
        if not isinstance(st.session_state.reminders, list):
            st.session_state.reminders = []
            self.repairs_made.append("破損したリマインダーデータを修復しました")
            return
        
        # 各リマインダーをチェック
        valid_reminders = []
        for reminder in st.session_state.reminders:
            if isinstance(reminder, dict) and 'content' in reminder and reminder['content']:
                # 日時のチェック
                if 'datetime' in reminder:
                    try:
                        datetime.strptime(reminder['datetime'], '%Y-%m-%d %H:%M')
                    except ValueError:
                        try:
                            datetime.strptime(reminder['datetime'], '%Y-%m-%d')
                        except ValueError:
                            self.repairs_made.append("不正なリマインダー日時を削除しました")
                            continue
                
                valid_reminders.append(reminder)
            else:
                self.repairs_made.append("不正なリマインダーデータを削除しました")
        
        st.session_state.reminders = valid_reminders
    
    def _check_json_files(self):
        """JSONファイルの整合性チェック"""
        json_files = [
            'subjects.json',
            'grades.json',
            'progress.json',
            'reminders.json',
            'user_profile.json'
        ]
        
        for filename in json_files:
            if os.path.exists(filename):
                try:
                    with open(filename, 'r', encoding='utf-8') as f:
                        json.load(f)
                    # ファイルが正常に読み込めた場合は問題なし
                except json.JSONDecodeError:
                    self.issues_found.append(f"{filename}が破損しています")
                    # 空のデータで初期化
                    self._create_empty_json_file(filename)
                    self.repairs_made.append(f"{filename}を初期化しました")
                except Exception as e:
                    self.issues_found.append(f"{filename}の読み込みでエラー: {str(e)}")
    
    def _create_empty_json_file(self, filename: str):
        """空のJSONファイルを作成"""
        default_data = {}
        if filename == 'subjects.json':
            default_data = []
        elif filename == 'grades.json':
            default_data = {}
        elif filename == 'progress.json':
            default_data = {}
        elif filename == 'reminders.json':
            default_data = []
        elif filename == 'user_profile.json':
            default_data = {"name": "", "age": "", "education_level": ""}
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(default_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.issues_found.append(f"{filename}の作成に失敗: {str(e)}")


def display_data_integrity_check():
    """データ整合性チェックの結果を表示（データ管理画面用）"""
    st.subheader("🔧 データ整合性チェック")
    
    if st.button("データ整合性チェックを実行", type="primary"):
        with st.spinner("データをチェック中..."):
            manager = DataIntegrityManager()
            issues, repairs = manager.check_and_repair_all_data()
        
        if repairs:
            st.success("データの修復が完了しました！")
            with st.expander("修復内容を確認", expanded=True):
                for repair in repairs:
                    st.info(f"✅ {repair}")
        
        if issues:
            st.warning("以下の問題が見つかりました")
            with st.expander("問題の詳細", expanded=True):
                for issue in issues:
                    st.error(f"⚠️ {issue}")
        
        if not issues and not repairs:
            st.success("データに問題は見つかりませんでした！")


def auto_check_on_startup():
    """アプリ起動時の自動チェック（静かに実行）"""
    if 'data_integrity_checked' not in st.session_state:
        manager = DataIntegrityManager()
        issues, repairs = manager.check_and_repair_all_data()
        
        st.session_state.data_integrity_checked = True
        
        # 重要な問題があった場合のみ通知
        if repairs:
            st.session_state.data_repairs_count = len(repairs)
        if issues:
            st.session_state.data_issues_count = len(issues)
