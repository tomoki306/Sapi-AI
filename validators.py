# validators.py
"""
データ検証・エラー防止機能
入力値の検証、重複チェック、必須項目チェックを実装
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List


class ValidationError(Exception):
    """カスタム検証エラー"""
    pass


def validate_grade(grade: Any) -> int:
    """
    成績の検証 (0-100の範囲)
    Args:
        grade: 成績値
    Returns:
        int: 検証済みの成績
    Raises:
        ValidationError: 範囲外の値の場合
    """
    try:
        grade_int = int(float(grade))
    except (ValueError, TypeError):
        raise ValidationError("成績は数値で入力してください")
    
    if not 0 <= grade_int <= 100:
        raise ValidationError("成績は0〜100の範囲で入力してください")
    
    return grade_int


def validate_study_time(study_time: Any) -> float:
    """
    学習時間の検証 (0-24時間)
    Args:
        study_time: 学習時間（時間）
    Returns:
        float: 検証済みの学習時間
    Raises:
        ValidationError: 負の値や24時間超の場合
    """
    try:
        time_float = float(study_time)
    except (ValueError, TypeError):
        raise ValidationError("学習時間は数値で入力してください")
    
    if time_float < 0:
        raise ValidationError("学習時間は0以上で入力してください")
    
    if time_float > 24:
        raise ValidationError("学習時間は24時間以内で入力してください")
    
    return time_float


def validate_subject_name(name: Any) -> str:
    """
    科目名の検証
    Args:
        name: 科目名
    Returns:
        str: 検証済みの科目名
    Raises:
        ValidationError: 空白や特殊文字、長すぎる場合
    """
    if not name or not str(name).strip():
        raise ValidationError("科目名を入力してください")
    
    name_str = str(name).strip()
    
    if len(name_str) > 50:
        raise ValidationError("科目名は50文字以内で入力してください")
    
    # 特殊文字のチェック（<>"'\）
    forbidden_chars = ['<', '>', '"', "'", '\\']
    for char in forbidden_chars:
        if char in name_str:
            raise ValidationError(f"科目名に使用できない文字が含まれています: {char}")
    
    return name_str


def validate_date(date_input: Any, allow_future_years: int = 10) -> datetime:
    """
    日付の検証
    Args:
        date_input: 日付（文字列またはdatetimeオブジェクト）
        allow_future_years: 未来の何年先まで許可するか
    Returns:
        datetime: 検証済みの日付
    Raises:
        ValidationError: 不正な日付の場合
    """
    if isinstance(date_input, datetime):
        target_date = date_input
    elif isinstance(date_input, str):
        try:
            target_date = datetime.strptime(date_input, "%Y-%m-%d")
        except ValueError:
            try:
                target_date = datetime.strptime(date_input, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                raise ValidationError("日付の形式が正しくありません（YYYY-MM-DD）")
    else:
        raise ValidationError("日付の形式が正しくありません")
    
    # 未来すぎる日付のチェック
    max_future_date = datetime.now() + timedelta(days=allow_future_years * 365)
    if target_date > max_future_date:
        raise ValidationError(f"{allow_future_years}年以上先の日付は設定できません")
    
    return target_date


def validate_reminder_content(content: Any) -> str:
    """
    リマインダー内容の検証
    Args:
        content: リマインダーの内容
    Returns:
        str: 検証済みのリマインダー内容
    Raises:
        ValidationError: 空の内容の場合
    """
    if not content or not str(content).strip():
        raise ValidationError("リマインダーの内容を入力してください")
    
    content_str = str(content).strip()
    
    if len(content_str) > 500:
        raise ValidationError("リマインダーの内容は500文字以内で入力してください")
    
    return content_str


def validate_weight(weight: Any) -> float:
    """
    重みの検証
    Args:
        weight: 重み値
    Returns:
        float: 検証済みの重み
    Raises:
        ValidationError: 不正な重みの場合
    """
    try:
        weight_float = float(weight)
    except (ValueError, TypeError):
        raise ValidationError("重みは数値で入力してください")
    
    if weight_float <= 0:
        raise ValidationError("重みは0より大きい値で入力してください")
    
    if weight_float > 100:
        raise ValidationError("重みは100以下で入力してください")
    
    return weight_float


def check_duplicate_subject(subject_name: str, existing_subjects: List[str]) -> bool:
    """
    科目名の重複チェック
    Args:
        subject_name: チェックする科目名
        existing_subjects: 既存の科目名リスト
    Returns:
        bool: 重複している場合True
    """
    return subject_name in existing_subjects


def check_duplicate_grade_record(subject: str, date: str, existing_grades: Dict) -> bool:
    """
    同じ日時の成績記録の重複チェック（警告レベル）
    Args:
        subject: 科目名
        date: 記録日（YYYY-MM-DD形式）
        existing_grades: 既存の成績記録辞書
    Returns:
        bool: 重複している場合True
    """
    if subject not in existing_grades:
        return False
    
    for grade_record in existing_grades[subject]:
        if grade_record.get('date') == date:
            return True
    
    return False


def validate_goal_content(goal: Dict[str, Any]) -> Dict[str, Any]:
    """
    学習目標の検証
    Args:
        goal: 目標の辞書
    Returns:
        Dict: 検証済みの目標
    Raises:
        ValidationError: 不正な目標の場合
    """
    validated_goal = {}
    
    # 目標タイトルの検証
    if 'title' not in goal or not goal['title']:
        raise ValidationError("目標のタイトルを入力してください")
    validated_goal['title'] = str(goal['title']).strip()
    
    # 期限の検証
    if 'deadline' in goal and goal['deadline']:
        validated_goal['deadline'] = validate_date(goal['deadline'])
    
    # 目標値の検証（数値目標の場合）
    if 'target_value' in goal and goal['target_value'] is not None:
        try:
            validated_goal['target_value'] = float(goal['target_value'])
        except (ValueError, TypeError):
            raise ValidationError("目標値は数値で入力してください")
    
    # その他のフィールドをコピー
    for key, value in goal.items():
        if key not in validated_goal:
            validated_goal[key] = value
    
    return validated_goal


def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> None:
    """
    必須フィールドの一括チェック
    Args:
        data: チェックするデータ
        required_fields: 必須フィールドのリスト
    Raises:
        ValidationError: 必須フィールドが不足している場合
    """
    missing_fields = []
    for field in required_fields:
        if field not in data or data[field] is None or (isinstance(data[field], str) and not data[field].strip()):
            missing_fields.append(field)
    
    if missing_fields:
        raise ValidationError(f"以下の必須項目が入力されていません: {', '.join(missing_fields)}")


def safe_int(value: Any, default: int = 0) -> int:
    """安全に整数に変換"""
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return default


def safe_float(value: Any, default: float = 0.0) -> float:
    """安全に浮動小数点数に変換"""
    try:
        return float(value)
    except (ValueError, TypeError):
        return default
