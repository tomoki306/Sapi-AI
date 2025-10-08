# backup_manager.py
"""
自動バックアップ機能
1日1回の自動バックアップ、最大30日分の保持、古いバックアップの自動削除
"""

import json
import os
import shutil
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import streamlit as st
import glob


class BackupManager:
    """バックアップ管理クラス"""
    
    def __init__(self, backup_dir: str = "backups"):
        self.backup_dir = backup_dir
        self.backup_files = [
            'subjects.json',
            'grades.json',
            'progress.json',
            'reminders.json',
            'user_profile.json'
        ]
        self.keep_days = 30
        
        # バックアップディレクトリを作成
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
    
    def should_backup(self) -> bool:
        """
        バックアップが必要かどうかを判定
        Returns:
            bool: バックアップが必要な場合True
        """
        # 最後のバックアップ日時を取得
        last_backup_info = self.get_last_backup_info()
        
        if not last_backup_info:
            return True  # バックアップが存在しない場合
        
        # 24時間経過しているかチェック
        last_backup_time = last_backup_info['datetime']
        time_since_backup = datetime.now() - last_backup_time
        
        return time_since_backup >= timedelta(hours=24)
    
    def create_backup(self) -> bool:
        """
        バックアップを作成
        Returns:
            bool: バックアップが成功した場合True
        """
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backed_up_files = []
            
            for filename in self.backup_files:
                if os.path.exists(filename):
                    # バックアップファイル名を生成
                    backup_filename = f"{timestamp}_{filename}"
                    backup_path = os.path.join(self.backup_dir, backup_filename)
                    
                    # ファイルをコピー
                    shutil.copy2(filename, backup_path)
                    backed_up_files.append(filename)
            
            # バックアップ情報を記録
            backup_info = {
                'datetime': datetime.now().isoformat(),
                'timestamp': timestamp,
                'files': backed_up_files,
                'file_count': len(backed_up_files)
            }
            
            info_path = os.path.join(self.backup_dir, f"{timestamp}_backup_info.json")
            with open(info_path, 'w', encoding='utf-8') as f:
                json.dump(backup_info, f, ensure_ascii=False, indent=2)
            
            return True
            
        except Exception as e:
            st.error(f"バックアップ作成中にエラーが発生しました: {str(e)}")
            return False
    
    def clean_old_backups(self) -> int:
        """
        古いバックアップファイルを削除
        Returns:
            int: 削除されたファイル数
        """
        deleted_count = 0
        cutoff_date = datetime.now() - timedelta(days=self.keep_days)
        
        try:
            # バックアップ情報ファイルを取得
            info_files = glob.glob(os.path.join(self.backup_dir, "*_backup_info.json"))
            
            for info_file in info_files:
                try:
                    with open(info_file, 'r', encoding='utf-8') as f:
                        backup_info = json.load(f)
                    
                    backup_date = datetime.fromisoformat(backup_info['datetime'])
                    
                    if backup_date < cutoff_date:
                        # 関連するバックアップファイルを削除
                        timestamp = backup_info['timestamp']
                        
                        # バックアップされたファイルを削除
                        for original_file in self.backup_files:
                            backup_file = f"{timestamp}_{original_file}"
                            backup_path = os.path.join(self.backup_dir, backup_file)
                            if os.path.exists(backup_path):
                                os.remove(backup_path)
                                deleted_count += 1
                        
                        # 情報ファイルも削除
                        os.remove(info_file)
                        deleted_count += 1
                        
                except Exception as e:
                    st.warning(f"バックアップファイル {info_file} の処理でエラー: {str(e)}")
                    
        except Exception as e:
            st.error(f"古いバックアップの削除中にエラーが発生しました: {str(e)}")
        
        return deleted_count
    
    def get_backup_list(self) -> List[Dict]:
        """
        バックアップの一覧を取得
        Returns:
            List[Dict]: バックアップ情報のリスト
        """
        backups = []
        
        try:
            info_files = glob.glob(os.path.join(self.backup_dir, "*_backup_info.json"))
            
            for info_file in info_files:
                try:
                    with open(info_file, 'r', encoding='utf-8') as f:
                        backup_info = json.load(f)
                    
                    # ファイルサイズを計算
                    total_size = 0
                    for original_file in backup_info.get('files', []):
                        backup_file = f"{backup_info['timestamp']}_{original_file}"
                        backup_path = os.path.join(self.backup_dir, backup_file)
                        if os.path.exists(backup_path):
                            total_size += os.path.getsize(backup_path)
                    
                    backup_info['total_size'] = total_size
                    backup_info['size_mb'] = round(total_size / (1024 * 1024), 2)
                    backups.append(backup_info)
                    
                except Exception as e:
                    st.warning(f"バックアップ情報の読み込みでエラー: {str(e)}")
            
            # 日時順でソート（新しい順）
            backups.sort(key=lambda x: x['datetime'], reverse=True)
            
        except Exception as e:
            st.error(f"バックアップ一覧の取得でエラー: {str(e)}")
        
        return backups
    
    def get_last_backup_info(self) -> Optional[Dict]:
        """
        最新のバックアップ情報を取得
        Returns:
            Optional[Dict]: 最新のバックアップ情報
        """
        backups = self.get_backup_list()
        if backups:
            last_backup = backups[0].copy()
            last_backup['datetime'] = datetime.fromisoformat(last_backup['datetime'])
            return last_backup
        return None
    
    def restore_from_backup(self, timestamp: str) -> bool:
        """
        指定されたタイムスタンプのバックアップから復元
        Args:
            timestamp: バックアップのタイムスタンプ
        Returns:
            bool: 復元が成功した場合True
        """
        try:
            # バックアップ情報を読み込み
            info_path = os.path.join(self.backup_dir, f"{timestamp}_backup_info.json")
            if not os.path.exists(info_path):
                st.error("バックアップ情報が見つかりません")
                return False
            
            with open(info_path, 'r', encoding='utf-8') as f:
                backup_info = json.load(f)
            
            restored_files = []
            
            # 各ファイルを復元
            for original_file in backup_info.get('files', []):
                backup_file = f"{timestamp}_{original_file}"
                backup_path = os.path.join(self.backup_dir, backup_file)
                
                if os.path.exists(backup_path):
                    # 現在のファイルをバックアップ（復元前）
                    if os.path.exists(original_file):
                        restore_backup = f"{original_file}.restore_backup"
                        shutil.copy2(original_file, restore_backup)
                    
                    # バックアップから復元
                    shutil.copy2(backup_path, original_file)
                    restored_files.append(original_file)
            
            st.success(f"バックアップから復元しました: {', '.join(restored_files)}")
            return True
            
        except Exception as e:
            st.error(f"復元中にエラーが発生しました: {str(e)}")
            return False
    
    def auto_backup(self):
        """
        自動バックアップの実行
        Returns:
            Tuple[bool, int]: (バックアップ実行したか, 削除したファイル数)
        """
        if self.should_backup():
            if self.create_backup():
                deleted_count = self.clean_old_backups()
                
                # セッションステートに記録
                st.session_state.last_auto_backup = datetime.now()
                
                return True, deleted_count
        return False, 0
    
    def get_backup_status(self) -> Dict:
        """
        バックアップの状態情報を取得
        Returns:
            Dict: バックアップ状態の情報
        """
        backups = self.get_backup_list()
        last_backup = self.get_last_backup_info()
        
        total_backups = len(backups)
        total_size = sum(backup.get('total_size', 0) for backup in backups)
        
        status = {
            'total_backups': total_backups,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'last_backup': last_backup,
            'needs_backup': self.should_backup()
        }
        
        return status


def display_backup_management():
    """バックアップ管理画面を表示"""
    st.subheader("💾 バックアップ管理")
    
    backup_manager = BackupManager()
    status = backup_manager.get_backup_status()
    
    # バックアップ状態の表示
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("バックアップ数", status['total_backups'])
    
    with col2:
        st.metric("総容量", f"{status['total_size_mb']} MB")
    
    with col3:
        if status['last_backup']:
            last_time = status['last_backup']['datetime']
            time_ago = datetime.now() - last_time
            hours_ago = int(time_ago.total_seconds() / 3600)
            st.metric("最終バックアップ", f"{hours_ago}時間前")
        else:
            st.metric("最終バックアップ", "なし")
    
    with col4:
        if status['needs_backup']:
            st.metric("状態", "要バックアップ")
        else:
            st.metric("状態", "最新")
    
    # バックアップ操作
    st.markdown("#### バックアップ操作")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("今すぐバックアップ", type="primary"):
            with st.spinner("バックアップ中..."):
                if backup_manager.create_backup():
                    st.success("バックアップが完了しました")
                    st.rerun()
    
    with col2:
        if st.button("古いバックアップを削除"):
            deleted_count = backup_manager.clean_old_backups()
            if deleted_count > 0:
                st.success(f"{deleted_count}個のファイルを削除しました")
                st.rerun()
            else:
                st.info("削除するファイルはありませんでした")
    
    with col3:
        if st.button("自動バックアップ実行"):
            backed_up, deleted = backup_manager.auto_backup()
            if backed_up:
                st.success("自動バックアップが完了しました")
                if deleted > 0:
                    st.info(f"古いファイル {deleted}個を削除しました")
                st.rerun()
            else:
                st.info("バックアップは必要ありませんでした")
    
    # バックアップ一覧
    st.markdown("#### バックアップ履歴")
    
    backups = backup_manager.get_backup_list()
    
    if backups:
        for backup in backups:
            with st.expander(f"📅 {backup['datetime'][:16]} ({backup['file_count']}ファイル, {backup['size_mb']}MB)"):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write("**含まれるファイル:**")
                    for file in backup.get('files', []):
                        st.write(f"• {file}")
                
                with col2:
                    restore_key = f"restore_{backup['timestamp']}"
                    confirm_key = f"confirm_restore_{backup['timestamp']}"
                    
                    if st.button("復元", key=restore_key):
                        if st.session_state.get(confirm_key, False):
                            if backup_manager.restore_from_backup(backup['timestamp']):
                                st.rerun()
                        else:
                            st.session_state[confirm_key] = True
                            st.warning("もう一度クリックして復元を確認してください")
    else:
        st.info("バックアップが存在しません")


def auto_backup_on_startup():
    """アプリ起動時の自動バックアップ（静かに実行）"""
    if 'auto_backup_checked' not in st.session_state:
        backup_manager = BackupManager()
        backed_up, deleted = backup_manager.auto_backup()
        
        st.session_state.auto_backup_checked = True
        
        if backed_up:
            st.session_state.auto_backup_done = True
            st.session_state.auto_backup_deleted = deleted
