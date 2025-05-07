#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AITRIOS APIクライアント
AITRIOSプラットフォームとの通信を担当するモジュール
"""

import time
import requests
import base64
import settings

# グローバル変数としてアクセストークンとその有効期限を保存
ACCESS_TOKEN = None
TOKEN_EXPIRY = 0

# AITRIOS APIの基本URL
BASE_URL = "https://console.aitrios.sony-semicon.com/api/v1"
PORTAL_URL = "https://auth.aitrios.sony-semicon.com/oauth2/default/v1/token"

class AITRIOSClient:
    """AITRIOSプラットフォームとの通信を行うクライアントクラス"""
    
    def __init__(self, device_id=settings.DEVICE_ID, client_id=settings.CLIENT_ID, 
                 client_secret=settings.CLIENT_SECRET):
        """
        AITRIOSクライアントの初期化
        
        Args:
            device_id (str): デバイスID
            client_id (str): クライアントID
            client_secret (str): クライアントシークレット
        """
        self.device_id = device_id
        self.client_id = client_id
        self.client_secret = client_secret
    
    def get_access_token(self):
        """
        APIアクセストークンを取得する
        
        Returns:
            str: アクセストークン
        """
        global ACCESS_TOKEN, TOKEN_EXPIRY
        current_time = time.time()
        
        # トークンが存在せず、または有効期限が切れている場合、新しいトークンを取得
        if ACCESS_TOKEN is None or current_time >= TOKEN_EXPIRY:
            auth = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()
            headers = {
                "Authorization": f"Basic {auth}",
                "Content-Type": "application/x-www-form-urlencoded"
            }
            data = {
                "grant_type": "client_credentials",
                "scope": "system"
            }
            response = requests.post(PORTAL_URL, headers=headers, data=data)
            if response.status_code == 200:
                token_data = response.json()
                ACCESS_TOKEN = token_data["access_token"]
                # トークンの有効期限を設定（念のため10秒早めに期限切れとする）
                TOKEN_EXPIRY = current_time + token_data.get("expires_in", 3600) - 10
            else:
                raise Exception(f"Failed to obtain access token: {response.text}")
        
        return ACCESS_TOKEN
    
    def get_device_info(self):
        """
        デバイスの情報を取得
        
        Returns:
            dict: デバイス情報
        """
        headers = {
            "Authorization": f"Bearer {self.get_access_token()}",
            "Content-Type": "application/json"
        }
        url = f"{BASE_URL}/devices/{self.device_id}"
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to get device info: {response.status_code} - {response.text}")
    
    def get_connection_state(self):
        """
        デバイスの接続状態を取得
        
        Returns:
            tuple: (接続状態, 動作状態)
            接続状態: "Connected" または "Disconnected"
            動作状態: "Idle", "StreamingImage", "StreamingInferenceResult" または "StreamingBoth"
        """
        try:
            device_info = self.get_device_info()
            
            # 接続状態の取得
            connection_state = device_info.get("connectionState", "Unknown")
            
            # 動作状態の取得（階層構造からの抽出）
            state = device_info.get("state", {})
            status = state.get("Status", {})
            operation_state = status.get("ApplicationProcessor", "Unknown")
            
            return connection_state, operation_state
        except Exception as e:
            print(f"Error getting connection state: {str(e)}")
            return "Unknown", "Unknown"
    
    def get_image_directories(self):
        """
        デバイスの画像ディレクトリ一覧を取得
        
        Returns:
            dict: 画像ディレクトリ情報
        """
        headers = {
            "Authorization": f"Bearer {self.get_access_token()}",
            "Content-Type": "application/json"
        }
        url = f"{BASE_URL}/devices/images/directories"
        params = {"device_id": self.device_id}
        response = requests.get(url, headers=headers, params=params)
        print("response=", response.status_code)
        return response.json()
    
    def get_images(self, sub_directory_name, file_name=None):
        """
        指定したサブディレクトリから画像を取得
        
        Args:
            sub_directory_name (str): サブディレクトリ名
            file_name (str, optional): ファイル名
        
        Returns:
            dict: 画像データを含むレスポンス
        """
        headers = {
            "Authorization": f"Bearer {self.get_access_token()}",
            "Content-Type": "application/json"
        }
        url = f"{BASE_URL}/devices/{self.device_id}/images/directories/{sub_directory_name}"
        params = {"order_by": "DESC", "number_of_images": 1}  # 最新の画像を1つだけ取得
        response = requests.get(url, headers=headers, params=params)
        return response.json()
    
    def get_inference_results(self, number_of_inference_results=5, filter=None):
        """
        デバイスの推論結果を取得
        
        Args:
            number_of_inference_results (int): 取得する推論結果の数
            filter (str, optional): フィルタ条件
        
        Returns:
            dict: 推論結果
        """
        headers = {
            "Authorization": f"Bearer {self.get_access_token()}",
            "Content-Type": "application/json"
        }
        url = f"{BASE_URL}/devices/{self.device_id}/inferenceresults"
        params = {
            "NumberOfInferenceresults": number_of_inference_results,
            "raw": 1,
            "order_by": "DESC"
        }
        if filter:
            params["filter"] = filter
        
        response = requests.get(url, headers=headers, params=params)
        return response.json()
        
    def start_inference(self):
        """
        デバイスの推論処理を開始する
        
        Returns:
            dict: APIレスポンス
        """
        headers = {
            "Authorization": f"Bearer {self.get_access_token()}",
            "Content-Type": "application/json"
        }
        url = f"{BASE_URL}/devices/{self.device_id}/inferenceresults/collectstart"
        response = requests.post(url, headers=headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to start inference: {response.status_code} - {response.text}")
    
    def stop_inference(self):
        """
        デバイスの推論処理を停止する
        
        Returns:
            dict: APIレスポンス
        """
        headers = {
            "Authorization": f"Bearer {self.get_access_token()}",
            "Content-Type": "application/json"
        }
        url = f"{BASE_URL}/devices/{self.device_id}/inferenceresults/collectstop"
        response = requests.post(url, headers=headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to stop inference: {response.status_code} - {response.text}")
    # パラメーターファイル一覧を取得するメソッドを追加

    def get_command_parameter_files(self):
        """
        Consoleに登録されているコマンドパラメーターファイル一覧を取得
        
        Returns:
            Dict[str, Any]: ファイル一覧とバインド情報
        """
        headers = {
            "Authorization": f"Bearer {self.get_access_token()}",
            "Content-Type": "application/json"
        }
        url = f"{BASE_URL}/command_parameter_files"
        
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            response_text = response.text
            raise Exception(f"Failed to get command parameter files: {response.status_code} - {response_text}")
    
    def unbind_command_parameter_file(self, file_name, device_ids):
        """
        デバイスからコマンドパラメーターファイルをアンバインド
        
        Args:
            file_name (str): アンバインドするコマンドパラメーターファイル名
            device_ids (list): アンバインド対象のデバイスIDリスト
        
        Returns:
            Dict[str, Any]: API応答
        """
        if not device_ids:
            print(f"No device IDs provided for unbinding from {file_name}")
            return {"result": "SUCCESS", "message": "No devices to unbind"}
            
        token = self.get_access_token()
        
        # 正しいエンドポイントとURLを使用
        url = f"{BASE_URL}/devices/configuration/command_parameter_files/{file_name}"
        
        # API仕様に基づいた正しいデータ形式（カンマ区切りの文字列）
        device_ids_str = ",".join(device_ids)
        data = {
            "device_ids": device_ids_str
        }
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        print(f"Unbinding command parameter file {file_name} from devices: {device_ids}")
        
        try:
            # DELETEメソッドでJSONデータを送信
            response = requests.delete(url, headers=headers, json=data)
            
            # 200または404なら成功 (404はファイルが存在しない場合)
            if response.status_code == 200 or response.status_code == 404:
                try:
                    return response.json()
                except:
                    return {"result": "SUCCESS"}
            else:
                # エラーメッセージを記録するが例外は発生させない
                print(f"Failed to unbind command parameter file: {response.status_code} - {response.text}")
                return {"result": "ERROR", "message": f"Unbind failed: {response.text}"}
        except Exception as e:
            print(f"Exception in unbind_command_parameter_file: {str(e)}")
            return {"result": "ERROR", "message": f"Exception: {str(e)}"}
    
    def update_command_parameter_file(self, file_name, comment, contents):
        """
        既存のコマンドパラメーターファイルを更新
        
        Args:
            file_name (str): コマンドパラメーターファイル名
            comment (str): コメント
            contents (str): Base64エンコードされたファイルの内容
        
        Returns:
            Dict[str, Any]: API応答
        """
        token = self.get_access_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        url = f"{BASE_URL}/command_parameter_files/{file_name}"
        
        # CommandParamUpdate.pyと同じリクエスト形式
        data = {
            "parameter": contents,  # parameterが正しいキー名
            "comment": comment
        }
        
        print(f"Updating command parameter file: {file_name}")
        print(f"Parameter length: {len(contents)}")
        
        response = requests.patch(url, headers=headers, json=data)
        response_text = response.text
        print(f"Update response status: {response.status_code}, body: {response_text}")
        
        if response.status_code == 200:
            try:
                return json.loads(response_text)
            except:
                return {"result": "SUCCESS"}
        else:
            print(f"Failed to update command parameter file: {response.status_code} - {response_text}")
            return {"result": "ERROR", "message": f"Update failed: {response_text}"}
    
    def bind_command_parameter_file(self, file_name, device_ids):
        """
        コマンドパラメーターファイルをデバイスにバインド
        
        Args:
            file_name (str): コマンドパラメーターファイル名
            device_ids (list): バインド対象のデバイスIDリスト
        
        Returns:
            Dict[str, Any]: API応答
        """
        if not device_ids:
            print(f"No device IDs provided for binding to {file_name}")
            return {"result": "SUCCESS", "message": "No devices to bind"}
            
        token = self.get_access_token()
        
        # 正しいエンドポイントと形式
        url = f"{BASE_URL}/devices/configuration/command_parameter_files/{file_name}"
        
        # API仕様に基づいた正しいデータ形式（カンマ区切りの文字列）
        device_ids_str = ",".join(device_ids)
        data = {
            "device_ids": device_ids_str
        }
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        print(f"Binding command parameter file {file_name} to devices: {device_ids}")
        
        try:
            # PUTメソッドでJSONデータを送信
            response = requests.put(url, headers=headers, json=data)
            response_text = response.text
            print(f"Bind response status: {response.status_code}, body: {response_text}")
            
            if response.status_code == 200:
                try:
                    return json.loads(response_text)
                except:
                    return {"result": "SUCCESS"}
            else:
                print(f"Failed to bind command parameter file: {response.status_code} - {response_text}")
                return {"result": "ERROR", "message": f"Bind failed: {response_text}"}
        except Exception as e:
            print(f"Exception in bind_command_parameter_file: {str(e)}")
            return {"result": "ERROR", "message": f"Exception: {str(e)}"}