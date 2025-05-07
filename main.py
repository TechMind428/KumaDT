#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Kumakita - AITRIOSによる物体検出と熊検出警告アプリケーション
メインエントリーポイント

作成者：AI Assistant
"""

import sys
import os
import argparse

# 現在のディレクトリをパスに追加
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# デバッグ出力
print(f"Python path: {sys.path}")
print(f"Current directory: {current_dir}")

# UI部分をインポート
from ui.main_window import KumakitaApp

def parse_args():
    """コマンドライン引数をパース"""
    parser = argparse.ArgumentParser(description='KumaDesktop - AITRIOSデバイス物体検出モニター')
    parser.add_argument('--debug', action='store_true', help='デバッグモードを有効化')
    parser.add_argument('--settings', type=str, help='代替設定ファイルのパス')
    return parser.parse_args()

def main():
    """アプリケーションのエントリーポイント"""
    # コマンドライン引数を解析
    args = parse_args()
    
    # デバッグモードが有効な場合は追加の情報を出力
    if args.debug:
        print("デバッグモードが有効です")
        print("Python バージョン:", sys.version)
        print("モジュールの検索パス:")
        for path in sys.path:
            print(f"  - {path}")
    
    # 代替設定ファイルの処理（未実装）
    if args.settings:
        print(f"注意: 代替設定ファイル機能は未実装です: {args.settings}")
    
    # アプリケーションを起動
    app = KumakitaApp()
    app.mainloop()

if __name__ == "__main__":
    main()