#!/usr/bin/env python3
"""
環境構築の確認スクリプト
このスクリプトを実行して、必要な環境が整っているか確認できます。
"""

import sys
import subprocess
import os

def check_python_version():
    """Pythonのバージョンを確認"""
    print("=" * 50)
    print("Python バージョン確認")
    print("=" * 50)
    version = sys.version_info
    print(f"Python {version.major}.{version.minor}.{version.micro}")
    
    if version.major >= 3 and version.minor >= 8:
        print("✅ Python バージョンは要件を満たしています")
        return True
    else:
        print("❌ Python 3.8以上が必要です")
        return False

def check_packages():
    """必要なパッケージがインストールされているか確認"""
    print("\n" + "=" * 50)
    print("必要なパッケージの確認")
    print("=" * 50)
    
    required_packages = {
        'streamlit': 'streamlit',
        'pandas': 'pandas',
        'numpy': 'numpy',
        'openai': 'openai',
        'scikit-learn': 'sklearn',
        'python-dotenv': 'dotenv',
        'plotly': 'plotly',
        'matplotlib': 'matplotlib',
        'youtube-transcript-api': 'youtube_transcript_api'
    }
    
    all_installed = True
    
    for package_name, import_name in required_packages.items():
        try:
            __import__(import_name)
            print(f"✅ {package_name}")
        except ImportError:
            print(f"❌ {package_name} - インストールが必要です")
            all_installed = False
    
    return all_installed

def check_env_file():
    """環境変数ファイルの存在確認"""
    print("\n" + "=" * 50)
    print("環境変数ファイルの確認")
    print("=" * 50)
    
    if os.path.exists('.env'):
        print("✅ .env ファイルが存在します")
        
        # 必須の環境変数が設定されているか確認
        from dotenv import load_dotenv
        load_dotenv()
        
        required_vars = [
            'AZURE_OPENAI_ENDPOINT',
            'AZURE_OPENAI_KEY',
            'AZURE_OPENAI_API_VERSION',
            'AZURE_OPENAI_MODEL'
        ]
        
        all_set = True
        for var in required_vars:
            value = os.getenv(var)
            if value and 'your_' not in value.lower() and value.strip():
                print(f"✅ {var} - 設定済み")
            else:
                print(f"❌ {var} - 設定が必要です")
                all_set = False
        
        return all_set
    else:
        print("❌ .env ファイルが見つかりません")
        print("   .env.example をコピーして .env を作成してください:")
        print("   cp .env.example .env")
        return False

def check_git():
    """Gitのインストール確認"""
    print("\n" + "=" * 50)
    print("Git の確認")
    print("=" * 50)
    
    try:
        result = subprocess.run(['git', '--version'], 
                              capture_output=True, 
                              text=True, 
                              check=True)
        print(f"✅ {result.stdout.strip()}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Git がインストールされていません")
        return False

def main():
    """メイン処理"""
    print("\n🔍 Sapi-AI 環境構築チェック\n")
    
    results = []
    
    # 各種チェック実行
    results.append(("Python バージョン", check_python_version()))
    results.append(("必要なパッケージ", check_packages()))
    results.append(("環境変数ファイル", check_env_file()))
    results.append(("Git", check_git()))
    
    # 結果のサマリー
    print("\n" + "=" * 50)
    print("チェック結果のサマリー")
    print("=" * 50)
    
    all_passed = True
    for name, passed in results:
        status = "✅ OK" if passed else "❌ NG"
        print(f"{status} - {name}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("✅ すべてのチェックに合格しました！")
        print("\nアプリケーションを起動できます:")
        print("  streamlit run app.py")
    else:
        print("❌ いくつかの項目で問題が見つかりました")
        print("\nREADME.mdを参照して、環境構築を完了してください")
        print("必要なパッケージをインストール:")
        print("  pip install -r requirements.txt")
    print("=" * 50)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
