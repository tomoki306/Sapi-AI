# logger.py
"""
エラーログ記録機能
エラーの自動記録、ログの閲覧機能を実装
"""

import logging
import os
from datetime import datetime
from typing import List, Dict
import streamlit as st


# ログファイルのパス
LOG_FILE = 'app.log'
MAX_LOG_SIZE = 10 * 1024 * 1024  # 10MB


# ロガーの設定
def setup_logger():
    """ロガーの初期設定"""
    logger = logging.getLogger('learning_app')
    logger.setLevel(logging.INFO)
    
    # ファイルハンドラー
    file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    
    # フォーマッター
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    
    # ハンドラーを追加（重複を避ける）
    if not logger.handlers:
        logger.addHandler(file_handler)
    
    return logger


# グローバルロガー
logger = setup_logger()


def log_info(message: str, context: str = ""):
    """
    情報ログを記録
    Args:
        message: ログメッセージ
        context: コンテキスト情報
    """
    if context:
        logger.info(f"[{context}] {message}")
    else:
        logger.info(message)


def log_error(error: Exception, context: str = "", show_user: bool = True, details: dict = None):
    """
    エラーログを記録
    Args:
        error: エラーオブジェクト
        context: エラーが発生したコンテキスト
        show_user: ユーザーにエラーを表示するか
        details: 追加の詳細情報（辞書形式）
    """
    error_msg = f"[{context}] {str(error)}" if context else str(error)
    
    # 詳細情報を追加
    if details:
        details_str = ", ".join([f"{k}={v}" for k, v in details.items()])
        error_msg = f"{error_msg} | Details: {details_str}"
    
    logger.error(error_msg, exc_info=True)
    
    if show_user:
        st.error(f"エラーが発生しました: {str(error)}")


def log_warning(message: str, context: str = ""):
    """
    警告ログを記録
    Args:
        message: 警告メッセージ
        context: コンテキスト情報
    """
    if context:
        logger.warning(f"[{context}] {message}")
    else:
        logger.warning(message)


def log_user_action(action: str, details: str = ""):
    """
    ユーザーの操作を記録
    Args:
        action: 操作内容
        details: 詳細情報
    """
    if details:
        logger.info(f"[USER_ACTION] {action} - {details}")
    else:
        logger.info(f"[USER_ACTION] {action}")


def read_log_file(max_lines: int = 100) -> List[str]:
    """
    ログファイルを読み込み
    Args:
        max_lines: 読み込む最大行数
    Returns:
        List[str]: ログ行のリスト
    """
    try:
        if not os.path.exists(LOG_FILE):
            return []
        
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 新しい順に返す
        return lines[-max_lines:][::-1]
    
    except Exception as e:
        st.error(f"ログファイルの読み込みに失敗しました: {str(e)}")
        return []


def parse_log_line(line: str) -> Dict:
    """
    ログ行をパースして辞書に変換
    Args:
        line: ログ行
    Returns:
        Dict: パースされたログ情報
    """
    try:
        # フォーマット: "2025-10-05 12:34:56 - INFO - message"
        parts = line.split(' - ', 2)
        if len(parts) >= 3:
            return {
                'datetime': parts[0],
                'level': parts[1],
                'message': parts[2].strip()
            }
        else:
            return {
                'datetime': '',
                'level': 'UNKNOWN',
                'message': line.strip()
            }
    except Exception:
        return {
            'datetime': '',
            'level': 'UNKNOWN',
            'message': line.strip()
        }


def get_log_statistics() -> Dict:
    """
    ログの統計情報を取得
    Returns:
        Dict: 統計情報
    """
    try:
        if not os.path.exists(LOG_FILE):
            return {
                'total_lines': 0,
                'error_count': 0,
                'warning_count': 0,
                'info_count': 0,
                'file_size_mb': 0.0
            }
        
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        error_count = sum(1 for line in lines if ' - ERROR - ' in line)
        warning_count = sum(1 for line in lines if ' - WARNING - ' in line)
        info_count = sum(1 for line in lines if ' - INFO - ' in line)
        
        file_size = os.path.getsize(LOG_FILE)
        file_size_mb = round(file_size / (1024 * 1024), 2)
        
        return {
            'total_lines': len(lines),
            'error_count': error_count,
            'warning_count': warning_count,
            'info_count': info_count,
            'file_size_mb': file_size_mb
        }
    
    except Exception as e:
        st.error(f"ログ統計の取得に失敗しました: {str(e)}")
        return {
            'total_lines': 0,
            'error_count': 0,
            'warning_count': 0,
            'info_count': 0,
            'file_size_mb': 0.0
        }


def filter_logs(lines: List[str], level_filter: str = "ALL", search_keyword: str = "") -> List[str]:
    """
    ログをフィルタリング
    Args:
        lines: ログ行のリスト
        level_filter: レベルフィルタ (ALL, ERROR, WARNING, INFO)
        search_keyword: 検索キーワード
    Returns:
        List[str]: フィルタリングされたログ行
    """
    filtered = lines
    
    # レベルでフィルタリング
    if level_filter != "ALL":
        filtered = [line for line in filtered if f" - {level_filter} - " in line]
    
    # キーワードで検索
    if search_keyword:
        filtered = [line for line in filtered if search_keyword.lower() in line.lower()]
    
    return filtered


def clear_old_logs():
    """古いログをクリア（ファイルサイズが大きい場合）"""
    try:
        if os.path.exists(LOG_FILE):
            file_size = os.path.getsize(LOG_FILE)
            if file_size > MAX_LOG_SIZE:
                # 最新の10000行だけ保持
                with open(LOG_FILE, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                with open(LOG_FILE, 'w', encoding='utf-8') as f:
                    f.writelines(lines[-10000:])
                
                log_info("古いログをクリアしました", "LOG_MAINTENANCE")
    
    except Exception as e:
        print(f"ログクリアに失敗: {str(e)}")


def display_log_viewer():
    """ログビューアー画面を表示"""
    st.subheader("📋 ログビューア")
    
    # 統計情報の表示
    stats = get_log_statistics()
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("総行数", stats['total_lines'])
    
    with col2:
        st.metric("エラー", stats['error_count'])
    
    with col3:
        st.metric("警告", stats['warning_count'])
    
    with col4:
        st.metric("情報", stats['info_count'])
    
    with col5:
        st.metric("ファイルサイズ", f"{stats['file_size_mb']} MB")
    
    # フィルタリングオプション
    st.markdown("#### フィルタ")
    
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        level_filter = st.selectbox(
            "ログレベル",
            ["ALL", "ERROR", "WARNING", "INFO"],
            index=0
        )
    
    with col2:
        search_keyword = st.text_input("キーワード検索", "")
    
    with col3:
        max_lines = st.number_input("表示行数", min_value=10, max_value=1000, value=100, step=10)
    
    # ログの表示
    lines = read_log_file(max_lines=int(max_lines))
    filtered_lines = filter_logs(lines, level_filter, search_keyword)
    
    st.markdown(f"#### ログ内容（{len(filtered_lines)}件）")
    
    if filtered_lines:
        # ログをテーブル形式で表示
        for line in filtered_lines:
            log_data = parse_log_line(line)
            
            # レベルによって色を変える
            if log_data['level'] == 'ERROR':
                st.error(f"**{log_data['datetime']}** | {log_data['message']}")
            elif log_data['level'] == 'WARNING':
                st.warning(f"**{log_data['datetime']}** | {log_data['message']}")
            else:
                st.info(f"**{log_data['datetime']}** | {log_data['message']}")
    else:
        st.info("ログが見つかりませんでした")
    
    # ログ管理ボタン
    st.markdown("#### ログ管理")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("ログをクリア"):
            if os.path.exists(LOG_FILE):
                os.remove(LOG_FILE)
                setup_logger()  # ロガーを再設定
                st.success("ログをクリアしました")
                st.rerun()
            else:
                st.info("ログファイルが存在しません")
    
    with col2:
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, 'r', encoding='utf-8') as f:
                log_content = f.read()
            
            st.download_button(
                label="ログをダウンロード",
                data=log_content,
                file_name=f"app_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain"
            )


# アプリ起動時にログメンテナンスを実行
def log_maintenance_on_startup():
    """アプリ起動時のログメンテナンス"""
    clear_old_logs()
    log_info("アプリケーションを起動しました", "APP_STARTUP")
