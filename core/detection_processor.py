#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
物体検出処理モジュール
画像処理と検出のコア機能
"""

import sys
import os
import base64
import time
import cv2
import numpy as np
import threading
from datetime import datetime

# 現在のディレクトリのパスを取得
current_path = os.path.dirname(os.path.abspath(__file__))  # core
root_path = os.path.dirname(current_path)  # プロジェクトルート

# グローバルな変数でモジュールを確保
sys.path.insert(0, root_path)
ObjectDetectionTop = None
BoundingBox = None
BoundingBox2d = None

# モジュールの遅延インポート関数
def ensure_modules_loaded():
    global ObjectDetectionTop, BoundingBox, BoundingBox2d
    if ObjectDetectionTop is None:
        import ObjectDetectionTop
        import BoundingBox
        import BoundingBox2d

from api.aitrios_client import AITRIOSClient
from utils.image_utils import download_image, draw_bounding_boxes

class DetectionProcessor:
    """AITRIOSからの画像取得と物体検出を処理するクラス"""
    
    def __init__(self, aitrios_client, objclass, callback=None):
        """
        検出プロセッサの初期化
        
        Args:
            aitrios_client (AITRIOSClient): AITRIOSとの通信クライアント
            objclass (list): 検出対象のクラスリスト
            callback (function, optional): 結果通知用のコールバック関数
        """
        self.aitrios_client = aitrios_client
        self.objclass = objclass
        self.callback = callback
        self.detected_labels = []
        self.device_monitor_thread = None
        self.device_monitor_flag = threading.Event()
        
        # 初期化時にモジュールを確保
        ensure_modules_loaded()
    
    def set_callback(self, callback):
        """
        コールバック関数をセット
        
        Args:
            callback (function): 結果を通知するコールバック関数
        """
        self.callback = callback
    
    def set_objclass(self, objclass):
        """
        検出オブジェクトのクラスリストを更新
        
        Args:
            objclass (list): 検出対象のクラスリスト
        """
        self.objclass = objclass
    
    def notify_status(self, message):
        """
        ステータスメッセージをコールバックで通知
        
        Args:
            message (str): ステータスメッセージ
        """
        if self.callback:
            self.callback("status", message)
    
    def notify_device_state(self, connection_state, operation_state):
        """
        デバイス状態をコールバックで通知
        
        Args:
            connection_state (str): 接続状態
            operation_state (str): 動作状態
        """
        if self.callback:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.callback("device_state", (connection_state, operation_state, timestamp))
    
    def decode_base64(self, encoded_data):
        """
        Base64エンコードされたデータをデコード
        
        Args:
            encoded_data (str): Base64エンコードされたデータ
        
        Returns:
            bytes: デコードされたバイナリデータ
        """
        return base64.b64decode(encoded_data)

    def deserialize_flatbuffers(self, buf):
        """
        FlatBuffersデータをデシリアライズ（直接インポート方式）
        
        Args:
            buf (bytes): FlatBuffersでシリアライズされたデータ
        
        Returns:
            list: 検出結果のリスト
        """
        try:
            # 現在のディレクトリのパス確認（実行時も確認）
            import sys
            import os
            current_path = os.path.dirname(os.path.abspath(__file__))  # core
            root_path = os.path.dirname(current_path)  # プロジェクトルート
            
            # FlatBuffersファイルの直接インポート
            sys.path.insert(0, root_path)
            
            # 絶対インポートを使用
            import flatbuffers
            from flatbuffers.table import Table
            
            # ObjectDetectionTopの実装を直接組み込む
            table_pos = flatbuffers.encode.Get(flatbuffers.packer.uoffset, buf, 0)
            obj_table = Table(buf, table_pos)
            
            # Perceptionフィールドを取得
            o = flatbuffers.number_types.UOffsetTFlags.py_type(obj_table.Offset(4))
            if o == 0:
                self.notify_status("パーセプションデータなし")
                return []
            
            perception_pos = obj_table.Indirect(o + obj_table.Pos)
            perception_table = Table(buf, perception_pos)
            
            # ObjectDetectionListの長さを取得
            o = flatbuffers.number_types.UOffsetTFlags.py_type(perception_table.Offset(4))
            if o == 0:
                self.notify_status("検出オブジェクトなし")
                return []
            
            list_length = perception_table.VectorLen(o)
            self.notify_status(f"検出オブジェクト数: {list_length}")
            
            results = []
            for i in range(list_length):
                try:
                    # ベクターの要素を取得
                    x = perception_table.Vector(o)
                    x += flatbuffers.number_types.UOffsetTFlags.py_type(i) * 4
                    x = perception_table.Indirect(x)
                    detection_table = Table(buf, x)
                    
                    # ClassIdを取得
                    class_id_offset = flatbuffers.number_types.UOffsetTFlags.py_type(detection_table.Offset(4))
                    class_id = 0
                    if class_id_offset != 0:
                        class_id = detection_table.Get(flatbuffers.number_types.Uint32Flags, class_id_offset + detection_table.Pos)
                    
                    # Scoreを取得
                    score_offset = flatbuffers.number_types.UOffsetTFlags.py_type(detection_table.Offset(10))
                    score = 0.0
                    if score_offset != 0:
                        score = detection_table.Get(flatbuffers.number_types.Float32Flags, score_offset + detection_table.Pos)
                    
                    # BoundingBoxTypeを取得
                    bbox_type_offset = flatbuffers.number_types.UOffsetTFlags.py_type(detection_table.Offset(6))
                    bbox_type = 0
                    if bbox_type_offset != 0:
                        bbox_type = detection_table.Get(flatbuffers.number_types.Uint8Flags, bbox_type_offset + detection_table.Pos)
                    
                    # BoundingBox2dの場合のみ処理
                    if bbox_type == 1:  # BoundingBox2d
                        bbox_offset = flatbuffers.number_types.UOffsetTFlags.py_type(detection_table.Offset(8))
                        if bbox_offset != 0:
                            # BoundingBoxテーブルにアクセス
                            bbox_table = Table(buf, detection_table.Indirect(bbox_offset + detection_table.Pos))
                            
                            # 座標を取得
                            left = top = right = bottom = 0
                            
                            # left
                            left_offset = flatbuffers.number_types.UOffsetTFlags.py_type(bbox_table.Offset(4))
                            if left_offset != 0:
                                left = bbox_table.Get(flatbuffers.number_types.Int32Flags, left_offset + bbox_table.Pos)
                            
                            # top
                            top_offset = flatbuffers.number_types.UOffsetTFlags.py_type(bbox_table.Offset(6))
                            if top_offset != 0:
                                top = bbox_table.Get(flatbuffers.number_types.Int32Flags, top_offset + bbox_table.Pos)
                            
                            # right
                            right_offset = flatbuffers.number_types.UOffsetTFlags.py_type(bbox_table.Offset(8))
                            if right_offset != 0:
                                right = bbox_table.Get(flatbuffers.number_types.Int32Flags, right_offset + bbox_table.Pos)
                            
                            # bottom
                            bottom_offset = flatbuffers.number_types.UOffsetTFlags.py_type(bbox_table.Offset(10))
                            if bottom_offset != 0:
                                bottom = bbox_table.Get(flatbuffers.number_types.Int32Flags, bottom_offset + bbox_table.Pos)
                            
                            # 結果を追加
                            results.append({
                                "class_id": class_id,
                                "score": score,
                                "left": left,
                                "top": top,
                                "right": right,
                                "bottom": bottom
                            })
                except Exception as e:
                    self.notify_status(f"オブジェクト {i} の処理中にエラー: {str(e)}")
            
            # 結果がなかった場合の処理を追加
            if len(results) == 0:
                self.notify_status("推論結果なし")
                
            return results
        except Exception as e:
            self.notify_status(f"デシリアライズエラー: {str(e)}")
            import traceback
            self.notify_status(traceback.format_exc())
            return []
            
            
    def monitor_device_state(self, running_flag):
        """
        デバイス状態を定期的に監視
        
        Args:
            running_flag (threading.Event): 処理実行のフラグ
        """
        while running_flag.is_set():
            try:
                # デバイス状態の取得
                connection_state, operation_state = self.aitrios_client.get_connection_state()
                
                # 状態の通知
                self.notify_device_state(connection_state, operation_state)
                
                # デバイス状態に応じたログ
                if connection_state == "Connected":
                    self.notify_status(f"デバイス接続中: {operation_state}")
                else:
                    self.notify_status(f"デバイス未接続: {connection_state}")
                
                # 10秒ごとに状態を更新
                time.sleep(10)
                
            except Exception as e:
                self.notify_status(f"デバイス状態取得エラー: {str(e)}")
                time.sleep(10)
                
    def process_images(self, running_flag):
        """
        画像取得と検出処理のメインループ
        
        Args:
            running_flag (threading.Event): 処理実行のフラグ
        """
        # 実行時にもパスの設定を確認
        import sys
        import os
        current_path = os.path.dirname(os.path.abspath(__file__))  # core
        root_path = os.path.dirname(current_path)  # プロジェクトルート
        
        if root_path not in sys.path:
            sys.path.insert(0, root_path)
            self.notify_status(f"パスを追加: {root_path}")
        
        # デバイス状態監視スレッドの開始
        self.device_monitor_flag.set()
        self.device_monitor_thread = threading.Thread(
            target=self.monitor_device_state,
            args=(self.device_monitor_flag,)
        )
        self.device_monitor_thread.daemon = True
        self.device_monitor_thread.start()
        
        # 現在のデバイス状態
        current_connection_state = "Unknown"
        current_operation_state = "Unknown"
        
        while running_flag.is_set():
            try:
                # 最新のデバイス状態を取得
                try:
                    connection_state, operation_state = self.aitrios_client.get_connection_state()
                    current_connection_state = connection_state
                    current_operation_state = operation_state
                    self.notify_status(f"デバイス状態: {connection_state} - {operation_state}")
                except Exception as e:
                    self.notify_status(f"デバイス状態取得エラー: {str(e)}")
                
                # StreamingInferenceResultモードでの処理
                if current_connection_state == "Connected" and current_operation_state == "StreamingInferenceResult":
                    self.notify_status("推論結果ストリーミングモードで動作中")
                    
                    # 推論結果のみを取得
                    inference_results = self.aitrios_client.get_inference_results(1)
                    
                    if isinstance(inference_results, list) and len(inference_results) > 0:
                        result = inference_results[0]
                        if "inference_result" in result and "Inferences" in result["inference_result"]:
                            for inference in result["inference_result"]["Inferences"]:
                                if "O" in inference:
                                    try:
                                        # メタデータのデコードとデシリアライズ
                                        decoded_data = self.decode_base64(inference["O"])
                                        deserialized_data = self.deserialize_flatbuffers(decoded_data)
                                        
                                        # 真っ黒な320x320の画像を生成
                                        self.notify_status("黒画像に推論結果を表示")
                                        image = np.zeros((320, 320, 3), dtype=np.uint8)  # 黒い画像
                                        
                                        # バウンディングボックスの描画と検出情報の取得
                                        image_with_boxes, detection_labels = draw_bounding_boxes(image, deserialized_data, self.objclass, scale_x=1, scale_y=1)
                                        
                                        # 検出情報を保存
                                        self.detected_labels = detection_labels
                                        
                                        # 画像をjpegで保存
                                        output_path = 'jpeg.jpg'
                                        cv2.imwrite(output_path, image_with_boxes)
                                        
                                        # GUIに画像とステータスを表示
                                        if self.callback:
                                            # OpenCV画像をRGB形式に変換
                                            self.callback("image", image_with_boxes)
                                            self.callback("detection", self.detected_labels)
                                    except Exception as e:
                                        self.notify_status(f"推論結果処理エラー: {str(e)}")
                                    
                                    break  # 最初の推論結果のみを処理
                    
                    # 短い間隔で更新
                    time.sleep(1)
                    continue
                
                # 通常モードでの処理 (画像取得を含む)
                # 画像ディレクトリの取得
                directories = self.aitrios_client.get_image_directories()
                if not directories or not directories[0]['devices']:
                    self.notify_status("画像ディレクトリが見つかりません")
                    time.sleep(5)
                    continue

                # 最新の1つの画像サブディレクトリ名を取得
                latest_subdirs = directories[0]['devices'][0]['Image'][-1:]

                for i, subdir in enumerate(reversed(latest_subdirs)):
                    if not running_flag.is_set():
                        break
                    
                    # 最新の画像を取得
                    self.notify_status(f"{subdir}から最新画像を取得中")
                    image_data = self.aitrios_client.get_images(subdir)
                    
                    if not image_data or 'images' not in image_data or len(image_data['images']) == 0:
                        self.notify_status(f"サブディレクトリ {subdir} に画像が見つかりません")
                        continue
                    
                    # 最新画像の情報を取得
                    latest_image = image_data['images'][0]
                    image_name = latest_image["name"]
                    image_timestamp = image_name.split('.')[0]  # 拡張子を除いたファイル名（タイムスタンプ）
                    
                    self.notify_status(f"最新画像: {image_name}, タイムスタンプ: {image_timestamp}")
                    
                    # 推論結果を取得
                    self.notify_status("推論結果を取得中")
                    inference_results = self.aitrios_client.get_inference_results(10)
                    
                    found_matching_inference = False
                    matching_inference = None
                    
                    # 推論結果から画像のタイムスタンプと一致するものを探す
                    if isinstance(inference_results, list) and len(inference_results) > 0:
                        for result in inference_results:
                            if "inference_result" in result and "Inferences" in result["inference_result"]:
                                for inference in result["inference_result"]["Inferences"]:
                                    if "T" in inference and inference["T"] == image_timestamp:
                                        matching_inference = inference
                                        found_matching_inference = True
                                        self.notify_status(f"画像 {image_name} に対応する推論結果を発見")
                                        break
                                if found_matching_inference:
                                    break
                    
                    # 一致する推論結果が見つからない場合
                    if not found_matching_inference:
                        self.notify_status(f"画像 {image_name} に対応する推論結果が見つかりません")
                        
                        # この部分を追加：推論結果がなくても画像を表示
                        try:
                            # 画像をダウンロード
                            image = download_image(latest_image["contents"])
                            
                            # 推論結果なしの場合でも画像を表示
                            detection_labels = ["推論結果なし"]
                            self.detected_labels = detection_labels
                            
                            # 画像をjpegで保存
                            output_path = 'jpeg.jpg'
                            cv2.imwrite(output_path, image)
                            
                            # GUIに画像とステータスを表示
                            if self.callback:
                                self.callback("image", image)
                                self.callback("detection", self.detected_labels)
                        except Exception as e:
                            self.notify_status(f"画像処理エラー: {str(e)}")
                        
                        continue
                    
                    # 対応する推論結果が見つかった場合の処理
                    if matching_inference and "O" in matching_inference:
                        try:
                            # メタデータのデコードとデシリアライズ
                            decoded_data = self.decode_base64(matching_inference["O"])
                            deserialized_data = self.deserialize_flatbuffers(decoded_data)
                            
                            # 画像をダウンロード
                            image = download_image(latest_image["contents"])
                            
                            # バウンディングボックスの描画と検出情報の取得
                            image_with_boxes, detection_labels = draw_bounding_boxes(image, deserialized_data, self.objclass, scale_x=1, scale_y=1)
                            
                            # 検出情報を保存
                            self.detected_labels = detection_labels
                            
                            # 画像をjpegで保存
                            output_path = 'jpeg.jpg'
                            cv2.imwrite(output_path, image_with_boxes)
                            
                            # GUIに画像とステータスを表示
                            if self.callback:
                                # OpenCV画像をRGB形式に変換
                                self.callback("image", image_with_boxes)
                                self.callback("detection", self.detected_labels)
                        except Exception as e:
                            self.notify_status(f"推論結果処理エラー: {str(e)}")
                
                # 処理間隔を設ける
                time.sleep(5)
                
            except Exception as e:
                self.notify_status(f"エラー: {str(e)}")
                time.sleep(5)
        
        # 処理終了時にデバイス監視も終了
        if self.device_monitor_flag.is_set():
            self.device_monitor_flag.clear()
            if self.device_monitor_thread and self.device_monitor_thread.is_alive():
                self.device_monitor_thread.join(1.0)