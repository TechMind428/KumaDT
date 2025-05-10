#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
メインタブUI
モニタリング画面のUIを実装
"""

import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from utils.image_utils import convert_cv_to_pil

class MainTab:
    """メイン監視タブのUI実装"""
    
    def __init__(self, parent):
        """
        メインタブの初期化
        
        Args:
            parent (tk.Frame): 親ウィジェット
        """
        self.parent = parent
        self.setup_ui()
    
    def setup_ui(self):
        """UIコンポーネントの初期化と配置"""
        # 上部フレーム（コントロールパネル）
        self.control_frame = ttk.Frame(self.parent)
        self.control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # コントロールボタン用のフレーム（左寄せ）
        button_frame = ttk.Frame(self.control_frame)
        button_frame.pack(side=tk.LEFT)
        
        # 推論制御ボタン（上段）
        inference_frame = ttk.LabelFrame(button_frame, text="推論制御")
        inference_frame.pack(fill=tk.X, padx=5, pady=2)
        
        self.inference_start_button = ttk.Button(inference_frame, text="推論開始", width=10)
        self.inference_start_button.pack(side=tk.LEFT, padx=5, pady=2)
        
        self.inference_stop_button = ttk.Button(inference_frame, text="推論停止", width=10, state=tk.DISABLED)
        self.inference_stop_button.pack(side=tk.LEFT, padx=5, pady=2)
        
        # 表示制御ボタン（下段）
        display_frame = ttk.LabelFrame(button_frame, text="表示制御")
        display_frame.pack(fill=tk.X, padx=5, pady=2)
        
        self.start_button = ttk.Button(display_frame, text="表示開始", width=10)
        self.start_button.pack(side=tk.LEFT, padx=5, pady=2)
        
        self.stop_button = ttk.Button(display_frame, text="表示停止", width=10, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5, pady=2)
        
        # デバイス状態フレーム
        self.device_frame = ttk.LabelFrame(self.parent, text="デバイス状態")
        self.device_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        # デバイス状態表示
        device_info_frame = ttk.Frame(self.device_frame)
        device_info_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 接続状態
        ttk.Label(device_info_frame, text="接続状態:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.connection_state_var = tk.StringVar(value="Unknown")
        self.connection_state_label = ttk.Label(device_info_frame, textvariable=self.connection_state_var, width=15)
        self.connection_state_label.grid(row=0, column=1, sticky=tk.W, padx=(0, 10))
        
        # 動作状態
        ttk.Label(device_info_frame, text="動作状態:").grid(row=0, column=2, sticky=tk.W, padx=(10, 5))
        self.operation_state_var = tk.StringVar(value="Unknown")
        self.operation_state_label = ttk.Label(device_info_frame, textvariable=self.operation_state_var, width=20)
        self.operation_state_label.grid(row=0, column=3, sticky=tk.W)
        
        # 最終更新時刻
        ttk.Label(device_info_frame, text="最終更新:").grid(row=0, column=4, sticky=tk.W, padx=(10, 5))
        self.last_updated_var = tk.StringVar(value="-")
        ttk.Label(device_info_frame, textvariable=self.last_updated_var).grid(row=0, column=5, sticky=tk.W)
        
        # メインコンテンツフレーム（左右分割）
        self.content_frame = ttk.Frame(self.parent)
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 左側フレーム（画像表示エリア）- 正方形に設定
        self.left_frame_container = ttk.Frame(self.content_frame)
        self.left_frame_container.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 2.5), pady=0)
        
        # 実際の画像表示フレーム - 高さと同じ幅になるように設定
        self.left_frame = ttk.Frame(self.left_frame_container, relief=tk.GROOVE, borderwidth=2)
        self.left_frame.pack(fill=tk.BOTH, expand=True)
        
        # 画像表示用キャンバス
        self.canvas = tk.Canvas(self.left_frame, bg="black")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # 左側フレームの幅を高さに合わせる処理
        self.parent.after(100, self.adjust_left_frame_width)
        
        # ウィンドウサイズ変更イベントを検知
        self.parent.bind("<Configure>", self.on_window_resize)
        
        # 右側フレーム
        self.right_frame = ttk.Frame(self.content_frame)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(2.5, 0), pady=0)
        
        # 検出情報表示エリア
        self.detection_frame = ttk.LabelFrame(self.right_frame, text="検出情報")
        self.detection_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        
        # 検出情報リストボックス
        self.detection_listbox = tk.Listbox(self.detection_frame, font=("Helvetica", 10), height=8)
        self.detection_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 検出リストボックスのスクロールバー
        detection_scrollbar = ttk.Scrollbar(self.detection_listbox, command=self.detection_listbox.yview)
        detection_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.detection_listbox.config(yscrollcommand=detection_scrollbar.set)
        
        # ログエリア
        self.log_frame = ttk.LabelFrame(self.right_frame, text="ログ")
        self.log_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        self.log_text = tk.Text(self.log_frame, height=6, width=40, font=("Helvetica", 9), state=tk.DISABLED)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        # ログのスクロールバー
        log_scrollbar = ttk.Scrollbar(self.log_text, command=self.log_text.yview)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=log_scrollbar.set)
        
        # 画像表示用の変数
        self.photo = None
    
    def on_window_resize(self, event):
        """ウィンドウサイズ変更時に呼ばれるハンドラー"""
        # イベントが左側フレームのものかチェック
        if event.widget == self.parent:
            # 少し遅延してフレームサイズを再調整
            self.parent.after(100, self.adjust_left_frame_width)
    
    def adjust_left_frame_width(self):
        """左側フレームの幅を高さに合わせて正方形にする"""
        # 左側フレームの高さを取得
        height = self.left_frame.winfo_height()
        if height > 1:  # 有効な高さがある場合のみ調整
            # 左側のコンテナフレームの幅を高さと同じに設定
            self.left_frame_container.config(width=height)
            # ウィジェットのサイズ変更を防止
            self.left_frame_container.pack_propagate(False)
            
            # 画像更新時に正しいアスペクト比で表示されるようにキャンバスサイズも調整
            self.canvas.config(width=height, height=height)
        else:
            # まだフレームが表示されていない場合は後で再試行
            self.parent.after(100, self.adjust_left_frame_width)
    
    def set_button_commands(self, start_command, stop_command, inference_start_command=None, inference_stop_command=None):
        """
        ボタンのコマンドを設定
        
        Args:
            start_command (function): 表示開始ボタンのコマンド
            stop_command (function): 表示停止ボタンのコマンド
            inference_start_command (function, optional): 推論開始ボタンのコマンド
            inference_stop_command (function, optional): 推論停止ボタンのコマンド
        """
        self.start_button.config(command=start_command)
        self.stop_button.config(command=stop_command)
        
        if inference_start_command:
            self.inference_start_button.config(command=inference_start_command)
        
        if inference_stop_command:
            self.inference_stop_button.config(command=inference_stop_command)
    
    def set_start_state(self, running=True):
        """
        表示ボタン状態を実行中/停止中に設定
        
        Args:
            running (bool): 実行中かどうか
        """
        if running:
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
        else:
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
    
    def set_inference_state(self, running=True, connection_state="Unknown", operation_state="Unknown"):
        """
        推論ボタン状態を設定
        
        Args:
            running (bool): 推論実行中かどうか
            connection_state (str): デバイス接続状態
            operation_state (str): デバイス動作状態
        """
        # 接続状態がConnectedの場合のみ有効化を検討
        if connection_state == "Connected":
            if operation_state == "Idle":
                # アイドル状態なら推論開始ボタンを有効
                self.inference_start_button.config(state=tk.NORMAL)
                self.inference_stop_button.config(state=tk.DISABLED)
            else:
                # それ以外の状態では推論停止ボタンを有効
                self.inference_start_button.config(state=tk.DISABLED)
                self.inference_stop_button.config(state=tk.NORMAL)
        else:
            # 未接続の場合は両方無効
            self.inference_start_button.config(state=tk.DISABLED)
            self.inference_stop_button.config(state=tk.DISABLED)
                
    def update_log(self, message):
        """
        ログテキストを更新
        
        Args:
            message (str): 表示するログメッセージ
        """
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def update_device_state(self, connection_state, operation_state, timestamp):
        """
        デバイス状態表示を更新
        
        Args:
            connection_state (str): 接続状態
            operation_state (str): 動作状態
            timestamp (str): 更新時刻
        """
        self.connection_state_var.set(connection_state)
        self.operation_state_var.set(operation_state)
        self.last_updated_var.set(timestamp)
        
        # 接続状態に応じたラベルの色設定
        if connection_state == "Connected":
            self.connection_state_label.config(foreground="green")
        elif connection_state == "Disconnected":
            self.connection_state_label.config(foreground="red")
        else:
            self.connection_state_label.config(foreground="orange")
        
        # 推論ボタンの状態も更新
        self.set_inference_state(
            running=(operation_state != "Idle"),
            connection_state=connection_state,
            operation_state=operation_state
        )
    
    def update_image(self, cv_image):
        """
        画像を更新
        
        Args:
            cv_image (numpy.ndarray): OpenCV形式の画像
        """
        # OpenCV画像をPIL形式に変換
        pil_image = convert_cv_to_pil(cv_image)
        
        # キャンバスのサイズを取得
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        # キャンバスがまだ表示されていない場合の対応
        if canvas_width <= 1:
            canvas_width = 320
        if canvas_height <= 1:
            canvas_height = 320
        
        # 画像のリサイズ（アスペクト比を維持）
        img_width, img_height = pil_image.size
        ratio = min(canvas_width/img_width, canvas_height/img_height)
        new_width = int(img_width * ratio)
        new_height = int(img_height * ratio)
        
        pil_image = pil_image.resize((new_width, new_height), Image.LANCZOS)
        
        # PIL画像をTkinter用に変換
        self.photo = ImageTk.PhotoImage(image=pil_image)
        
        # キャンバスをクリアして新しい画像を表示
        self.canvas.delete("all")
        
        # 画像をキャンバスの中央に配置
        x = max(0, (canvas_width - new_width) // 2)
        y = max(0, (canvas_height - new_height) // 2)
        
        self.canvas.create_image(x, y, anchor=tk.NW, image=self.photo)
    
    def update_detection_info(self, detections):
        """
        検出情報を更新
        
        Args:
            detections (list): 検出情報のリスト
        """
        # リストボックスをクリア
        self.detection_listbox.delete(0, tk.END)
        
        # 検出情報がなければその旨を表示
        if not detections:
            self.detection_listbox.insert(tk.END, "検出されたオブジェクトはありません")
        else:
            # すべての検出情報を表示
            for i, detection in enumerate(detections, 1):
                self.detection_listbox.insert(tk.END, f"{i}. {detection}")

    def update_device_state_ui(self, connection_state, operation_state, timestamp):
        """
        デバイス状態表示を更新（ボタン状態の更新なし）
        
        Args:
            connection_state (str): 接続状態
            operation_state (str): 動作状態
            timestamp (str): 更新時刻
        """
        self.connection_state_var.set(connection_state)
        self.operation_state_var.set(operation_state)
        self.last_updated_var.set(timestamp)
        
        # 接続状態に応じたラベルの色設定
        if connection_state == "Connected":
            self.connection_state_label.config(foreground="green")
        elif connection_state == "Disconnected":
            self.connection_state_label.config(foreground="red")
        else:
            self.connection_state_label.config(foreground="orange")