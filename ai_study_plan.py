"""
学習計画作成AI機能モジュール
個別最適化された学習計画の生成
"""
import streamlit as st
from datetime import datetime
from ai_config import get_ai_response, call_api_with_retry, DEFAULT_MAX_COMPLETION_TOKENS, COMPLEX_REASONING_EFFORT
from data import get_user_profile


def generate_study_plan(subject, current_level, target_level, target_date, weekly_hours):
    """AIによる学習計画の生成
    
    Args:
        subject: 科目名
        current_level: 現在のレベル（例: "初心者", "中級者"）
        target_level: 目標レベル（例: "中級者", "上級者"）
        target_date: 目標達成日
        weekly_hours: 週あたりの学習時間
    
    Returns:
        str: 生成された学習計画
    """
    try:
        # ユーザープロフィールを取得
        user_profile = get_user_profile()
        age = user_profile.get('age', '不明')
        education_level = user_profile.get('education_level', '不明')
        
        # 日数を計算
        today = datetime.now()
        target = datetime.strptime(target_date, "%Y-%m-%d")
        days_remaining = (target - today).days
        weeks = max(1, days_remaining // 7)
        
        # プロンプト作成（GPT-5-mini向けに詳細化）
        prompt = f"""【学習者プロフィール】
年齢: {age}歳
現在の学歴/学習段階: {education_level}

【学習計画の要件】
科目: {subject}
現在のレベル: {current_level}
目標レベル: {target_level}
目標達成日: {target_date}（約{weeks}週間）
週あたりの学習時間: {weekly_hours}時間

上記の学習者の年齢と学習段階に最適化された、実践的で効果的な学習計画を作成してください。

以下の形式で回答してください：

## 📋 全体目標
（学習者の年齢と学歴を考慮した、明確で達成可能な目標を1-2文で記載）

## 📅 週次学習計画
（第1週から第{weeks}週まで、各週ごとに以下を記載）
- **第X週**: [学習内容] - [重点分野] - [達成目標]

## 💡 効果的な学習のコツ
（学習者の年齢と学習段階に適した具体的な学習方法を4-5個、箇条書きで）

## ✅ 中間チェックポイント
（学習の進捗を確認するための重要なマイルストーンを3-4個）

学習者の年齢（{age}歳）と学歴（{education_level}）を十分に考慮し、理解しやすく実践的な内容にしてください。"""
        
        # AIレスポンス生成（GPT-5推論モデル用に最適化）
        # 学習計画作成は複雑な計画タスクなのでreasoning_effort='medium'を使用
        response = call_api_with_retry(
            lambda: get_ai_response(
                prompt,
                system_content=f"あなたは{education_level}の学習者向けに個別最適化された学習計画を作成する専門的な教育アドバイザーです。年齢や学習段階に配慮した、実践的で効果的な指導を提供してください。",
                max_tokens=DEFAULT_MAX_COMPLETION_TOKENS,
                reasoning_effort=COMPLEX_REASONING_EFFORT
            )
        )
        
        return response
        
    except Exception as e:
        st.error(f"学習計画の生成に失敗しました: {str(e)}")
        return None


def display_study_planning_in_ai():
    """AI機能内での学習計画作成UI - planning.pyの機能を使用"""
    from planning import display_study_planning
    
    # planning.pyの完全な機能を使用
    display_study_planning()
