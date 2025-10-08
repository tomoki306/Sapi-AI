# grade_filters.py
"""
学習記録のフィルタリング・検索機能
期間、科目、タイプ、点数範囲、キーワードでのフィルタリングとソート機能
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import pandas as pd


def filter_grades_by_period(grades_data: Dict[str, List[Dict]], period: str, 
                           custom_start: Optional[str] = None, 
                           custom_end: Optional[str] = None) -> Dict[str, List[Dict]]:
    """
    期間で成績データをフィルタリング
    Args:
        grades_data: 成績データ辞書
        period: 期間（"今週", "今月", "3ヶ月", "6ヶ月", "1年", "全期間", "カスタム"）
        custom_start: カスタム期間の開始日（YYYY-MM-DD）
        custom_end: カスタム期間の終了日（YYYY-MM-DD）
    Returns:
        フィルタリングされた成績データ
    """
    if period == "全期間":
        return grades_data
    
    # 期間の計算
    today = datetime.now()
    
    if period == "今週":
        start_date = today - timedelta(days=today.weekday())
        end_date = today
    elif period == "今月":
        start_date = today.replace(day=1)
        end_date = today
    elif period == "3ヶ月":
        start_date = today - timedelta(days=90)
        end_date = today
    elif period == "6ヶ月":
        start_date = today - timedelta(days=180)
        end_date = today
    elif period == "1年":
        start_date = today - timedelta(days=365)
        end_date = today
    elif period == "カスタム" and custom_start and custom_end:
        start_date = datetime.strptime(custom_start, "%Y-%m-%d")
        end_date = datetime.strptime(custom_end, "%Y-%m-%d")
    else:
        return grades_data
    
    # フィルタリング
    filtered_data = {}
    for subject, grades_list in grades_data.items():
        filtered_grades = []
        for grade in grades_list:
            try:
                grade_date = datetime.strptime(grade.get('date', ''), "%Y-%m-%d")
                if start_date <= grade_date <= end_date:
                    filtered_grades.append(grade)
            except (ValueError, TypeError):
                continue
        
        if filtered_grades:
            filtered_data[subject] = filtered_grades
    
    return filtered_data


def filter_grades_by_subjects(grades_data: Dict[str, List[Dict]], 
                             selected_subjects: List[str]) -> Dict[str, List[Dict]]:
    """
    科目で成績データをフィルタリング
    Args:
        grades_data: 成績データ辞書
        selected_subjects: 選択された科目のリスト
    Returns:
        フィルタリングされた成績データ
    """
    if not selected_subjects or "すべて" in selected_subjects:
        return grades_data
    
    filtered_data = {}
    for subject in selected_subjects:
        if subject in grades_data:
            filtered_data[subject] = grades_data[subject]
    
    return filtered_data


def filter_grades_by_type(grades_data: Dict[str, List[Dict]], 
                         grade_types: List[str]) -> Dict[str, List[Dict]]:
    """
    タイプで成績データをフィルタリング
    Args:
        grades_data: 成績データ辞書
        grade_types: 選択されたタイプのリスト（"テスト", "課題"など）
    Returns:
        フィルタリングされた成績データ
    """
    if not grade_types or "すべて" in grade_types:
        return grades_data
    
    filtered_data = {}
    for subject, grades_list in grades_data.items():
        filtered_grades = [
            grade for grade in grades_list 
            if grade.get('type') in grade_types
        ]
        if filtered_grades:
            filtered_data[subject] = filtered_grades
    
    return filtered_data


def filter_grades_by_score_range(grades_data: Dict[str, List[Dict]], 
                                min_score: int = 0, 
                                max_score: int = 100) -> Dict[str, List[Dict]]:
    """
    点数範囲で成績データをフィルタリング
    Args:
        grades_data: 成績データ辞書
        min_score: 最小点数
        max_score: 最大点数
    Returns:
        フィルタリングされた成績データ
    """
    filtered_data = {}
    for subject, grades_list in grades_data.items():
        filtered_grades = [
            grade for grade in grades_list 
            if min_score <= grade.get('grade', 0) <= max_score
        ]
        if filtered_grades:
            filtered_data[subject] = filtered_grades
    
    return filtered_data


def search_grades_by_keyword(grades_data: Dict[str, List[Dict]], 
                            keyword: str) -> Dict[str, List[Dict]]:
    """
    キーワードで成績データを検索
    Args:
        grades_data: 成績データ辞書
        keyword: 検索キーワード
    Returns:
        検索結果の成績データ
    """
    if not keyword:
        return grades_data
    
    keyword_lower = keyword.lower()
    filtered_data = {}
    
    for subject, grades_list in grades_data.items():
        filtered_grades = []
        for grade in grades_list:
            # コメント、科目名、タイプで検索
            comment = grade.get('comment', '').lower()
            grade_type = grade.get('type', '').lower()
            subject_lower = subject.lower()
            
            if (keyword_lower in comment or 
                keyword_lower in grade_type or 
                keyword_lower in subject_lower):
                filtered_grades.append(grade)
        
        if filtered_grades:
            filtered_data[subject] = filtered_grades
    
    return filtered_data


def sort_grades(grades_data: Dict[str, List[Dict]], 
               sort_by: str = "date", 
               ascending: bool = False) -> Dict[str, List[Dict]]:
    """
    成績データをソート
    Args:
        grades_data: 成績データ辞書
        sort_by: ソート基準（"date", "grade", "type"）
        ascending: 昇順かどうか
    Returns:
        ソートされた成績データ
    """
    sorted_data = {}
    
    for subject, grades_list in grades_data.items():
        if sort_by == "date":
            sorted_grades = sorted(
                grades_list, 
                key=lambda x: x.get('date', ''), 
                reverse=not ascending
            )
        elif sort_by == "grade":
            sorted_grades = sorted(
                grades_list, 
                key=lambda x: x.get('grade', 0), 
                reverse=not ascending
            )
        elif sort_by == "type":
            sorted_grades = sorted(
                grades_list, 
                key=lambda x: x.get('type', ''), 
                reverse=not ascending
            )
        else:
            sorted_grades = grades_list
        
        sorted_data[subject] = sorted_grades
    
    return sorted_data


def apply_all_filters(grades_data: Dict[str, List[Dict]], 
                     filters: Dict[str, Any]) -> Dict[str, List[Dict]]:
    """
    すべてのフィルタを適用
    Args:
        grades_data: 成績データ辞書
        filters: フィルタ設定の辞書
            - period: 期間
            - custom_start: カスタム期間開始
            - custom_end: カスタム期間終了
            - subjects: 科目リスト
            - types: タイプリスト
            - min_score: 最小点数
            - max_score: 最大点数
            - keyword: 検索キーワード
            - sort_by: ソート基準
            - ascending: 昇順かどうか
    Returns:
        フィルタリング・ソートされた成績データ
    """
    result = grades_data.copy()
    
    # 期間フィルタ
    if 'period' in filters:
        result = filter_grades_by_period(
            result, 
            filters['period'],
            filters.get('custom_start'),
            filters.get('custom_end')
        )
    
    # 科目フィルタ
    if 'subjects' in filters:
        result = filter_grades_by_subjects(result, filters['subjects'])
    
    # タイプフィルタ
    if 'types' in filters:
        result = filter_grades_by_type(result, filters['types'])
    
    # 点数範囲フィルタ
    if 'min_score' in filters and 'max_score' in filters:
        result = filter_grades_by_score_range(
            result, 
            filters['min_score'], 
            filters['max_score']
        )
    
    # キーワード検索
    if 'keyword' in filters and filters['keyword']:
        result = search_grades_by_keyword(result, filters['keyword'])
    
    # ソート
    if 'sort_by' in filters:
        result = sort_grades(
            result, 
            filters['sort_by'], 
            filters.get('ascending', False)
        )
    
    return result


def convert_grades_to_dataframe(grades_data: Dict[str, List[Dict]]) -> pd.DataFrame:
    """
    成績データをDataFrameに変換
    Args:
        grades_data: 成績データ辞書
    Returns:
        pandas.DataFrame
    """
    all_grades = []
    
    for subject, grades_list in grades_data.items():
        for grade in grades_list:
            all_grades.append({
                '科目': subject,
                '日付': grade.get('date', ''),
                'タイプ': grade.get('type', ''),
                '点数': grade.get('grade', 0),
                '重み': grade.get('weight', 1.0),
                'コメント': grade.get('comment', '')
            })
    
    if all_grades:
        return pd.DataFrame(all_grades)
    else:
        return pd.DataFrame(columns=['科目', '日付', 'タイプ', '点数', '重み', 'コメント'])


def get_filter_statistics(grades_data: Dict[str, List[Dict]]) -> Dict[str, Any]:
    """
    フィルタリング結果の統計情報を取得
    Args:
        grades_data: 成績データ辞書
    Returns:
        統計情報の辞書
    """
    total_records = sum(len(grades) for grades in grades_data.values())
    
    if total_records == 0:
        return {
            'total_records': 0,
            'subjects_count': 0,
            'average_score': 0.0,
            'max_score': 0,
            'min_score': 0,
            'test_count': 0,
            'assignment_count': 0
        }
    
    all_scores = []
    test_count = 0
    assignment_count = 0
    
    for grades_list in grades_data.values():
        for grade in grades_list:
            all_scores.append(grade.get('grade', 0))
            if grade.get('type') == 'テスト':
                test_count += 1
            elif grade.get('type') == '課題':
                assignment_count += 1
    
    return {
        'total_records': total_records,
        'subjects_count': len(grades_data),
        'average_score': round(sum(all_scores) / len(all_scores), 1) if all_scores else 0.0,
        'max_score': max(all_scores) if all_scores else 0,
        'min_score': min(all_scores) if all_scores else 0,
        'test_count': test_count,
        'assignment_count': assignment_count
    }
