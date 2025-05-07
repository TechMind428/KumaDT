#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
設定管理モジュール
アプリケーション設定の読み書きを管理
"""

import os
import re
import settings

class SettingsManager:
    """設定ファイルの読み書きを管理するクラス"""
    
    def __init__(self, settings_module=settings):
        """
        設定マネージャーの初期化
        
        Args:
            settings_module: 設定が定義されているモジュール
        """
        self.settings_module = settings_module
        
        # モジュールの実際のファイルパスを取得
        if hasattr(settings_module, '__file__'):
            # モジュールの実際のファイルパスを取得
            self.settings_file = os.path.abspath(settings_module.__file__)
            print(f"設定ファイルのパス: {self.settings_file}")
        else:
            # モジュールのファイルパスが取得できない場合のフォールバック
            print("警告: モジュールのファイルパスが取得できません。フォールバックを使用します。")
            # 現在のプロジェクトディレクトリを取得
            current_dir = os.path.dirname(os.path.abspath(__file__))
            parent_dir = os.path.dirname(current_dir)
            self.settings_file = os.path.join(parent_dir, "settings.py")
            print(f"フォールバックパス: {self.settings_file}")
        
        self.config = {}
        self.load_settings()
    
    def load_settings(self):
        """
        設定をモジュールから読み込む
        
        Returns:
            dict: 読み込まれた設定
        """
        self.config = {
            'DEVICE_ID': getattr(self.settings_module, 'DEVICE_ID', ""),
            'CLIENT_ID': getattr(self.settings_module, 'CLIENT_ID', ""),
            'CLIENT_SECRET': getattr(self.settings_module, 'CLIENT_SECRET', ""),
            'numberofclass': getattr(self.settings_module, 'numberofclass', 3),
            'objclass': getattr(self.settings_module, 'objclass', ["CLASS0", "CLASS1", "CLASS2"]),
        }
        return self.config
    
    def save_settings(self, new_settings):
        """
        新しい設定をファイルに保存
        
        Args:
            new_settings (dict): 保存する新しい設定
            
        Returns:
            bool: 保存が成功したかどうか
        """
        try:
            # 設定ファイルの存在確認
            if not os.path.exists(self.settings_file):
                raise FileNotFoundError(f"設定ファイルが見つかりません: {self.settings_file}")
            
            print(f"設定を保存: {self.settings_file}")
            
            # 設定ファイルの内容を一旦読み込む
            with open(self.settings_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 各設定項目を更新
            modified_content = content
            
            # DEVICE_ID, CLIENT_ID, CLIENT_SECRETの更新
            for key in ['DEVICE_ID', 'CLIENT_ID', 'CLIENT_SECRET']:
                if key in new_settings:
                    value = new_settings[key]
                    pattern = r'({}\s*=\s*)["\'].*?["\']'.format(key)
                    replacement = f'{key} = "{value}"'
                    if re.search(pattern, modified_content):
                        modified_content = re.sub(pattern, replacement, modified_content)
                    else:
                        print(f"警告: {key}のパターンがマッチしませんでした")
            
            # numberofclassの更新
            if 'numberofclass' in new_settings:
                value = new_settings['numberofclass']
                pattern = r'(numberofclass\s*=\s*)\d+'
                replacement = f'numberofclass = {value}'
                if re.search(pattern, modified_content):
                    modified_content = re.sub(pattern, replacement, modified_content)
                else:
                    print(f"警告: numberofclassのパターンがマッチしませんでした")
            
            # objclassの更新
            if 'objclass' in new_settings:
                value = new_settings['objclass']
                # 改行を含む可能性があるため、DOTALLフラグを使用
                pattern = r'(objclass\s*=\s*)\[.*?\]'
                
                # リストの文字列表現を整形
                objclass_str = "["
                for i, cls in enumerate(value):
                    if i > 0:
                        objclass_str += ", "
                    objclass_str += f"'{cls}'"
                objclass_str += "]"
                
                replacement = f'objclass = {objclass_str}'
                
                if re.search(pattern, modified_content, re.DOTALL):
                    modified_content = re.sub(pattern, replacement, modified_content, flags=re.DOTALL)
                else:
                    print(f"警告: objclassのパターンがマッチしませんでした")
            
            # 変更がないかチェック
            if content == modified_content:
                print("情報: 変更がありませんでした。現在の設定が既に保存されています。")
                # 変更がなくても成功として扱う
                return True
            
            # 設定ファイルに書き戻す
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                f.write(modified_content)
            
            # 設定モジュールに反映
            for key, value in new_settings.items():
                setattr(self.settings_module, key, value)
            
            # コンフィグを更新
            self.config = new_settings
            
            print("設定が正常に保存されました")
            return True
        except Exception as e:
            print(f"設定保存エラー: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
            
    def get_setting(self, key, default=None):
        """
        指定したキーの設定値を取得
        
        Args:
            key (str): 取得する設定のキー
            default: デフォルト値
            
        Returns:
            設定値
        """
        return self.config.get(key, default)