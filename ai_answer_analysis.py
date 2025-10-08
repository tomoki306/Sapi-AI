"""
解答分析AI機能モジュール
テスト・課題の解答を分析し、詳細なフィードバックを提供
"""
import base64
import streamlit as st
from PIL import Image
from ai_config import get_ai_response, client, MODEL_NAME, DEFAULT_MAX_COMPLETION_TOKENS, COMPLEX_REASONING_EFFORT, determine_reasoning_effort
from data import get_user_profile


def display_answer_analysis():
    """解答分析UIの表示"""
    st.subheader("テスト・課題の解答分析")
    
    file_type = st.radio("分析対象の種類", ["テスト解答用紙", "小テスト", "課題"])
    
    subject = st.text_input("科目名（任意）")
    
    uploaded_file = st.file_uploader(
        "解答用紙または課題ファイルをアップロード（任意）",
        type=["jpg", "jpeg", "png", "pdf"],
        help="画像があればOCRで自動的にテキスト抽出します。画像がなくても分析できます。"
    )

    file_bytes = None
    uploaded_mime = None

    if uploaded_file is not None:
        try:
            file_extension = uploaded_file.name.split('.')[-1].lower()

            if file_extension == 'pdf':
                st.info("PDFファイルがアップロードされました（自動OCRは行いません）。")
            else:
                file_bytes = uploaded_file.getvalue()
                uploaded_file.seek(0)

                image = Image.open(uploaded_file)
                st.image(image, caption="アップロードされた解答用紙（自動OCRは行いません）", use_container_width=True)

                if file_extension in ('jpg', 'jpeg'):
                    uploaded_mime = 'jpeg'
                elif file_extension == 'png':
                    uploaded_mime = 'png'
                else:
                    uploaded_mime = file_extension

        except Exception as e:
            st.error(f"ファイル処理エラー: {str(e)}")
    
    st.write("---")
    combined_description = st.text_area(
        "補足内容説明（任意）",
        help="問題や解答についての説明や補足を記入してください。画像をアップロードしても自動OCRは行われません。分析開始時に画像があると、画像も一緒に送信されます。",
        value=""
    )
    
    if st.button("分析開始"):
        has_content = combined_description.strip() != "" or uploaded_file is not None

        if not has_content:
            st.warning("補足内容の説明、または画像のいずれかを入力してください")
        else:
            with st.spinner("解答を分析しています..."):
                try:
                    all_input = []
                    if subject:
                        all_input.append(f"【科目】{subject}")
                    if combined_description:
                        all_input.append(f"【補足内容】{combined_description}")
                    
                    # ユーザープロフィールの取得
                    user_profile = get_user_profile()
                    tone_instruction = ""
                    if user_profile.get("age") and user_profile.get("education_level"):
                        all_input.append(f"【学習者】{user_profile['age']}歳（{user_profile['education_level']}）")
                        edu_level = user_profile["education_level"]
                        if edu_level in ["小学生", "中学生"]:
                            tone_instruction = "説明は優しく、わかりやすい言葉で、具体例を多く使ってください。"
                        elif edu_level == "高校生":
                            tone_instruction = "わかりやすさを保ちつつ、適度に専門用語も使って説明してください。"
                        elif edu_level in ["大学生", "大学院生"]:
                            tone_instruction = "論理的で専門的な説明を心がけ、学術的な観点も含めてください。"
                    
                    combined_input = "\n\n".join(all_input)
                    
                    # データ量に応じてreasoning_effortを動的に決定
                    input_length = len(combined_input)
                    reasoning_effort = determine_reasoning_effort(
                        input_length=input_length,
                        task_complexity="medium"  # 解答分析は中程度の複雑さ
                    )
                    
                    # デバッグ情報（開発時のみ表示）
                    if st.session_state.get('debug_mode', False):
                        st.info(f"📊 入力データ長: {input_length}文字 → reasoning_effort: {reasoning_effort}")

                    analysis_prompt = f"""
                    # 解答分析依頼

                    ## 基本情報
                    - 対象: {file_type}

                    ## 提供された情報
                    {combined_input}

                    ## 指示
                    {tone_instruction}
                    1) 最初に「結論（正解）」を簡潔に明示
                    2) 数学なら途中式をステップで
                    3) 解答の論理・理由を過不足なく
                    4) 誤り箇所と正しい考え方を具体的に
                    5) 学習改善の具体アドバイス
                    6) 最後に要点まとめ（箇条書き）
                    """
                    
                    if file_bytes is not None:
                        try:
                            b64 = base64.b64encode(file_bytes).decode('utf-8')
                            data_url = f"data:image/{uploaded_mime};base64,{b64}"

                            # GPT-5-mini向けに最適化
                            messages = [
                                {"role": "system", "content": "解答を詳細に分析し、建設的なフィードバックを提供します。"},
                                {"role": "user", "content": [
                                    {"type": "text", "text": analysis_prompt},
                                    {"type": "image_url", "image_url": {"url": data_url, "detail": "high"}}
                                ]}
                            ]

                            response = client.chat.completions.create(
                                model=MODEL_NAME,
                                messages=messages,
                                max_completion_tokens=DEFAULT_MAX_COMPLETION_TOKENS
                            )

                            analysis_result = response.choices[0].message.content

                        except Exception as e:
                            st.error(f"画像送信中にエラーが発生しました: {str(e)}")
                            # データ量に応じて動的に決定したreasoning_effortを使用
                            analysis_result = get_ai_response(
                                analysis_prompt,
                                system_content="解答を分析します。",
                                reasoning_effort=reasoning_effort
                            )
                    else:
                        # データ量に応じて動的に決定したreasoning_effortを使用
                        analysis_result = get_ai_response(
                            analysis_prompt,
                            system_content="解答を分析します。",
                            reasoning_effort=reasoning_effort
                        )
                    
                    st.subheader("解答分析結果")
                    st.write("（以下、生成された解答全文）")
                    st.markdown(analysis_result)
            
                except Exception as e:
                    st.error(f"エラーが発生しました: {str(e)}")
                    st.error("分析処理中に問題が発生しました。入力内容を見直すか、後でもう一度お試しください。")
