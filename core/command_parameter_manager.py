#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
コマンドパラメーター管理モジュール
AITRIOSデバイスのコマンドパラメーターを管理する
"""

import json
import base64
import logging
from typing import Dict, Any, List, Optional, Tuple

from api.aitrios_client import AITRIOSClient

# ロガーの設定
logger = logging.getLogger(__name__)

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
    
    def get_parameter_file_for_device(self, device_id: str) -> Tuple[str, Dict[str, Any]]:
        """
        デバイスに対応するパラメーターファイル名を取得
        
        Args:
            device_id: デバイスID
            
        Returns:
            Tuple[str, Dict[str, Any]]: (ファイル名, バインド情報)
        """
        try:
            # パラメーターファイル一覧を取得
            files_data = self.aitrios_client.get_command_parameter_files()
            
            # デバッグ情報としてパラメーターファイル一覧の内容を出力
            param_list = files_data.get("parameter_list", [])
            logger.info(f"Parameter files contains {len(param_list)} files")
            
            # このデバイスがバインドされているファイルを確認
            for param_file in param_list:
                device_ids = param_file.get("device_ids", [])
                if device_id in device_ids:
                    file_name = param_file.get("file_name", "")
                    logger.info(f"Device {device_id} is bound to file {file_name}")
                    
                    # ファイルの内容を取得
                    if "parameter" not in param_file:
                        file_data = self.aitrios_client.export_command_parameter_file(file_name)
                        if file_data and "parameter" in file_data:
                            # Base64デコードしてJSONオブジェクトに変換
                            encoded_param = file_data.get("parameter", "")
                            try:
                                decoded_bytes = base64.b64decode(encoded_param)
                                param_json = json.loads(decoded_bytes.decode('utf-8'))
                                param_file["parameter"] = param_json
                            except Exception as e:
                                logger.error(f"Error decoding parameter file: {str(e)}")
                    
                    return file_name, param_file
            
            # 見つからない場合は空の情報を返す
            logger.warning(f"No parameter file found for device {device_id}")
            return "", {}
            
        except Exception as e:
            logger.error(f"Error getting parameter file for device {device_id}: {str(e)}")
            return "", {}
    
    def get_device_parameters(self, device_id: str) -> Dict[str, Any]:
        """
        デバイスの現在のコマンドパラメーターを取得
        
        Args:
            device_id: デバイスID
            
        Returns:
            Dict[str, Any]: コマンドパラメーター
        """
        try:
            # 毎回新しくAITRIOSからパラメーターを取得
            logger.info(f"Getting parameters for device {device_id}")
            
            # デバイスがコマンドパラメーターファイルにバインドされているか確認
            file_name, file_info = self.get_parameter_file_for_device(device_id)
            
            if file_name and "parameter" in file_info:
                # バインドされているファイルからパラメーターを取得
                parameters = file_info["parameter"]
                logger.info(f"Found parameters for device {device_id} in file {file_name}")
                return parameters
            else:
                # バインドされていない場合はデフォルトパラメーターを返す
                logger.warning(f"No parameter file found for device {device_id}, returning defaults")
                return self.get_default_parameters()
                
        except Exception as e:
            logger.error(f"Error getting device parameters for {device_id}: {str(e)}")
            # エラー時はデフォルトパラメーターを返す
            return self.get_default_parameters()
    
    def apply_parameters(self, device_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
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
            if not self._validate_parameters(parameters):
                return {"success": False, "message": "無効なパラメーター形式です。'commands'キーが必要です。"}
            
            # デバイスがバインドされているファイルを確認
            bound_file_name, bound_file_info = self.get_parameter_file_for_device(device_id)
            
            # バインドされていない場合はエラー
            if not bound_file_name:
                return {"success": False, "message": "デバイスにパラメーターファイルがバインドされていません。コンソールでバインドしてください。"}
            
            # コメント設定
            comment = f"Updated parameters for device {device_id}"
            
            # パラメーターをJSONに変換してBase64エンコード
            command_param_data = {
                "commands": parameters.get("commands", [])
            }
            
            command_param_json = json.dumps(command_param_data, indent=4, ensure_ascii=False)
            encoded_param_data = base64.b64encode(command_param_json.encode('utf-8')).decode('utf-8')
            
            logger.info(f"Preparing to update command parameter file {bound_file_name} for device {device_id}")
            logger.info(f"Encoded contents length: {len(encoded_param_data)} bytes")
            
            # エンコードされたデータが空でないか確認
            if not encoded_param_data:
                logger.error("Generated parameter data is empty")
                return {"success": False, "message": "パラメーターのエンコードに失敗しました"}
            
            try:
                # 1. デバイスをアンバインド
                logger.info(f"Unbinding device {device_id} from file {bound_file_name}")
                unbind_result = self.aitrios_client.unbind_command_parameter_file(bound_file_name, [device_id])
                
                if unbind_result.get("result") != "SUCCESS":
                    logger.warning(f"Unbind may have failed: {unbind_result}")
                else:
                    logger.info(f"Successfully unbound device {device_id} from file {bound_file_name}")
                
                # 2. パラメーターファイルを更新
                logger.info(f"Updating command parameter file {bound_file_name}")
                update_result = self.aitrios_client.update_command_parameter_file(bound_file_name, comment, encoded_param_data)
                
                if update_result.get("result") != "SUCCESS":
                    logger.error(f"Failed to update parameter file: {update_result}")
                    return {"success": False, "message": f"パラメーターファイルの更新に失敗しました: {update_result.get('message', '')}"}
                
                logger.info(f"Successfully updated parameter file {bound_file_name}")
                
                # 3. デバイスを再バインド
                logger.info(f"Rebinding device {device_id} to file {bound_file_name}")
                bind_result = self.aitrios_client.bind_command_parameter_file(bound_file_name, [device_id])
                
                if bind_result.get("result") != "SUCCESS":
                    logger.error(f"Failed to bind device: {bind_result}")
                    return {"success": False, "message": f"デバイスのバインドに失敗しました: {bind_result.get('message', '')}"}
                
                logger.info(f"Successfully bound device {device_id} to file {bound_file_name}")
                
                return {"success": True, "message": f"コマンドパラメーターを正常に適用しました"}
                
            except Exception as api_error:
                logger.error(f"API error while applying command parameters: {str(api_error)}")
                return {"success": False, "message": f"APIエラー: {str(api_error)}"}
            
        except Exception as e:
            logger.error(f"Error applying command parameters for {device_id}: {str(e)}")
            return {"success": False, "message": f"エラーが発生しました: {str(e)}"}
    
    def _validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """
        パラメーターのバリデーション
        
        Args:
            parameters: バリデーションするパラメーター
            
        Returns:
            bool: バリデーション結果
        """
        # コマンドが存在するか確認
        if "commands" not in parameters:
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