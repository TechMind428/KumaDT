#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
コマンドパラメータータブUI
コマンドパラメーター設定画面のUIを実装
"""

import tkinter as tk
from tkinter import ttk, messagebox, StringVar, IntVar, DoubleVar
import json
import base64
import re

from core.command_parameter_manager import CommandParameterManager

class CommandParamsTab:
    """
    コマンドパラメータータブのUI実装
    """
    
    def __init__(self, parent, command_param_manager, settings_manager):
        """
        コマンドパラメータータブの初期化
        
        Args:
            parent (tk.Frame): 親ウィジェット
            command_param_manager (CommandParameterManager): コマンドパラメーター管理オブジェクト
            settings_manager (SettingsManager): 設定管理オブジェクト
        """
        self.parent = parent
        self.command_param_manager = command_param_manager
        self.settings_manager = settings_manager
        
        # UIの構築
        self.setup_ui()
    
    def setup_ui(self):
        """
        UIコンポーネントの初期化と配置
        """
        # デバイス選択領域
        self.device_frame = ttk.LabelFrame(self.parent, text="対象デバイス")
        self.device_frame.pack(fill=tk.X, padx=10, pady=5)
        
        device_selection_frame = ttk.Frame(self.device_frame)
        device_selection_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(device_selection_frame, text="デバイス:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        # デバイス選択用のコンボボックス
        self.device_id_var = StringVar()
        self.device_selector = ttk.Combobox(device_selection_frame, textvariable=self.device_id_var, width=50, state="readonly")
        self.device_selector.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        self.device_selector.bind("<<ComboboxSelected>>", self.on_device_selected)
        
        # 取得ボタン
        self.fetch_button = ttk.Button(device_selection_frame, text="取得", command=self.fetch_parameters)
        self.fetch_button.grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        
        # スクロール可能なキャンバス（大きなコンテンツ用）
        self.canvas = tk.Canvas(self.parent)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # スクロールバー
        self.scrollbar = ttk.Scrollbar(self.parent, orient=tk.VERTICAL, command=self.canvas.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # キャンバス内のフレーム
        self.scroll_frame = ttk.Frame(self.canvas)
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scroll_frame, anchor=tk.NW)
        
        # パラメーター設定領域
        self.params_frame = ttk.LabelFrame(self.scroll_frame, text="コマンドパラメーター設定")
        self.params_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # アップロードモード設定
        mode_frame = ttk.LabelFrame(self.params_frame, text="アップロードモード")
        mode_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.param_mode = IntVar(value=2)  # デフォルトは推論結果のみ
        ttk.Radiobutton(mode_frame, text="入力画像のみ (0)", variable=self.param_mode, value=0, command=self.update_ui_by_mode).pack(anchor=tk.W, padx=5, pady=2)
        ttk.Radiobutton(mode_frame, text="入力画像と推論結果 (1)", variable=self.param_mode, value=1, command=self.update_ui_by_mode).pack(anchor=tk.W, padx=5, pady=2)
        ttk.Radiobutton(mode_frame, text="推論結果のみ (2)", variable=self.param_mode, value=2, command=self.update_ui_by_mode).pack(anchor=tk.W, padx=5, pady=2)
        
        # 画像アップロード設定
        self.img_upload_frame = ttk.LabelFrame(self.params_frame, text="画像アップロード設定")
        self.img_upload_frame.pack(fill=tk.X, padx=5, pady=5)
        
        img_upload_grid = ttk.Frame(self.img_upload_frame)
        img_upload_grid.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(img_upload_grid, text="アップロード方法:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.upload_method_var = StringVar(value="HTTPStorage")
        upload_method_cb = ttk.Combobox(img_upload_grid, textvariable=self.upload_method_var, state="readonly", width=20)
        upload_method_cb['values'] = ("HTTPStorage", "BlobStorage")
        upload_method_cb.grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
        
        ttk.Label(img_upload_grid, text="ストレージ名:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.storage_name_var = StringVar(value="http://localhost:8080")
        ttk.Entry(img_upload_grid, textvariable=self.storage_name_var, width=40).grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)
        
        ttk.Label(img_upload_grid, text="サブディレクトリパス:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        self.storage_subdir_var = StringVar(value="/image/{device_id}")
        ttk.Entry(img_upload_grid, textvariable=self.storage_subdir_var, width=40).grid(row=2, column=1, sticky=tk.W, padx=5, pady=2)
        
        ttk.Label(img_upload_grid, text="ファイル形式:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=2)
        self.file_format_var = StringVar(value="JPG")
        file_format_cb = ttk.Combobox(img_upload_grid, textvariable=self.file_format_var, state="readonly", width=10)
        file_format_cb['values'] = ("JPG", "BMP")
        file_format_cb.grid(row=3, column=1, sticky=tk.W, padx=5, pady=2)
        
        # 推論結果アップロード設定
        self.ir_upload_frame = ttk.LabelFrame(self.params_frame, text="推論結果アップロード設定")
        self.ir_upload_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ir_upload_grid = ttk.Frame(self.ir_upload_frame)
        ir_upload_grid.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(ir_upload_grid, text="アップロード方法:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.upload_method_ir_var = StringVar(value="HTTPStorage")
        upload_method_ir_cb = ttk.Combobox(ir_upload_grid, textvariable=self.upload_method_ir_var, state="readonly", width=20)
        upload_method_ir_cb['values'] = ("HTTPStorage", "Mqtt")
        upload_method_ir_cb.grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
        
        ttk.Label(ir_upload_grid, text="ストレージ名:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.storage_name_ir_var = StringVar(value="http://localhost:8080")
        ttk.Entry(ir_upload_grid, textvariable=self.storage_name_ir_var, width=40).grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)
        
        ttk.Label(ir_upload_grid, text="サブディレクトリパス:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        self.storage_subdir_ir_var = StringVar(value="/meta/{device_id}")
        ttk.Entry(ir_upload_grid, textvariable=self.storage_subdir_ir_var, width=40).grid(row=2, column=1, sticky=tk.W, padx=5, pady=2)
        
        # 画像切り抜き設定
        crop_frame = ttk.LabelFrame(self.params_frame, text="画像切り抜き設定")
        crop_frame.pack(fill=tk.X, padx=5, pady=5)
        
        crop_grid = ttk.Frame(crop_frame)
        crop_grid.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(crop_grid, text="横オフセット:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.crop_h_offset_var = IntVar(value=0)
        ttk.Entry(crop_grid, textvariable=self.crop_h_offset_var, width=10).grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
        
        ttk.Label(crop_grid, text="縦オフセット:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=2)
        self.crop_v_offset_var = IntVar(value=0)
        ttk.Entry(crop_grid, textvariable=self.crop_v_offset_var, width=10).grid(row=0, column=3, sticky=tk.W, padx=5, pady=2)
        
        ttk.Label(crop_grid, text="横サイズ:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.crop_h_size_var = IntVar(value=4056)
        ttk.Entry(crop_grid, textvariable=self.crop_h_size_var, width=10).grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)
        
        ttk.Label(crop_grid, text="縦サイズ:").grid(row=1, column=2, sticky=tk.W, padx=5, pady=2)
        self.crop_v_size_var = IntVar(value=3040)
        ttk.Entry(crop_grid, textvariable=self.crop_v_size_var, width=10).grid(row=1, column=3, sticky=tk.W, padx=5, pady=2)
        
        # アップロードパラメーター
        upload_params_frame = ttk.LabelFrame(self.params_frame, text="アップロードパラメーター")
        upload_params_frame.pack(fill=tk.X, padx=5, pady=5)
        
        upload_params_grid = ttk.Frame(upload_params_frame)
        upload_params_grid.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(upload_params_grid, text="画像数(0=無制限):").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.num_images_var = IntVar(value=0)
        ttk.Entry(upload_params_grid, textvariable=self.num_images_var, width=10).grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
        
        ttk.Label(upload_params_grid, text="アップロード間隔(秒):").grid(row=0, column=2, sticky=tk.W, padx=5, pady=2)
        self.upload_interval_var = IntVar(value=60)
        ttk.Entry(upload_params_grid, textvariable=self.upload_interval_var, width=10).grid(row=0, column=3, sticky=tk.W, padx=5, pady=2)
        
        ttk.Label(upload_params_grid, text="1メッセージあたりの推論数:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.num_inferences_var = IntVar(value=1)
        ttk.Entry(upload_params_grid, textvariable=self.num_inferences_var, width=10).grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)
        
        # PPLパラメーター
        ppl_frame = ttk.LabelFrame(self.params_frame, text="PPLパラメーター")
        ppl_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ppl_grid = ttk.Frame(ppl_frame)
        ppl_grid.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(ppl_grid, text="最大検出数:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.max_detections_var = IntVar(value=1)
        ttk.Entry(ppl_grid, textvariable=self.max_detections_var, width=10).grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
        
        ttk.Label(ppl_grid, text="検出閾値:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=2)
        self.threshold_var = DoubleVar(value=0.3)
        ttk.Entry(ppl_grid, textvariable=self.threshold_var, width=10).grid(row=0, column=3, sticky=tk.W, padx=5, pady=2)
        
        ttk.Label(ppl_grid, text="入力幅:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.input_width_var = IntVar(value=320)
        ttk.Entry(ppl_grid, textvariable=self.input_width_var, width=10).grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)
        
        ttk.Label(ppl_grid, text="入力高さ:").grid(row=1, column=2, sticky=tk.W, padx=5, pady=2)
        self.input_height_var = IntVar(value=320)
        ttk.Entry(ppl_grid, textvariable=self.input_height_var, width=10).grid(row=1, column=3, sticky=tk.W, padx=5, pady=2)
        
        # バインド状態表示 - aitros_meeting_roomの実装から追加
        self.bound_file_info = StringVar()
        ttk.Label(self.params_frame, textvariable=self.bound_file_info).pack(fill=tk.X, padx=5, pady=5)
        
        # 操作ボタン
        button_frame = ttk.Frame(self.params_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=10)
        
        self.apply_button = ttk.Button(button_frame, text="適用", command=self.apply_parameters)
        self.apply_button.pack(side=tk.RIGHT, padx=5)
        
        self.reset_button = ttk.Button(button_frame, text="リセット", command=self.reset_parameters)
        self.reset_button.pack(side=tk.RIGHT, padx=5)
        
        # ステータス表示
        self.status_var = StringVar()
        self.status_label = ttk.Label(self.params_frame, textvariable=self.status_var, foreground="blue")
        self.status_label.pack(fill=tk.X, padx=5, pady=5)
        
        # 結果表示エリア - aitros_meeting_roomの実装から追加
        self.params_result = ttk.Label(self.params_frame, text="", background="#f0f0f0", padding=10)
        self.params_result.pack(fill=tk.X, padx=5, pady=5)
        
        # キャンバスの更新イベント
        self.scroll_frame.bind("<Configure>", self.on_frame_configure)
        self.canvas.bind("<Configure>", self.on_canvas_configure)
        
        # 初期UIの更新
        self.update_ui_by_mode()
        self.update_device_selector()
        self.disable_parameters_ui()
    
    def on_frame_configure(self, event):
        """
        スクロールフレームサイズ変更時のイベントハンドラ
        """
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def on_canvas_configure(self, event):
        """
        キャンバスサイズ変更時のイベントハンドラ
        """
        # キャンバスの幅に合わせてフレームの幅を設定
        self.canvas.itemconfig(self.canvas_window, width=event.width)
    
    def update_device_selector(self):
        """
        デバイスセレクタを更新
        """
        # 設定からデバイスリストを取得
        config = self.settings_manager.config
        devices = config.get('objclass', [])
        
        # デバイスセレクタの選択肢を設定
        device_options = []
        for i, device_name in enumerate(devices):
            device_id = config.get('DEVICE_ID', "")
            if device_id:
                device_options.append(f"{device_name} ({device_id})")
        
        if device_options:
            self.device_selector['values'] = device_options
            self.device_selector.current(0)  # 最初のデバイスを選択
            self.fetch_button.config(state=tk.NORMAL)  # 取得ボタンを有効化
        else:
            self.device_selector['values'] = ["デバイスがありません"]
            self.device_selector.current(0)
            self.fetch_button.config(state=tk.DISABLED)  # 取得ボタンを無効化
            self.disable_parameters_ui()
    
    def on_device_selected(self, event):
        """
        デバイス選択変更時のイベントハンドラ
        """
        # 選択変更時に取得ボタンを有効化
        selected_device = self.device_selector.get()
        if selected_device and selected_device != "デバイスがありません":
            self.fetch_button.config(state=tk.NORMAL)
        else:
            self.fetch_button.config(state=tk.DISABLED)
            self.disable_parameters_ui()
    
    def update_ui_by_mode(self):
        """
        選択されたモードに応じてUIを更新
        """
        mode = self.param_mode.get()
        
        # モードに応じて関連UIの表示/非表示を設定
        if mode in [0, 1]:  # 画像のみ または 画像と推論結果
            self.img_upload_frame.pack(fill=tk.X, padx=5, pady=5)
        else:
            self.img_upload_frame.pack_forget()
        
        if mode in [1, 2]:  # 推論結果のみ または 画像と推論結果
            self.ir_upload_frame.pack(fill=tk.X, padx=5, pady=5)
        else:
            self.ir_upload_frame.pack_forget()
    
    def disable_parameters_ui(self):
        """
        パラメーターUI要素を無効化
        """
        # パラメーター設定部分を無効化
        for child in self.params_frame.winfo_children():
            for widget in child.winfo_children():
                if isinstance(widget, (ttk.Entry, ttk.Combobox, ttk.Radiobutton, ttk.Button)) and widget != self.fetch_button:
                    widget.configure(state=tk.DISABLED)
        
        # ボタンも無効化
        self.apply_button.configure(state=tk.DISABLED)
        self.reset_button.configure(state=tk.DISABLED)
    
    def enable_parameters_ui(self):
        """
        パラメーターUI要素を有効化
        """
        # パラメーター設定部分を有効化
        for child in self.params_frame.winfo_children():
            for widget in child.winfo_children():
                if isinstance(widget, (ttk.Entry, ttk.Combobox, ttk.Radiobutton)):
                    widget.configure(state=tk.NORMAL)
                # コンボボックスはreadonlyに
                if isinstance(widget, ttk.Combobox):
                    widget.configure(state="readonly")
        
        # ボタンも有効化
        self.apply_button.configure(state=tk.NORMAL)
        self.reset_button.configure(state=tk.NORMAL)
        
        # モードに応じたUI更新
        self.update_ui_by_mode()
    
    def fetch_parameters(self):
        """
        デバイスからパラメーターを取得
        """
        # 選択されたデバイスからIDを抽出
        selected_device = self.device_selector.get()
        if not selected_device or selected_device == "デバイスがありません":
            self.status_var.set("デバイスが選択されていません")
            return
        
        # デバイスIDの取得（括弧内の文字列を抽出）
        match = re.search(r'\((.*?)\)', selected_device)
        if match:
            device_id = match.group(1)
        else:
            # デバイスIDがない場合は設定から取得
            device_id = self.settings_manager.config.get('DEVICE_ID', "")
        
        if not device_id:
            self.status_var.set("デバイスIDが取得できません")
            return
        
        # ステータス更新
        self.status_var.set(f"パラメーター取得中... ({device_id})")
        self.parent.update()  # UI更新
        
        # バックグラウンドでのパラメーター取得は本来は非同期で行うべきだが
        # ここではシンプルに同期的に実装
        try:
            # まずデバイスがバインドされているファイルを確認
            bound_file_name, bound_file_info = self.command_param_manager.get_parameter_file_for_device(device_id)
            
            if not bound_file_name:
                self.status_var.set("デバイスにパラメーターファイルがバインドされていません")
                self.params_result.config(text="デバイスにパラメーターファイルがバインドされていません。\nコンソールでバインドしてください。")
                self.disable_parameters_ui()
                return
            
            # バインド情報を表示
            self.bound_file_info.set(f"バインドファイル: {bound_file_name}")
            
            # パラメーターを取得
            parameters = self.command_param_manager.get_device_parameters(device_id)
            self.set_parameters_to_ui(parameters)
            self.enable_parameters_ui()
            self.status_var.set(f"パラメーター取得完了 ({device_id})")
            self.params_result.config(text="")
        except Exception as e:
            self.status_var.set(f"エラー: {str(e)}")
            self.params_result.config(text=f"パラメーター取得エラー: {str(e)}")
            messagebox.showerror("パラメーター取得エラー", f"パラメーターの取得中にエラーが発生しました:\n{str(e)}")
    
    def set_parameters_to_ui(self, parameters):
        """
        パラメーターをUIに設定
        
        Args:
            parameters (dict): パラメーター辞書
        """
        try:
            # コマンドパラメーターからStartUploadInferenceDataを取得
            commands = parameters.get("commands", [])
            start_upload_cmd = None
            
            for cmd in commands:
                if cmd.get("command_name") == "StartUploadInferenceData":
                    start_upload_cmd = cmd
                    break
            
            if not start_upload_cmd or "parameters" not in start_upload_cmd:
                self.status_var.set("パラメーターフォーマットが無効です")
                return
            
            params = start_upload_cmd["parameters"]
            
            # 基本パラメーター
            self.param_mode.set(params.get("Mode", 2))
            
            # 画像アップロード設定
            self.upload_method_var.set(params.get("UploadMethod", "HTTPStorage"))
            self.storage_name_var.set(params.get("StorageName", "http://localhost:8080"))
            self.storage_subdir_var.set(params.get("StorageSubDirectoryPath", "/image/{device_id}"))
            self.file_format_var.set(params.get("FileFormat", "JPG"))
            
            # 推論結果アップロード設定
            self.upload_method_ir_var.set(params.get("UploadMethodIR", "HTTPStorage"))
            self.storage_name_ir_var.set(params.get("StorageNameIR", "http://localhost:8080"))
            self.storage_subdir_ir_var.set(params.get("StorageSubDirectoryPathIR", "/meta/{device_id}"))
            
            # 画像切り抜き設定
            self.crop_h_offset_var.set(params.get("CropHOffset", 0))
            self.crop_v_offset_var.set(params.get("CropVOffset", 0))
            self.crop_h_size_var.set(params.get("CropHSize", 4056))
            self.crop_v_size_var.set(params.get("CropVSize", 3040))
            
            # アップロードパラメーター
            self.num_images_var.set(params.get("NumberOfImages", 0))
            self.upload_interval_var.set(params.get("UploadInterval", 60))
            self.num_inferences_var.set(params.get("NumberOfInferencesPerMessage", 1))
            
            # PPLパラメーター
            ppl_params = params.get("PPLParameter", {})
            self.max_detections_var.set(ppl_params.get("max_detections", 1))
            self.threshold_var.set(ppl_params.get("threshold", 0.3))
            self.input_width_var.set(ppl_params.get("input_width", 320))
            self.input_height_var.set(ppl_params.get("input_height", 320))
            
            # モードに応じたUI更新
            self.update_ui_by_mode()
            
        except Exception as e:
            self.status_var.set(f"パラメーター設定エラー: {str(e)}")
            messagebox.showerror("パラメーター設定エラー", f"UIへのパラメーター設定中にエラーが発生しました:\n{str(e)}")
    
    def get_parameters_from_ui(self):
        """
        UIからコマンドパラメーターを取得
        
        Returns:
            dict: パラメーター辞書
        """
        try:
            # 基本パラメーター
            mode = int(self.param_mode.get())
            
            # 画像アップロード設定
            upload_method = self.upload_method_var.get()
            storage_name = self.storage_name_var.get()
            storage_sub_dir = self.storage_subdir_var.get()
            file_format = self.file_format_var.get()
            
            # 推論結果アップロード設定
            upload_method_ir = self.upload_method_ir_var.get()
            storage_name_ir = self.storage_name_ir_var.get()
            storage_sub_dir_ir = self.storage_subdir_ir_var.get()
            
            # 画像切り抜き設定
            crop_h_offset = int(self.crop_h_offset_var.get())
            crop_v_offset = int(self.crop_v_offset_var.get())
            crop_h_size = int(self.crop_h_size_var.get())
            crop_v_size = int(self.crop_v_size_var.get())
            
            # アップロードパラメーター
            num_images = int(self.num_images_var.get())
            upload_interval = int(self.upload_interval_var.get())
            num_inferences = int(self.num_inferences_var.get())
            
            # PPLパラメーター
            max_detections = int(self.max_detections_var.get())
            threshold = float(self.threshold_var.get())
            input_width = int(self.input_width_var.get())
            input_height = int(self.input_height_var.get())
            
            # コマンドパラメーターを構築
            parameters = {
                "commands": [
                    {
                        "command_name": "StartUploadInferenceData",
                        "parameters": {
                            "Mode": mode,
                            "UploadMethod": upload_method,
                            "StorageName": storage_name,
                            "StorageSubDirectoryPath": storage_sub_dir,
                            "FileFormat": file_format,
                            "UploadMethodIR": upload_method_ir,
                            "StorageNameIR": storage_name_ir,
                            "StorageSubDirectoryPathIR": storage_sub_dir_ir,
                            "CropHOffset": crop_h_offset,
                            "CropVOffset": crop_v_offset,
                            "CropHSize": crop_h_size,
                            "CropVSize": crop_v_size,
                            "NumberOfImages": num_images,
                            "UploadInterval": upload_interval,
                            "NumberOfInferencesPerMessage": num_inferences,
                            "MaxDetectionsPerFrame": max_detections,
                            "PPLParameter": {
                                "header": {
                                    "id": "00",
                                    "version": "01.01.00"
                                },
                                "dnn_output_detections": 100,
                                "max_detections": max_detections,
                                "threshold": threshold,
                                "input_width": input_width,
                                "input_height": input_height
                            }
                        }
                    }
                ]
            }
            
            return parameters
        except Exception as e:
            print(f"UIからパラメーター取得エラー: {str(e)}")
            return None
                
    def validate_parameters(self):
        """
        パラメーターのバリデーション
        
        Returns:
            bool: バリデーション結果
        """
        try:
            # 必須項目のチェック
            mode = self.param_mode.get()
            
            # 画像アップロード設定のチェック
            if mode in [0, 1]:
                if not self.storage_name_var.get().strip():
                    messagebox.showerror("バリデーションエラー", "ストレージ名は必須です")
                    return False
                
                if not self.storage_subdir_var.get().strip():
                    messagebox.showerror("バリデーションエラー", "サブディレクトリパスは必須です")
                    return False
            
            # 推論結果アップロード設定のチェック
            if mode in [1, 2]:
                if not self.storage_name_ir_var.get().strip():
                    messagebox.showerror("バリデーションエラー", "推論結果ストレージ名は必須です")
                    return False
                
                if not self.storage_subdir_ir_var.get().strip():
                    messagebox.showerror("バリデーションエラー", "推論結果サブディレクトリパスは必須です")
                    return False
            
            # 数値項目のチェック
            if self.upload_interval_var.get() <= 0:
                messagebox.showerror("バリデーションエラー", "アップロード間隔は1以上の値を設定してください")
                return False
            
            if self.num_inferences_var.get() <= 0:
                messagebox.showerror("バリデーションエラー", "1メッセージあたりの推論数は1以上の値を設定してください")
                return False
            
            if self.max_detections_var.get() <= 0:
                messagebox.showerror("バリデーションエラー", "最大検出数は1以上の値を設定してください")
                return False
            
            if self.threshold_var.get() <= 0 or self.threshold_var.get() >= 1:
                messagebox.showerror("バリデーションエラー", "検出閾値は0より大きく1未満の値を設定してください")
                return False
            
            return True
            
        except Exception as e:
            self.status_var.set(f"バリデーションエラー: {str(e)}")
            messagebox.showerror("バリデーションエラー", f"パラメーターのバリデーション中にエラーが発生しました:\n{str(e)}")
            return False
    
    def apply_parameters(self):
        """パラメーターを適用"""
        try:
            # デバイスIDを取得
            selected_device = self.device_selector.get()
            
            if not selected_device or selected_device == "デバイスがありません":
                self.status_var.set("デバイスが選択されていません")
                return
            
            # デバイスIDの取得（括弧内の文字列を抽出）
            match = re.search(r'\((.*?)\)', selected_device)
            if match:
                device_id = match.group(1)
            else:
                # デバイスIDがない場合は設定から取得
                device_id = self.settings_manager.config.get('DEVICE_ID', "")
            
            if not device_id:
                self.status_var.set("デバイスIDが取得できません")
                return
            
            # パラメーターのバリデーション
            if not self.validate_parameters():
                return
            
            # UIからパラメーターを取得
            parameters = self.get_parameters_from_ui()
            if not parameters:
                return
            
            # 確認ダイアログを表示
            if not messagebox.askyesno("確認", f"パラメーターをデバイス {device_id} に適用しますか？\n(推論を一時停止して適用します)"):
                return
            
            # ステータス更新
            self.status_var.set(f"パラメーター適用中... ({device_id})")
            
            # ボタンを無効化
            self.apply_button.config(state=tk.DISABLED)
            self.parent.update()  # UI更新
            
            # パラメーターを適用
            result = self.command_param_manager.apply_parameters(device_id, parameters)
            if result.get("success", False):
                self.status_var.set(f"パラメーター適用完了 ({device_id})")
                self.params_result.config(text=f"パラメーターが正常に適用されました。", foreground="green")
                messagebox.showinfo("成功", f"パラメーターがデバイス {device_id} に適用されました")
            else:
                self.status_var.set(f"パラメーター適用失敗 ({device_id})")
                self.params_result.config(text=f"エラー: {result.get('message', '不明なエラー')}", foreground="red")
                messagebox.showerror("エラー", f"パラメーターの適用に失敗しました: {result.get('message', '')}")
        except Exception as e:
            self.status_var.set(f"エラー: {str(e)}")
            self.params_result.config(text=f"予期しないエラー: {str(e)}", foreground="red")
            messagebox.showerror("パラメーター適用エラー", f"パラメーターの適用中にエラーが発生しました:\n{str(e)}")
        finally:
            # ボタンを再有効化
            self.apply_button.config(state=tk.NORMAL)
    
    def reset_parameters(self):
        """
        パラメーターをデフォルト値にリセット
        """
        if not messagebox.askyesno("確認", "パラメーターをデフォルト値にリセットしますか？"):
            return
        
        # デフォルトパラメーターを取得
        default_params = self.command_param_manager.get_default_parameters()
        
        # UIに設定
        self.set_parameters_to_ui(default_params)
        self.status_var.set("パラメーターをデフォルト値にリセットしました")
    
    def refresh(self):
        """
        タブの表示時に呼び出される更新処理
        """
        # デバイスセレクタを更新
        self.update_device_selector()