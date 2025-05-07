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