#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
画像処理ユーティリティモジュール
画像の処理と変換のためのユーティリティ関数
"""

import base64
import cv2
import numpy as np

def download_image(image_data):
    """
    Base64エンコードされた画像データを画像に変換
    
    Args:
        image_data (str): Base64エンコードされた画像データ
    
    Returns:
        numpy.ndarray: OpenCV画像データ
    """
    image_bytes = base64.b64decode(image_data)
    nparr = np.frombuffer(image_bytes, np.uint8)
    return cv2.imdecode(nparr, cv2.IMREAD_COLOR)

def draw_bounding_boxes(image, detections, objclass, scale_x=1, scale_y=1):
    """
    画像にバウンディングボックスを描画
    
    Args:
        image (numpy.ndarray): 元画像
        detections (list): 検出結果のリスト
        objclass (list): クラスのリスト
        scale_x (float): X方向のスケール係数
        scale_y (float): Y方向のスケール係数
    
    Returns:
        tuple: (描画された画像, 検出ラベルのリスト)
    """
    # 画像のコピーを作成して描画
    result_image = image.copy()
    detection_labels = []
    
    # 検出結果がない場合は元の画像と空のラベルリストを返す
    if not detections:
        return result_image, ["推論結果なし"]
    
    # OpenCVでの色定義 (BGR形式)
    BOX_COLOR = (0, 255, 0)       # 緑色 (検出ボックス)
    TEXT_COLOR = (0, 255, 255)    # 黄色 (テキストの色)
    
    for det in detections:
        left, top, right, bottom = int(det['left'] * scale_x), int(det['top'] * scale_y), int(det['right'] * scale_x), int(det['bottom'] * scale_y)
        
        # クラスIDが範囲内かチェック
        class_id = det['class_id']
        if 0 <= class_id < len(objclass):
            class_name = objclass[class_id]
        else:
            class_name = f"Unknown-{class_id}"
        
        # バウンディングボックスの描画
        cv2.rectangle(result_image, (left, top), (right, bottom), BOX_COLOR, 2)
        
        # ラベルテキストの設定
        label_text = f"Class: {class_name}, Score: {det['score']:.2f}"
        detection_labels.append(label_text)
        
        # ラベルの描画
        cv2.putText(result_image, label_text, (left+2, top+20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, TEXT_COLOR, 1)
    
    return result_image, detection_labels
        
def resize_for_display(image, max_width=800, max_height=600):
    """
    表示用に画像をリサイズ
    
    Args:
        image (numpy.ndarray): リサイズする画像
        max_width (int): 最大幅
        max_height (int): 最大高さ
    
    Returns:
        numpy.ndarray: リサイズされた画像
    """
    height, width = image.shape[:2]
    
    # リサイズが必要ない場合
    if width <= max_width and height <= max_height:
        return image
    
    # アスペクト比を維持してリサイズ
    scale = min(max_width / width, max_height / height)
    new_width = int(width * scale)
    new_height = int(height * scale)
    
    return cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)

def convert_cv_to_pil(cv_image):
    """
    OpenCV画像をPIL画像に変換
    
    Args:
        cv_image (numpy.ndarray): OpenCV形式の画像
    
    Returns:
        PIL.Image: PIL形式の画像
    """
    from PIL import Image
    # BGRからRGBに変換
    rgb_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
    return Image.fromarray(rgb_image)