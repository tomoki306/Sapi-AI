"""
YouTube確認問題生成AI機能モジュール
YouTube動画の字幕から確認問題を自動生成
"""
import re
import json
import hashlib
import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi
from ai_config import client, MODEL_NAME, YOUTUBE_QUIZ_MAX_COMPLETION_TOKENS
from data import get_user_profile


def get_cached_transcript(video_id, languages_tuple):
    """字幕取得のキャッシュ版（重複リクエスト削減）"""
    # キャッシュキーの生成
    cache_key = hashlib.md5(f"{video_id}_{languages_tuple}".encode()).hexdigest()
    
    # セッションステートにキャッシュ
    if "transcript_cache" not in st.session_state:
        st.session_state.transcript_cache = {}
    
    if cache_key in st.session_state.transcript_cache:
        st.info("キャッシュから字幕を取得しました（高速）")
        return st.session_state.transcript_cache[cache_key]
    
    # キャッシュになければ取得
    result = _get_transcript_internal(video_id, languages_tuple)
    st.session_state.transcript_cache[cache_key] = result
    
    return result


def _get_transcript_internal(video_id, languages_tuple):
    """内部用：実際の字幕取得処理"""
    try:
        st.write(f"動画ID: `{video_id}`")
        
        api = YouTubeTranscriptApi()
        
        st.write("利用可能な字幕を確認中...")
        try:
            available_list = api.list(video_id)
            available_info = []
            for t in available_list:
                available_info.append(f"{t.language} ({t.language_code})")
            
            if available_info:
                st.info(f"利用可能: {', '.join(available_info)}")
        except Exception as list_err:
            st.warning(f"リスト取得スキップ: {str(list_err)}")
        
        st.write(f"字幕を取得中（優先順: {', '.join(languages_tuple)}）...")
        
        fetched = api.fetch(video_id, languages=list(languages_tuple))
        data = fetched.to_raw_data()
        
        if not data:
            raise Exception("字幕データが空です")
        
        full_text = ' '.join([item['text'] for item in data])
        
        st.success(f"字幕取得成功（{len(data)}件、{len(full_text)}文字）")
        
        return {
            "success": True,
            "text": full_text,
            "language": fetched.language_code if hasattr(fetched, 'language_code') else "unknown"
        }
        
    except Exception as e:
        error_msg = str(e)
        st.error(f"エラー: {error_msg}")
        
        if 'No transcripts' in error_msg or 'transcript' in error_msg.lower():
            return {
                "success": False,
                "error": "この動画には字幕が見つかりませんでした。字幕付きの動画をお試しください。"
            }
        elif 'video' in error_msg.lower() and ('unavailable' in error_msg.lower() or 'private' in error_msg.lower()):
            return {
                "success": False,
                "error": "この動画は非公開または利用できません。"
            }
        else:
            return {
                "success": False,
                "error": f"字幕取得エラー: {error_msg}"
            }


def extract_video_id(url):
    """YouTubeのURLから動画IDを抽出（改良版）"""
    patterns = [
        r'(?:youtube\.com\/watch\?v=)([a-zA-Z0-9_-]{11})',
        r'(?:youtu\.be\/)([a-zA-Z0-9_-]{11})',
        r'(?:youtube\.com\/embed\/)([a-zA-Z0-9_-]{11})',
        r'(?:youtube\.com\/v\/)([a-zA-Z0-9_-]{11})',
        r'(?:youtube\.com\/shorts\/)([a-zA-Z0-9_-]{11})'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    # URLではなく直接IDが渡された場合（最初の11文字のみ抽出）
    if re.match(r'^[a-zA-Z0-9_-]{11}', url):
        return url[:11]
    
    return None


def get_youtube_transcript(video_id, languages=('ja', 'en')):
    """YouTube動画の字幕を取得（キャッシュ対応版）"""
    return get_cached_transcript(video_id, languages)


def generate_quiz_from_transcript(transcript_text, num_questions=5, difficulty="初級"):
    """トランスクリプトから確認問題を生成（難易度対応強化版）"""
    
    # ユーザープロフィールの取得
    user_profile = get_user_profile()
    profile_context = ""
    if user_profile.get("age") and user_profile.get("education_level"):
        profile_context = f"\n【対象者】{user_profile['age']}歳（{user_profile['education_level']}）\n"
    
    # 難易度別のプロンプトテンプレート
    difficulty_templates = {
        "初級": {
            "description": "基本的な用語や概念の理解を確認する問題",
            "question_types": "用語の定義、基本的な事実確認、簡単な理解度チェック",
            "complexity": "シンプルで直接的な問題文",
            "distractors": "明確に間違いとわかる選択肢"
        },
        "中級": {
            "description": "概念の応用や関連性を理解しているかを確認する問題",
            "question_types": "概念の応用、因果関係の理解、比較・分類",
            "complexity": "複数の概念を組み合わせた問題文",
            "distractors": "部分的に正しい選択肢で思考を促す"
        },
        "上級": {
            "description": "深い理解と批判的思考を要する高度な問題",
            "question_types": "分析・評価・総合、仮説検証、複雑な推論",
            "complexity": "多段階の思考が必要な問題文",
            "distractors": "高度な知識がないと区別が難しい選択肢"
        }
    }
    
    template = difficulty_templates.get(difficulty, difficulty_templates["中級"])
    
    prompt = f"""
以下はYouTubeの自動字幕テキストです。**誤字・脱字が含まれている可能性があります**が、文脈から正しい内容を推測して、{num_questions}問の確認問題を作成してください。

【重要】
- 音声認識の誤り（同音異義語の間違いなど）を文脈から推測して正しく理解してください
- 明らかな誤字は脳内で修正して問題を作成してください
- 専門用語や固有名詞の誤認識に注意してください

{profile_context}
【難易度】{difficulty}
【問題の特徴】{template['description']}
【問題タイプ】{template['question_types']}
【複雑さ】{template['complexity']}
【選択肢の作り方】{template['distractors']}

【字幕テキスト】
{transcript_text[:3000]}

【選択肢作成の重要ルール】
1. **正解の位置をランダム化**: 正解が常に最初や最後にならないよう、ランダムな位置に配置すること
   - パターン化を避けるため、各問題で異なる位置（0,1,2,3のいずれか）に正解を配置
   
2. **選択肢の長さを均等に**: 正解だけが極端に長い/短いことを避け、全選択肢の文字数を同程度（±5文字以内）にすること
   - 正解: 約30文字 → 誤答も28-32文字程度に調整
   - 長さで正解が推測されないように注意
   
3. **極端な表現を避ける**: 誤答に「絶対に」「必ず」「全く」「一切」などの極端な表現を使わないこと
   - ❌ 悪い誤答: 「全く関係ない」「絶対にありえない」
   - ✅ 良い誤答: 「部分的に関連するが、主要な観点では異なる」
   
4. **部分的に正しい誤答**: 完全に間違った情報ではなく、一部は正しいが重要な点で誤っている選択肢を含めること
   - ❌ 悪い誤答: 動画と全く無関係な情報
   - ✅ 良い誤答: 「AはBに影響するが、Cを経由する（実際はDを経由）」
   
5. **魅力的な誤答の作り方**: 
   - 動画内で言及された関連する内容を使う
   - 一般的な誤解や混同しやすい概念を利用する
   - 時系列や因果関係を少しずらす
   - 数値や固有名詞を微妙に変える

【選択肢の質を高めるコツ】
✅ 良い例:
問題: 「動画で説明された主要なプロセスは？」
- 選択肢1 (正解): 「データを収集し、前処理を行い、モデルを訓練する」（30文字）
- 選択肢2: 「データを収集し、直接モデルに入力して結果を得る」（28文字）
- 選択肢3: 「前処理を行い、データを検証してから分析する」（26文字）
- 選択肢4: 「モデルを訓練し、その後にデータを収集する」（24文字）

❌ 悪い例:
- 選択肢1 (正解): 「データを収集し、前処理を行い、モデルを訓練する」（30文字）
- 選択肢2: 「違う」（2文字） ← 短すぎる
- 選択肢3: 「全く関係ない手順」 ← 極端な表現
- 選択肢4: 「動画で説明されていない別のトピックについての詳細な説明文」 ← 長すぎる

【出力形式】
以下のJSON形式で出力してください：

{{
  "questions": [
    {{
      "question": "問題文",
      "options": ["選択肢1", "選択肢2", "選択肢3", "選択肢4"],
      "correct_answer": 2,
      "explanation": "解説文"
    }}
  ]
}}

- questionsは配列で、{num_questions}問の問題を含む
- optionsは4つの選択肢を含む配列（各選択肢の文字数は同程度にすること）
- correct_answerは正解の選択肢のインデックス（0-3）で、問題ごとにランダムな位置にすること
- explanationは正解の解説（なぜ他の選択肢が不正解かも簡潔に説明）

**重要**: JSON形式のみで出力し、余計な説明は含めないでください。
"""
    
    try:
        # GPT-5-mini向けに最適化（誤字認識と内容理解を同時に行うためmedium推論）
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "誤字を含む可能性のある字幕から正確な確認問題を作成します。文脈から正しい内容を推測してください。"},
                {"role": "user", "content": prompt}
            ],
            max_completion_tokens=YOUTUBE_QUIZ_MAX_COMPLETION_TOKENS,
            reasoning_effort="medium"
        )
        
        result = response.choices[0].message.content
        
        if "```json" in result:
            result = result.split("```json")[1].split("```")[0].strip()
        elif "```" in result:
            result = result.split("```")[1].split("```")[0].strip()
        
        quiz_data = json.loads(result)
        return {"success": True, "quiz": quiz_data}
    
    except json.JSONDecodeError as e:
        return {"success": False, "error": f"JSON解析エラー: {str(e)}", "raw_response": result}
    except Exception as e:
        return {"success": False, "error": f"問題生成エラー: {str(e)}"}


def display_youtube_quiz():
    """YouTube確認問題生成UIの表示"""
    st.subheader("YouTube動画から確認問題を生成")
    
    st.info("YouTube動画の字幕から自動的に確認問題を生成します（誤字は自動認識）")
    
    youtube_url = st.text_input(
        "YouTube動画のURLを入力してください",
        placeholder="https://www.youtube.com/watch?v=..."
    )
    
    col1, col2 = st.columns(2)
    with col1:
        num_questions = st.selectbox("問題数を選択", [3, 5, 10, 15], index=1)
    with col2:
        difficulty = st.selectbox("難易度を選択", ["初級", "中級", "上級"], index=1)
    
    # 生成ボタン
    generate_btn = st.button("確認問題を生成", type="primary")

    if generate_btn:
        if not youtube_url:
            st.warning("YouTube動画のURLを入力してください")
        else:
            video_id = extract_video_id(youtube_url)
            
            if not video_id:
                st.error("有効なYouTube URLを入力してください")
            else:
                with st.spinner("字幕を取得しています..."):
                    transcript_result = get_youtube_transcript(video_id)
                    
                    if not transcript_result["success"]:
                        st.error(f"{transcript_result['error']}")
                        st.info("この動画には字幕がない可能性があります。字幕付きの動画をお試しください。")
                    else:
                        st.success(f"字幕取得成功（言語: {transcript_result['language']}）")
                        
                        transcript_text = transcript_result["text"]
                        
                        with st.expander("取得した字幕を確認"):
                            st.text_area("字幕テキスト（最初の500文字）", transcript_text[:500] + "...", height=150)
                            st.caption("※自動字幕に誤字がある場合、AIが文脈から推測して問題を生成します")
                        
                        with st.spinner(f"{num_questions}問の確認問題を生成しています..."):
                            quiz_result = generate_quiz_from_transcript(transcript_text, num_questions, difficulty)
                            
                            if not quiz_result["success"]:
                                st.error(f"{quiz_result['error']}")
                                if "raw_response" in quiz_result:
                                    with st.expander("エラー詳細"):
                                        st.text(quiz_result["raw_response"])
                            else:
                                st.success("確認問題を生成しました")
                                
                                # 生成した問題をセッションに保存（再描画でも消えない）
                                st.session_state.quiz_data = quiz_result["quiz"]
                                # 回答も初期化
                                st.session_state.quiz_answers = {}

    # セッションに問題があれば常に表示
    quiz_data = st.session_state.get('quiz_data')
    if quiz_data:
        st.markdown("---")
        st.subheader("確認問題（保存済み）")
        
        # 各問題のUI（ユーザー選択をセッションに保存）
        for i, q in enumerate(quiz_data["questions"]):
            st.markdown(f"### 問題 {i+1}")
            st.write(q["question"])
            
            answer_key = f"q_{i}"
            selected = st.radio(
                "選択してください：",
                options=range(len(q["options"])),
                format_func=lambda x, opts=q["options"]: opts[x],
                key=answer_key
            )
            # 念のため手動でも保持
            st.session_state.quiz_answers[answer_key] = selected
            st.markdown("---")
        
        # 採点ボタン（常に表示）
        if st.button("採点する", type="primary"):
            st.markdown("---")
            st.subheader("採点結果")
            
            correct_count = 0
            total_questions = len(quiz_data["questions"])
            
            for i, q in enumerate(quiz_data["questions"]):
                answer_key = f"q_{i}"
                user_answer = st.session_state.quiz_answers.get(answer_key, -1)
                correct_answer = q["correct_answer"]
                
                is_correct = user_answer == correct_answer
                if is_correct:
                    correct_count += 1
                
                st.markdown(f"### 問題 {i+1}")
                if is_correct:
                    st.success("正解")
                else:
                    st.error("不正解")
                    st.info(f"正解: {q['options'][correct_answer]}")
                
                st.write(f"**解説:** {q['explanation']}")
                st.markdown("---")
            
            score_percentage = (correct_count / total_questions) * 100 if total_questions else 0
            st.markdown("### 総合結果")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("正解数", f"{correct_count} / {total_questions}")
            with col2:
                st.metric("正答率", f"{score_percentage:.1f}%")
            with col3:
                if score_percentage >= 80:
                    st.success("素晴らしい")
                elif score_percentage >= 60:
                    st.info("良い理解度です")
                else:
                    st.warning("復習をお勧めします")
