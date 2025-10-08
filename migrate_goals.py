"""
データ移行スクリプト
旧形式の目標データを最新のリスト形式に一括変換します。

使用方法:
    python migrate_goals.py

このスクリプトは一度だけ実行してください。
"""

import json
import os
import shutil
from datetime import datetime
from typing import Any, Dict, List


def _normalize_goal_record(subject: str, goal_type: str, payload: Any) -> Dict[str, Any]:
    """個別の目標レコードを正規化"""
    if isinstance(payload, dict):
        goal_text = payload.get('goal', '')
        deadline = payload.get('deadline', '')
        status = payload.get('status', '進行中')
    elif isinstance(payload, str):
        goal_text = payload
        deadline = ''
        status = '進行中'
    else:
        return {}

    return {
        'subject': subject,
        'goal_type': goal_type,
        'goal': goal_text,
        'deadline': deadline,
        'status': status
    }


def normalize_goals_data_legacy(data: Any) -> List[Dict[str, Any]]:
    """様々なフォーマットの目標データを統一フォーマットへ変換（レガシー版）"""
    normalized: List[Dict[str, Any]] = []

    if isinstance(data, list):
        # すでにリスト形式の場合
        for item in data:
            if isinstance(item, dict):
                subject = item.get('subject') or item.get('course') or "不明な科目"
                goal_type = item.get('goal_type') or item.get('type') or '短期'
                payload = {
                    'goal': item.get('goal') or item.get('title') or item.get('description') or "",
                    'deadline': item.get('deadline', ''),
                    'status': item.get('status', '進行中')
                }
                record = _normalize_goal_record(subject, goal_type, payload)
            else:
                record = _normalize_goal_record("不明な科目", '短期', item)

            if record:
                normalized.append(record)

    elif isinstance(data, dict):
        # 辞書形式の場合（旧形式）
        for subject, goal_types in data.items():
            if not isinstance(goal_types, dict):
                continue
            for goal_type, goals_list in goal_types.items():
                if not isinstance(goals_list, list):
                    continue
                for goal_payload in goals_list:
                    record = _normalize_goal_record(subject, goal_type, goal_payload)
                    if record:
                        normalized.append(record)

    return normalized


def migrate_goals_to_latest_format():
    """旧形式のデータを最新形式に一括変換"""
    goals_file = 'goals.json'
    
    if not os.path.exists(goals_file):
        print("⚠️ goals.json が見つかりません。移行は不要です。")
        return
    
    # バックアップを作成
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f'goals_backup_{timestamp}.json'
    shutil.copy(goals_file, backup_file)
    print(f"✅ バックアップを作成しました: {backup_file}")
    
    # 既存データを読み込み
    with open(goals_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # データ形式を確認
    if isinstance(data, list):
        # すでにリスト形式かチェック
        if all(isinstance(item, dict) and 'subject' in item and 'goal' in item for item in data):
            print("✅ データはすでに最新形式です。移行は不要です。")
            # バックアップを削除
            os.remove(backup_file)
            return
    
    # 正規化を実行
    print("🔄 データ移行中...")
    normalized = normalize_goals_data_legacy(data)
    
    # 最新形式で保存
    with open(goals_file, 'w', encoding='utf-8') as f:
        json.dump(normalized, f, ensure_ascii=False, indent=4)
    
    print(f"✅ 目標データを最新フォーマットに移行しました ({len(normalized)}件)")
    print(f"   元のデータは {backup_file} に保存されています")


if __name__ == "__main__":
    print("=" * 60)
    print("目標データ移行スクリプト")
    print("=" * 60)
    
    migrate_goals_to_latest_format()
    
    print("\n移行が完了しました!")
    print("問題がなければ、このスクリプトは削除してかまいません。")
