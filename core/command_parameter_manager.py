#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
コマンドパラメーター管理モジュール
AITRIOSデバイスのコマンドパラメーターを管理する
"""

import json
import base64
import time
import logging
from typing import Dict, Any, List, Optional, Tuple

from api.aitrios_client import AITRIOSClient

class CommandParameterManager:
    """
    AITRIOSデバイスのコマンドパラメーターを管理するクラス
    """
    
    def __init__(self, aitrios_client: AITRIOSClient):
        """
        コマンドパラメーター管理の初期化
        
        Args:
            aitrios_client: AITRIOSクライアント
        """
        self.aitrios_client = aitrios_client
        self.parameter_cache = {}  # デバイスIDをキーとするパラメーターキャッシュ
        self.cache_timestamp = 0  # キャッシュのタイムスタンプ
        self.cache_ttl = 300  # キャッシュの有効期間（秒）
    
    def get_default_parameters(self) -> Dict[str, Any]:
        """
        デフォルトのコマンドパラメーターを取得
        
        Returns:
            Dict[str, Any]: デフォルトパラメーター
        """
        return {
            "commands": [
                {
                    "command_name": "StartUploadInferenceData",
                    "parameters": {
                        "Mode": 2,  # 推論結果のみ
                        "UploadMethod": "HTTPStorage",
                        "StorageName": "http://localhost:8080",
                        "StorageSubDirectoryPath": "/image/{device_id}",
                        "FileFormat": "JPG",
                        "UploadMethodIR": "HTTPStorage",
                        "StorageNameIR": "http://localhost:8080",
                        "StorageSubDirectoryPathIR": "/meta/{device_id}",
                        "CropHOffset": 0,
                        "CropVOffset": 0,
                        "CropHSize": 4056,
                        "CropVSize": 3040,
                        "NumberOfImages": 0,
                        "UploadInterval": 60,
                        "NumberOfInferencesPerMessage": 1,
                        "MaxDetectionsPerFrame": 1,
                        "PPLParameter": {
                            "header": {
                                "id": "00",
                                "version": "01.01.00"
                            },
                            "dnn_output_detections": 100,
                            "max_detections": 1,
                            "threshold": 0.3,
                            "input_width": 320,
                            "input_height": 320
                        }
                    }
                }
            ]
        }
    
    def get_device_parameters(self, device_id: str) -> Dict[str, Any]:
        """
        デバイスの現在のコマンドパラメーターを取得
        
        Args:
            device_id: デバイスID
            
        Returns:
            Dict[str, Any]: コマンドパラメーター
        """
        current_time = time.time()
        
        # キャッシュが有効期限内か確認
        if device_id in self.parameter_cache and (current_time - self.cache_timestamp) < self.cache_ttl:
            print(f"キャッシュからパラメーターを返します： {device_id}")
            return self.parameter_cache[device_id]
        
        try:
            # AITRIOSからのパラメーター取得を試みる
            print(f"AITRIOSからパラメーターを取得します： {device_id}")
            # ここでは処理の流れを説明するだけのダミーコード
            # 実際の実装ではAITRIOSクライアントを使用してAPIからパラメーターを取得する
            
            # ダミーデータ（実際にはAPIから取得）
            parameters = self.get_default_parameters()
            
            # キャッシュに保存
            self.parameter_cache[device_id] = parameters
            self.cache_timestamp = current_time
            
            return parameters
        except Exception as e:
            print(f"パラメーター取得エラー: {str(e)}")
            # エラー時はデフォルトパラメーターを返す
            return self.get_default_parameters()
    
    def apply_parameters(self, device_id: str, parameters: Dict[str, Any]) -> bool:
        """
        デバイスにコマンドパラメーターを適用
        
        Args:
            device_id: デバイスID
            parameters: 適用するパラメーター
            
        Returns:
            bool: 成功したかどうか
        """
        try:
            # バリデーション
            if not self._validate_parameters(parameters):
                print("パラメーターのバリデーションに失敗しました")
                return False
            
            # AITRIOSにパラメーターを適用
            print(f"AITRIOSにパラメーターを適用します: {device_id}")
            
            # パラメーターをエンコード
            encoded_parameters = self._encode_parameters(parameters)
            
            # ここではデモ用に成功を返す
            # 実際の実装では、AITRIOSクライアントを使ってAPIを呼び出す
            
            # キャッシュを更新
            self.parameter_cache[device_id] = parameters
            self.cache_timestamp = time.time()
            
            return True
        except Exception as e:
            print(f"パラメーター適用エラー: {str(e)}")
            return False
    
    def _validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """
        パラメーターのバリデーション
        
        Args:
            parameters: バリデーションするパラメーター
            
        Returns:
            bool: バリデーション結果
        """
        # コマンドが存在するか確認
        if "commands" not in parameters or not parameters["commands"]:
            return False
        
        # StartUploadInferenceDataコマンドが存在するか確認
        commands = parameters["commands"]
        start_upload_cmd = None
        
        for cmd in commands:
            if cmd.get("command_name") == "StartUploadInferenceData":
                start_upload_cmd = cmd
                break
        
        if not start_upload_cmd or "parameters" not in start_upload_cmd:
            return False
        
        # 必須パラメーターの存在確認
        required_params = ["Mode", "UploadInterval", "NumberOfInferencesPerMessage"]
        params = start_upload_cmd["parameters"]
        
        for param in required_params:
            if param not in params:
                return False
        
        # モードに応じた必須パラメーターの確認
        mode = params.get("Mode")
        
        if mode in [0, 1]:  # 画像アップロードあり
            img_params = ["UploadMethod", "StorageName", "StorageSubDirectoryPath"]
            for param in img_params:
                if param not in params:
                    return False
        
        if mode in [1, 2]:  # 推論結果アップロードあり
            ir_params = ["UploadMethodIR", "StorageNameIR", "StorageSubDirectoryPathIR"]
            for param in ir_params:
                if param not in params:
                    return False
        
        return True
    
    def _encode_parameters(self, parameters: Dict[str, Any]) -> str:
        """
        パラメーターをBase64エンコード
        
        Args:
            parameters: エンコードするパラメーター
            
        Returns:
            str: エンコードされたパラメーター
        """
        # JSONに変換
        json_params = json.dumps(parameters, ensure_ascii=False)
        
        # Base64エンコード
        encoded = base64.b64encode(json_params.encode('utf-8')).decode('utf-8')
        
        return encoded