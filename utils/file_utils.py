#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ファイル操作ユーティリティモジュール
CSVファイルなどのファイル操作を行うユーティリティ関数
"""

import csv
import os

def export_classes_to_csv(class_list, filename):
    """
    クラスリストをCSVファイルに出力
    
    Args:
        class_list (list): クラスリスト
        filename (str): 出力ファイルパス
        
    Returns:
        bool: 成功した場合はTrue、失敗した場合はFalse
    """
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Index", "ClassName"])  # ヘッダー
            
            for i, class_name in enumerate(class_list):
                writer.writerow([i, class_name])
                
        return True
    except Exception as e:
        print(f"CSVエクスポートエラー: {str(e)}")
        return False

def import_classes_from_csv(filename):
    """
    CSVファイルからクラスリストを読み込み
    
    Args:
        filename (str): 入力ファイルパス
        
    Returns:
        list: 読み込まれたクラスリスト、失敗した場合は空リスト
    """
    try:
        classes = []
        with open(filename, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            next(reader, None)  # ヘッダーをスキップ
            
            for row in reader:
                if len(row) >= 2:
                    classes.append(row[1])  # クラス名を追加
                    
        return classes
    except Exception as e:
        print(f"CSVインポートエラー: {str(e)}")
        return []

def ensure_directory(directory_path):
    """
    ディレクトリが存在することを確認し、必要に応じて作成
    
    Args:
        directory_path (str): 確認/作成するディレクトリパス
        
    Returns:
        bool: 成功した場合はTrue、失敗した場合はFalse
    """
    try:
        if not os.path.exists(directory_path):
            os.makedirs(directory_path)
        return True
    except Exception as e:
        print(f"ディレクトリ作成エラー: {str(e)}")
        return False

def get_latest_file(directory, extension=None):
    """
    指定したディレクトリ内の最新ファイルを取得
    
    Args:
        directory (str): ディレクトリパス
        extension (str, optional): ファイル拡張子フィルタ（例: '.jpg'）
    
    Returns:
        str: 最新ファイルのパス、またはNone
    """
    try:
        files = os.listdir(directory)
        if extension:
            files = [f for f in files if f.endswith(extension)]
            
        if not files:
            return None
            
        paths = [os.path.join(directory, f) for f in files]
        return max(paths, key=os.path.getmtime)
    except Exception as e:
        print(f"ファイル検索エラー: {str(e)}")
        return None