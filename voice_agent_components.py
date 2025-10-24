"""
音声エージェントコンポーネント
render_mini_voice_agent() の機能を分割して保守性を向上
"""

import os
import json
import tempfile
import uuid
import requests
import streamlit as st


def initialize_voice_agent():
    """音声エージェントの初期化処理"""
    # メッセージ履歴の初期化
    if "voice_agent_messages" not in st.session_state:
        st.session_state["voice_agent_messages"] = [
            {"role": "system", "content": "あなたは親切なAIアシスタントです。必ず日本語で回答してください。"}
        ]
    
    # 録音ボタンのバグ修正：完全に独立した状態管理
    if "recorder_session_id" not in st.session_state:
        st.session_state["recorder_session_id"] = str(uuid.uuid4())
    
    if "last_audio_data" not in st.session_state:
        st.session_state["last_audio_data"] = None
        
    if "recorder_reset_needed" not in st.session_state:
        st.session_state["recorder_reset_needed"] = False
    
    # 安定した文字起こし保存用キー
    if "last_transcription" not in st.session_state:
        st.session_state["last_transcription"] = ""


def get_azure_client():
    """Azure OpenAI クライアントの取得（音声認識・TTS対応）"""
    try:
        from openai import AzureOpenAI
    except Exception:
        st.warning("openai パッケージが未インストールです。'pip install openai' を実行してください。")
        return None, None, None, None, None, None, None
    
    # GPT用クライアント（メインのAzure OpenAI - East US 2）
    GPT_API_KEY = os.getenv("AZURE_OPENAI_KEY")
    GPT_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
    GPT_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-10-21")
    
    # 音声認識用クライアント（gpt-4o-mini-transcribe用）
    VOICE_API_KEY = os.getenv("AZURE_OPENAI_KEY")
    VOICE_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
    VOICE_API_VERSION = os.getenv("VOICE_AZURE_OPENAI_API_VERSION", "2024-06-01")
    
    # TTS用の設定（REST API用）
    TTS_API_KEY = os.getenv("VOICE_TTS_API_KEY", VOICE_API_KEY)  # 未設定の場合はVOICE_API_KEYを使用
    TTS_ENDPOINT = os.getenv("VOICE_TTS_ENDPOINT", VOICE_ENDPOINT)  # 未設定の場合はVOICE_ENDPOINTを使用
    TTS_API_VERSION = os.getenv("VOICE_TTS_API_VERSION", "2025-03-01-preview")
    
    # デバッグ情報（本番環境では削除推奨）
    if not GPT_API_KEY or not GPT_ENDPOINT:
        st.error("❌ GPT用の環境変数が設定されていません！")
        st.info(f"GPT API Key: {'設定済み' if GPT_API_KEY else '未設定'}")
        st.info(f"GPT Endpoint: {GPT_ENDPOINT if GPT_ENDPOINT else '未設定'}")
        return None, None, None, None, None, None, None
    
    if not VOICE_API_KEY or not VOICE_ENDPOINT:
        st.error("❌ 音声認識用の環境変数が設定されていません！")
        st.info(f"Voice API Key: {'設定済み' if VOICE_API_KEY else '未設定'}")
        st.info(f"Voice Endpoint: {VOICE_ENDPOINT if VOICE_ENDPOINT else '未設定'}")
        return None, None, None, None, None, None, None
    
    # ⚠️ 末尾スラッシュを削除（Azure OpenAI SDKでは不要）
    GPT_ENDPOINT = GPT_ENDPOINT.rstrip('/')
    VOICE_ENDPOINT = VOICE_ENDPOINT.rstrip('/')
    TTS_ENDPOINT = TTS_ENDPOINT.rstrip('/') if TTS_ENDPOINT else None
    
    try:
        # GPT用クライアント（East US 2）
        gpt_client = AzureOpenAI(
            api_key=GPT_API_KEY,
            azure_endpoint=GPT_ENDPOINT,
            api_version=GPT_API_VERSION,
        )
        
        # 音声認識用クライアント（gpt-4o-mini-transcribe）
        voice_client = AzureOpenAI(
            api_key=VOICE_API_KEY,
            azure_endpoint=VOICE_ENDPOINT,
            api_version=VOICE_API_VERSION,
        )
    except Exception as e:
        st.error(f"❌ Azure OpenAI クライアント初期化エラー: {e}")
        return None, None, None, None, None, None, None
    
    # デプロイメント名（.envから取得）
    GPT_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_MODEL", "gpt-5-mini")
    STT_DEPLOYMENT_NAME = os.getenv("VOICE_STT_DEPLOYMENT_NAME", "gpt-4o-mini-transcribe")
    TTS_DEPLOYMENT_NAME = os.getenv("VOICE_TTS_DEPLOYMENT_NAME", "gpt-4o-mini-tts")
    
    # TTS設定を辞書にまとめる
    tts_config = {
        "api_key": TTS_API_KEY,
        "endpoint": TTS_ENDPOINT,
        "api_version": TTS_API_VERSION,
        "deployment_name": TTS_DEPLOYMENT_NAME
    }
    
    return gpt_client, voice_client, GPT_DEPLOYMENT_NAME, STT_DEPLOYMENT_NAME, tts_config


def load_json_safe(path: str):
    """JSONファイルの安全な読み込み"""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def contains_any(text: str, keywords: list[str]) -> bool:
    """テキストに指定されたキーワードが含まれているかチェック"""
    text = text or ""
    return any((k in text) for k in keywords if k)


def build_rag_context(query: str) -> str:
    """RAGコンテキストの構築（関連するJSONデータを取得）"""
    base = os.path.dirname(__file__)
    subjects = load_json_safe(os.path.join(base, "subjects.json"))
    grades = load_json_safe(os.path.join(base, "grades.json"))
    progress = load_json_safe(os.path.join(base, "progress.json"))
    reminders = load_json_safe(os.path.join(base, "reminders.json"))
    
    q = query or ""
    subjects_in_query = []
    if isinstance(subjects, list):
        for s in subjects:
            if isinstance(s, str) and s and s in q:
                subjects_in_query.append(s)
    
    parts: list[str] = []
    
    # 常に科目一覧は付与（短いのでマッピングに役立つ）
    if subjects is not None:
        parts.append("[subjects]\n" + json.dumps(subjects, ensure_ascii=False, indent=2))
    
    # 成績
    if isinstance(grades, dict):
        pick = {}
        if subjects_in_query:
            for s in subjects_in_query:
                if s in grades and isinstance(grades[s], list):
                    pick[s] = grades[s][-5:]
        else:
            # 各科目の最新3件
            for s, arr in grades.items():
                if isinstance(arr, list):
                    pick[s] = arr[-3:]
        if pick:
            parts.append("[grades] (最新)\n" + json.dumps(pick, ensure_ascii=False, indent=2))
    
    # 進捗
    if isinstance(progress, dict):
        pick = {}
        if subjects_in_query:
            for s in subjects_in_query:
                if s in progress and isinstance(progress[s], list):
                    pick[s] = progress[s][-5:]
        else:
            for s, arr in progress.items():
                if isinstance(arr, list):
                    pick[s] = arr[-3:]
        if pick and contains_any(q, ["進捗", "時間", "学習", "モチベーション", "progress", "study"]):
            parts.append("[progress] (最新)\n" + json.dumps(pick, ensure_ascii=False, indent=2))
    
    # リマインダー
    if isinstance(reminders, list):
        pick = reminders
        if subjects_in_query:
            pick = [r for r in reminders if isinstance(r, dict) and r.get("subject") in subjects_in_query]
        if pick and contains_any(q, ["予定", "リマインダー", "締切", "試験", "reminder", "deadline", "exam"]):
            parts.append("[reminders]\n" + json.dumps(pick, ensure_ascii=False, indent=2))
    
    # 長すぎる場合は先頭を優先してカット
    ctx = "\n\n".join(parts)
    max_chars = 8000
    if len(ctx) > max_chars:
        ctx = ctx[:max_chars] + "\n... (truncated)"
    return ctx


def handle_voice_input(client, STT_DEPLOYMENT_NAME):
    """音声入力の処理"""
    try:
        from audio_recorder_streamlit import audio_recorder
    except Exception:
        st.warning("audio_recorder_streamlit が未インストールです。'pip install audio-recorder-streamlit' を実行してください。")
        return ""
    
    # 音声録音コンポーネント
    try:
        audio_bytes = audio_recorder(
            text="🎤 録音",
            recording_color="#ff4444",
            neutral_color="#6aa36f",
            icon_name="microphone",
            icon_size="1x",
            key=f"audio_recorder_{st.session_state['recorder_session_id']}"
        )
    except Exception as e:
        st.error(f"音声録音コンポーネントエラー: {e}")
        return ""
    
    # 音声認識処理（改良版 - 複数形式対応）
    transcribed_text = ""
    
    if audio_bytes and audio_bytes != st.session_state["last_audio_data"]:
        st.session_state["last_audio_data"] = audio_bytes
        
        with st.spinner("音声認識中…"):
            tmp_path = None
            try:
                # audio-recorder-streamlitはWAV形式で録音するため、WAVを最優先
                formats_to_try = [
                    (".wav", "audio/wav"),
                    (".webm", "audio/webm"),
                    (".mp3", "audio/mpeg"),
                    (".m4a", "audio/mp4"),
                ]
                
                last_error = None
                for suffix, mime_type in formats_to_try:
                    try:
                        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                            tmp.write(audio_bytes)
                            tmp_path = tmp.name
                        
                        with open(tmp_path, "rb") as f:
                            transcription = client.audio.transcriptions.create(
                                model=STT_DEPLOYMENT_NAME,
                                file=(f"audio{suffix}", f, mime_type),
                                response_format="text",
                            )
                        
                        # 成功したらループを抜ける
                        transcribed_text = transcription if isinstance(transcription, str) else str(transcription)
                        st.success("✅ 音声認識完了！内容を確認して送信してください。")
                        break
                        
                    except Exception as e:
                        last_error = e
                        # 最初の形式（WAV）で失敗した場合のみ警告を表示
                        if suffix == ".wav":
                            st.info("🔄 別の形式で試行中...")
                        if tmp_path and os.path.exists(tmp_path):
                            try:
                                os.remove(tmp_path)
                            except Exception:
                                pass
                        tmp_path = None
                        continue
                
                # すべての形式で失敗した場合
                if not transcribed_text and last_error:
                    raise last_error
                
                # 録音完了後に自動リセット（新しい録音のために）
                if transcribed_text:
                    st.session_state["recorder_session_id"] = str(uuid.uuid4())
                    st.session_state["last_audio_data"] = None
                    st.session_state["last_transcription"] = transcribed_text
                
            except Exception as e:
                st.error(f"❌ 音声認識エラー: {e}")
                st.warning("💡 考えられる原因:")
                st.write("1. 録音時間が短すぎる可能性があります（最低1秒以上録音してください）")
                st.write("2. マイクの権限が許可されていない可能性があります")
                st.write("3. 音声データが破損している可能性があります")
                st.write(f"4. デプロイメント名: `{STT_DEPLOYMENT_NAME}`")
                st.write("5. Azure Portalでデプロイメント名とAPIキーを確認してください")
                
                # デバッグ用: 音声データの先頭バイトを表示
                if audio_bytes and len(audio_bytes) > 0:
                    st.write(f"🔍 音声データの先頭: {audio_bytes[:20].hex()}")
                    
            finally:
                if tmp_path and os.path.exists(tmp_path):
                    try:
                        os.remove(tmp_path)
                    except Exception:
                        pass
    
    return transcribed_text


def generate_speech(text: str, tts_config: dict, voice: str = "alloy") -> bytes:
    """
    テキストから音声を生成（REST API使用）
    
    Args:
        text: 音声化するテキスト
        tts_config: TTS設定の辞書（api_key, endpoint, api_version, deployment_name）
        voice: 使用する音声（alloy, echo, fable, onyx, nova, shimmer）
    
    Returns:
        bytes: 生成された音声データ（MP3形式）、エラー時はNone
    """
    if not text or not text.strip():
        return None
    
    # TTS設定の取得
    api_key = tts_config.get("api_key")
    endpoint = tts_config.get("endpoint")
    api_version = tts_config.get("api_version")
    deployment_name = tts_config.get("deployment_name")
    
    if not all([api_key, endpoint, deployment_name]):
        st.warning("⚠️ TTS設定が不完全です。.envファイルを確認してください。")
        return None
    
    # REST APIエンドポイントURL
    url = f"{endpoint}/openai/deployments/{deployment_name}/audio/speech?api-version={api_version}"
    
    # リクエストヘッダー
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    # リクエストボディ
    payload = {
        "model": deployment_name,
        "input": text[:4096],  # 最大4096文字まで
        "voice": voice
    }
    
    try:
        # REST APIリクエスト
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            return response.content
        else:
            st.error(f"❌ TTS APIエラー: {response.status_code}")
            st.error(f"詳細: {response.text}")
            return None
            
    except requests.exceptions.Timeout:
        st.error("❌ TTS API タイムアウト: 30秒以内に応答がありませんでした")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"❌ TTS API リクエストエラー: {e}")
        return None
    except Exception as e:
        st.error(f"❌ TTS 予期しないエラー: {e}")
        return None


def render_input_ui():
    """入力UIの表示（テキストと音声）"""
    col1, col2 = st.columns([1, 1])
    
    with col1:
        # テキスト入力は session_state に保持して上書きを防ぐ
        text_key = f"text_input_{st.session_state['recorder_session_id']}"
        if text_key not in st.session_state:
            st.session_state[text_key] = ""
        user_text = st.text_input(
            "テキスト入力",
            placeholder="メッセージを入力…",
            key=text_key
        )
        return user_text
    
    return ""


def handle_text_input(user_text: str, transcribed_text: str) -> str:
    """最終的な入力の決定"""
    final_input = user_text
    
    # 音声認識結果がある場合は編集可能なテキストエリアを表示
    if st.session_state.get("last_transcription", "") != "":
        st.text_area(
            "認識結果（編集可）",
            height=80,
            key="last_transcription"
        )
        final_input = st.session_state.get("last_transcription", "")
    
    return final_input


def render_send_button():
    """送信UIの表示"""
    c1, c2 = st.columns([1, 4])
    
    with c1:
        send = st.button(
            "送信", 
            use_container_width=True,
            key=f"send_button_{st.session_state['recorder_session_id']}"
        )
    
    with c2:
        # 録音リセットボタン（デバッグ用）
        if st.button("🔄 録音リセット", help="録音ボタンが消えた時に使用"):
            st.session_state["recorder_session_id"] = str(uuid.uuid4())
            st.session_state["last_audio_data"] = None
            st.session_state["recorder_reset_needed"] = False
            st.session_state["last_transcription"] = ""
            st.rerun()
    
    return send


def generate_ai_response(client, GPT_DEPLOYMENT_NAME, final_input: str, tts_config: dict = None):
    """AI応答の生成とTTS音声生成"""
    # RAG: 現在の質問に関連するJSONを注入
    rag_ctx = build_rag_context(final_input)
    rag_system = {
        "role": "system",
        "content": (
            "以下は参考用のローカルJSONデータです。これを最優先で参照し、"
            "事実に基づき簡潔に日本語で回答してください。データに存在しないことは推測せず、"
            "不明な点は『データからは不明』と述べてください。\n\n" + rag_ctx
        ),
    }
    
    # 送信用メッセージ（先頭の system の直後に RAG を挿入）
    base_msgs = st.session_state["voice_agent_messages"]
    if base_msgs and base_msgs[0].get("role") == "system":
        messages_to_send = [base_msgs[0], rag_system] + base_msgs[1:]
    else:
        messages_to_send = [rag_system] + base_msgs
    
    ai_reply = None
    audio_data = None
    
    with st.spinner("🤖 応答生成中…"):
        try:
            # デバッグ情報を表示
            st.info(f"🔍 使用モデル: {GPT_DEPLOYMENT_NAME}")
            st.info(f"🔍 GPT API バージョン: {os.getenv('AZURE_OPENAI_API_VERSION', 'デフォルト')}")
            st.info(f"🔍 GPT エンドポイント: {os.getenv('AZURE_OPENAI_ENDPOINT', '未設定')}")
            
            resp = client.chat.completions.create(
                model=GPT_DEPLOYMENT_NAME,
                messages=messages_to_send,
                max_completion_tokens=1000,  # GPT-5推論モデル用
                # temperature は推論モデルではサポートされていない（デフォルト値1を使用）
            )
            ai_reply = resp.choices[0].message.content
            
            # TTS音声生成
            if ai_reply and tts_config:
                with st.spinner("🔊 音声生成中..."):
                    audio_data = generate_speech(ai_reply, tts_config)
                    if audio_data:
                        st.success("✅ 音声生成完了！")
                    
        except Exception as e:
            st.error(f"応答生成エラー: {e}")
            st.warning("💡 考えられる原因:")
            st.write("1. デプロイメント名が正しくない可能性があります")
            st.write("2. APIバージョンが対応していない可能性があります")
            st.write("3. APIキーの権限が不足している可能性があります")
            st.write(f"4. 使用しようとしたモデル: `{GPT_DEPLOYMENT_NAME}`")
    
    return ai_reply, audio_data


def display_chat_history():
    """チャット履歴の表示"""
    if st.session_state["voice_agent_messages"]:
        st.divider()
        st.caption("📝 チャット履歴")
        for i, m in enumerate(st.session_state["voice_agent_messages"][-6:]):  # 最新6件のみ表示
            if m["role"] == "user":
                st.markdown(f"**👤 あなた:** {m['content']}")
            elif m["role"] == "assistant":
                st.markdown(f"**🤖 AI:** {m['content']}")


def render_audio_player(audio_data: bytes):
    """
    音声プレイヤーの表示
    
    Args:
        audio_data: 音声データ（MP3形式のバイト列）
    """
    if audio_data:
        st.divider()
        st.caption("🔊 音声再生")
        st.audio(audio_data, format="audio/mp3")
        
        # ダウンロードボタン（オプション）
        st.download_button(
            label="📥 音声をダウンロード",
            data=audio_data,
            file_name=f"ai_response_{uuid.uuid4().hex[:8]}.mp3",
            mime="audio/mp3"
        )
