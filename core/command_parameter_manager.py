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

class CommandParameterManager:
    """
    AITRIOSデバイスのコマンドパラメーターを管理するクラス
    """
    
    def __init__(self, aitrios_client):
        """
        コマンドパラメーター管理の初期化
        
        Args:
            aitrios_client: AITRIOSクライアント
        """
        self.aitrios_client = aitrios_client
        self.parameter_files_cache = {}
        self.cache_timestamp = 0
        self.cache_ttl = 300  # 5分のキャッシュTTL
    
    async def get_device_parameters(self, device_id):
        """
        デバイスのコマンドパラメーターを取得
        
        Args:
            device_id: デバイスID
            
        Returns:
            Dict[str, Any]: コマンドパラメーター
        """
        try:
            # キャッシュを更新
            await self._update_parameter_files_cache()
            
            # デバイスがバインドされているファイルを検索
            bound_file_name, bound_file_info = await self.get_parameter_file_for_device(device_id)
            
            # バインドされている場合はそのファイルのパラメーターを返す
            if bound_file_info and "parameter" in bound_file_info:
                print(f"Found parameters for device {device_id} in file {bound_file_name}")
                return bound_file_info["parameter"]
            
            # バインドされていない場合はエラー
            print(f"No parameter file found for device {device_id}")
            return {}
            
        except Exception as e:
            print(f"Error getting device parameters for {device_id}: {str(e)}")
            return {}
    
    async def _update_parameter_files_cache(self):
        """キャッシュを更新"""
        current_time = time.time()
        
        # キャッシュの有効期限が切れていたら更新
        if current_time - self.cache_timestamp > self.cache_ttl or not self.parameter_files_cache:
            try:
                # コマンドパラメーターファイル一覧を取得
                self.parameter_files_cache = await self.aitrios_client.get_command_parameter_files()
                self.cache_timestamp = current_time
                print(f"Updated parameter files cache. Found {len(self.parameter_files_cache.get('parameter_list', []))} files")
            except Exception as e:
                print(f"Error updating parameter files cache: {str(e)}")
                if not self.parameter_files_cache:
                    # 初回取得失敗時は空のキャッシュを作成
                    self.parameter_files_cache = {"parameter_list": []}
    
    async def get_parameter_file_for_device(self, device_id):
        """
        デバイスに対応するパラメーターファイル名を取得
        
        Args:
            device_id: デバイスID
            
        Returns:
            Tuple[str, Dict[str, Any]]: (ファイル名, バインド情報)
        """
        # キャッシュを更新
        await self._update_parameter_files_cache()
        
        # このデバイスがバインドされているファイルを確認
        for param_file in self.parameter_files_cache.get("parameter_list", []):
            device_ids = param_file.get("device_ids", [])
            if device_id in device_ids:
                file_name = param_file.get("file_name", "")
                print(f"Device {device_id} is bound to file {file_name}")
                return file_name, param_file
        
        # 見つからない場合は空の情報を返す
        return "", {}
    
    async def apply_parameters(self, device_id, parameters):
        """
        デバイスにコマンドパラメーターを適用
        
        Args:
            device_id: デバイスID
            parameters: 適用するパラメーター
            
        Returns:
            Dict[str, Any]: 実行結果
        """
        try:
            # パラメーターの検証
            if "commands" not in parameters:
                return {"success": False, "message": "無効なパラメーター形式です。'commands'キーが必要です。"}
            
            # キャッシュを更新
            await self._update_parameter_files_cache()
            
            # デバイスがバインドされているファイルを確認
            bound_file_name, bound_file_info = await self.get_parameter_file_for_device(device_id)
            
            # バインドされていない場合はエラー
            if not bound_file_name or not bound_file_info:
                return {"success": False, "message": "デバイスにパラメーターファイルがバインドされていません。コンソールでバインドしてください。"}
            
            # コメントとパラメーターを準備
            comment = f"Updated parameters for device {device_id}"
            
            # パラメーターをJSONに変換してBase64エンコード
            command_param_data = {
                "commands": parameters.get("commands", [])
            }
            
            command_param_json = json.dumps(command_param_data, indent=4, ensure_ascii=False)
            encoded_param_data = base64.b64encode(command_param_json.encode('utf-8')).decode('utf-8')
            
            print(f"Preparing to update command parameter file {bound_file_name} for device {device_id}")
            print(f"Encoded contents length: {len(encoded_param_data)} bytes")
            
            # エンコードされたデータが空でないか確認
            if not encoded_param_data:
                print("Generated parameter data is empty")
                return {"success": False, "message": "パラメーターのエンコードに失敗しました"}
            
            try:
                # デバイスをアンバインド
                print(f"Unbinding device {device_id} from file {bound_file_name}")
                unbind_result = await self.aitrios_client.unbind_command_parameter_file(bound_file_name, [device_id])
                
                if unbind_result.get("result") != "SUCCESS":
                    print(f"Unbind may have failed: {unbind_result}")
                else:
                    print(f"Successfully unbound device {device_id} from file {bound_file_name}")
                
                # パラメーターファイルを更新
                print(f"Updating command parameter file {bound_file_name}")
                update_result = await self.aitrios_client.update_command_parameter_file(bound_file_name, comment, encoded_param_data)
                
                if update_result.get("result") != "SUCCESS":
                    print(f"Failed to update parameter file: {update_result}")
                    return {"success": False, "message": f"パラメーターファイルの更新に失敗しました: {update_result.get('message', '')}"}
                
                print(f"Successfully updated parameter file {bound_file_name}")
                
                # デバイスを再バインド
                print(f"Rebinding device {device_id} to file {bound_file_name}")
                bind_result = await self.aitrios_client.bind_command_parameter_file(bound_file_name, [device_id])
                
                if bind_result.get("result") != "SUCCESS":
                    print(f"Failed to bind device: {bind_result}")
                    return {"success": False, "message": f"デバイスのバインドに失敗しました: {bind_result.get('message', '')}"}
                
                print(f"Successfully bound device {device_id} to file {bound_file_name}")
                
                # キャッシュをクリア
                self.cache_timestamp = 0
                
                return {"success": True, "message": f"コマンドパラメーターを正常に適用しました"}
                
            except Exception as api_error:
                print(f"API error while applying command parameters: {str(api_error)}")
                return {"success": False, "message": f"APIエラー: {str(api_error)}"}
            
        except Exception as e:
            print(f"Error applying command parameters for {device_id}: {str(e)}")
            return {"success": False, "message": f"エラーが発生しました: {str(e)}"}
    
    def get_default_parameters(self):
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