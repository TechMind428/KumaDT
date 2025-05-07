#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
コマンドパラメータータブUI
コマンドパラメーター設定画面のUIを実装
"""

import tkinter as tk
from tkinter import ttk, messagebox, StringVar, IntVar, DoubleVar
import json
import re
import logging

from core.command_parameter_manager import CommandParameterManager

# ロガーの設定
logger = logging.getLogger(__name__)

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
        # メインフレーム（スクロール可能）
        self.main_frame = ttk.Frame(self.parent)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # キャンバスとスクロールバー
        self.canvas = tk.Canvas(self.main_frame)
        self.scrollbar = ttk.Scrollbar(self.main_frame, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # スクロール可能なフレーム
        self.scrollable_frame = ttk.Frame(self.canvas)
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        
        # デバイス選択領域
        self.device_frame = ttk.LabelFrame(self.scrollable_frame, text="対象デバイス")
        self.device_frame.pack(fill=tk.X, padx=10, pady=5)
        
        device_selection_frame = ttk.Frame(self.device_frame)
        device_selection_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(device_selection_frame, text="デバイスID:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        # デバイスID入力フィールド - 設定画面からのデバイスIDを使用
        self.device_id_var = StringVar()
        self.device_id_entry = ttk.Entry(device_selection_frame, textvariable=self.device_id_var, width=50, state="readonly")
        self.device_id_entry.grid(row=0, column=1, sticky=tk.W+tk.E, padx=5, pady=5)
        
        # バインド情報表示
        self.bound_file_info = ttk.Label(device_selection_frame, text="")
        self.bound_file_info.grid(row=1, column=0, columnspan=3, sticky=tk.W, padx=5, pady=2)
        
        # パラメーター設定領域
        self.params_frame = ttk.LabelFrame(self.scrollable_frame, text="コマンドパラメーター設定")
        self.params_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # アップロードモード設定
        mode_frame = ttk.LabelFrame(self.params_frame, text="アップロードモード")
        mode_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.mode_var = IntVar(value=2)  # デフォルトは推論結果のみ
        ttk.Radiobutton(mode_frame, text="入力画像のみ (0)", variable=self.mode_var, value=0).pack(anchor=tk.W, padx=5, pady=2)
        ttk.Radiobutton(mode_frame, text="入力画像と推論結果 (1)", variable=self.mode_var, value=1).pack(anchor=tk.W, padx=5, pady=2)
        ttk.Radiobutton(mode_frame, text="推論結果のみ (2)", variable=self.mode_var, value=2).pack(anchor=tk.W, padx=5, pady=2)
        
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
        ttk.Entry(img_upload_grid, textvariable=self.storage_name_var, width=40).grid(row=1, column=1, sticky=tk.W+tk.E, padx=5, pady=2)
        
        ttk.Label(img_upload_grid, text="サブディレクトリパス:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        self.storage_subdir_var = StringVar(value="/image/{device_id}")
        ttk.Entry(img_upload_grid, textvariable=self.storage_subdir_var, width=40).grid(row=2, column=1, sticky=tk.W+tk.E, padx=5, pady=2)
        
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
        ttk.Entry(ir_upload_grid, textvariable=self.storage_name_ir_var, width=40).grid(row=1, column=1, sticky=tk.W+tk.E, padx=5, pady=2)
        
        ttk.Label(ir_upload_grid, text="サブディレクトリパス:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        self.storage_subdir_ir_var = StringVar(value="/meta/{device_id}")
        ttk.Entry(ir_upload_grid, textvariable=self.storage_subdir_ir_var, width=40).grid(row=2, column=1, sticky=tk.W+tk.E, padx=5, pady=2)
        
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
        
        # 結果表示エリア
        self.params_result = ttk.Label(self.params_frame, text="", background="#f0f0f0")
        self.params_result.pack(fill=tk.X, padx=5, pady=5)
        
        # 操作ボタン
        button_frame = ttk.Frame(self.params_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=10)
        
        # キャンセルと適用ボタン (右寄せ)
        self.cancel_button = ttk.Button(button_frame, text="キャンセル", command=self.on_cancel)
        self.cancel_button.pack(side=tk.RIGHT, padx=5)
        
        self.apply_button = ttk.Button(button_frame, text="適用", command=self.apply_parameters)
        self.apply_button.pack(side=tk.RIGHT, padx=5)
        
        # スクロールの設定
        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", self.on_canvas_configure)
        
        # マウスホイールのスクロールイベントを設定
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        
        # 初期状態では設定欄を無効化
        self.disable_parameters_ui()
        
        # 初期化時にデバイスIDを取得
        self.load_device_id()
        
        # 100ms後にパラメーター自動取得を実行
        self.parent.after(100, self.fetch_parameters)
    
    def _on_mousewheel(self, event):
        """マウスホイールのスクロールイベント"""
        self.canvas.yview_scroll(-1 * (event.delta // 120), "units")
    
    def on_canvas_configure(self, event):
        """キャンバスのリサイズ時にスクロール可能なフレームの幅を調整"""
        self.canvas.itemconfig(self.canvas_window, width=event.width)
    
    def load_device_id(self):
        """設定画面からデバイスIDを読み込む"""
        # 設定マネージャーからデバイスIDを取得
        device_id = self.settings_manager.config.get('DEVICE_ID', "")
        
        if device_id:
            self.device_id_var.set(device_id)
        else:
            self.device_id_var.set("デバイスIDが設定されていません")
            # デバイスIDがない場合は警告を表示
            self.params_result.config(
                text="デバイスIDが設定されていません。設定画面でデバイスIDを設定してください。",
                foreground="red",
                background="#ffe6e6"
            )
    
    def update_ui_by_mode(self):
        """選択されたモードに応じてUIを更新"""
        # モードによらず全ての項目を表示する（req：常に全項目表示）
        # この関数は何もしない（項目の表示/非表示切り替えをしない）
        pass
    
    def disable_parameters_ui(self):
        """パラメーターUI要素を無効化"""
        # パラメーター設定部分を無効化
        for child in self.params_frame.winfo_children():
            if isinstance(child, ttk.LabelFrame):
                for widget in child.winfo_children():
                    if isinstance(widget, (ttk.Entry, ttk.Combobox, ttk.Radiobutton)):
                        widget.configure(state=tk.DISABLED)
            elif isinstance(widget, ttk.Frame):
                for subwidget in widget.winfo_children():
                    if isinstance(subwidget, (ttk.Entry, ttk.Combobox, ttk.Radiobutton)):
                        subwidget.configure(state=tk.DISABLED)
        
        # ボタンを無効化
        self.apply_button.configure(state=tk.DISABLED)
    
    def enable_parameters_ui(self):
        """パラメーターUI要素を有効化"""
        # パラメーター設定部分を有効化
        for child in self.params_frame.winfo_children():
            if isinstance(child, ttk.LabelFrame):
                for widget in child.winfo_children():
                    if isinstance(widget, ttk.Entry):
                        widget.configure(state=tk.NORMAL)
                    elif isinstance(widget, ttk.Combobox):
                        widget.configure(state="readonly")
                    elif isinstance(widget, ttk.Radiobutton):
                        widget.configure(state=tk.NORMAL)
                    elif isinstance(widget, ttk.Frame):
                        for subwidget in widget.winfo_children():
                            if isinstance(subwidget, ttk.Entry):
                                subwidget.configure(state=tk.NORMAL)
                            elif isinstance(subwidget, ttk.Combobox):
                                subwidget.configure(state="readonly")
                            elif isinstance(subwidget, ttk.Radiobutton):
                                subwidget.configure(state=tk.NORMAL)
            elif isinstance(child, ttk.Frame):
                for widget in child.winfo_children():
                    if isinstance(widget, ttk.Entry):
                        widget.configure(state=tk.NORMAL)
                    elif isinstance(widget, ttk.Combobox):
                        widget.configure(state="readonly")
                    elif isinstance(widget, ttk.Radiobutton):
                        widget.configure(state=tk.NORMAL)
        
        # ボタンを有効化
        self.apply_button.configure(state=tk.NORMAL)
        
        # モードに応じたUI更新
        self.update_ui_by_mode()
    
    def fetch_parameters(self):
        """デバイスからパラメーターを取得"""
        device_id = self.device_id_var.get()
        
        if not device_id or device_id == "デバイスIDが設定されていません":
            messagebox.showerror("エラー", "有効なデバイスIDが設定されていません。")
            return
        
        # ステータス更新
        self.params_result.config(text=f"パラメーター取得中... ({device_id})")
        self.parent.update()  # UI更新
        
        try:
            # APIを使ってコマンドパラメーターファイルの情報を取得
            bound_file_info = None
            try:
                # デバイスに紐づけられたパラメーターファイルとその内容を取得
                file_name, file_info = self.command_param_manager.get_parameter_file_for_device(device_id)
                if file_name:
                    self.bound_file_info.config(
                        text=f"バインドされているファイル: {file_name}",
                        foreground="green"
                    )
                    bound_file_info = file_info
                else:
                    self.bound_file_info.config(
                        text="バインドされているファイルがありません",
                        foreground="red"
                    )
                    messagebox.showwarning("警告", "このデバイスにはコマンドパラメーターファイルがバインドされていません。")
                    return
            except Exception as e:
                print(f"パラメーターファイル情報取得エラー: {str(e)}")
                self.bound_file_info.config(
                    text="バインド情報取得エラー",
                    foreground="red"
                )
            
            # パラメーター取得
            parameters = self.command_param_manager.get_device_parameters(device_id)
            
            # UIにパラメーターを設定
            self.set_parameters_to_ui(parameters)
            
            # UIを有効化
            self.enable_parameters_ui()
            
            # 成功メッセージ
            self.params_result.config(
                text=f"パラメーター取得完了 ({device_id})",
                foreground="green",
                background="#e6ffe6"
            )
        except Exception as e:
            self.params_result.config(
                text=f"エラー: {str(e)}",
                foreground="red",
                background="#ffe6e6"
            )
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
                self.params_result.config(
                    text="パラメーターフォーマットが無効です",
                    foreground="red",
                    background="#ffe6e6"
                )
                return
            
            params = start_upload_cmd["parameters"]
            
            # 基本パラメーター
            self.mode_var.set(params.get("Mode", 2))
            
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
            
            # モードに応じたUI更新を遅延実行
            self.parent.after(100, self.update_ui_by_mode)
            
            # バインド情報を表示
            self.bound_file_info.config(
                text="バインドされているファイル: あり",
                foreground="green"
            )
            
        except Exception as e:
            self.params_result.config(
                text=f"パラメーター設定エラー: {str(e)}",
                foreground="red",
                background="#ffe6e6"
            )
            messagebox.showerror("パラメーター設定エラー", f"UIへのパラメーター設定中にエラーが発生しました:\n{str(e)}")
    
    def get_parameters_from_ui(self):
        """
        UIからパラメーターを取得
        
        Returns:
            dict: パラメーター辞書
        """
        try:
            # 基本パラメーター
            mode = self.mode_var.get()
            
            # デバイスIDからサフィックスを抽出（存在する場合）
            device_id = self.device_id_var.get()
            device_suffix = device_id.split('-')[-1] if device_id and '-' in device_id else device_id
            
            # StorageSubDirectoryPathの{device_id}をサフィックスに置換
            storage_subdir = self.storage_subdir_var.get().replace("{device_id}", device_suffix)
            storage_subdir_ir = self.storage_subdir_ir_var.get().replace("{device_id}", device_suffix)
            
            # パラメーター辞書を構築
            cmd_params = {
                "Mode": mode,
                "UploadInterval": self.upload_interval_var.get(),
                "NumberOfInferencesPerMessage": self.num_inferences_var.get(),
                "CropHOffset": self.crop_h_offset_var.get(),
                "CropVOffset": self.crop_v_offset_var.get(),
                "CropHSize": self.crop_h_size_var.get(),
                "CropVSize": self.crop_v_size_var.get(),
                "NumberOfImages": self.num_images_var.get(),
                "MaxDetectionsPerFrame": self.max_detections_var.get(),
                "PPLParameter": {
                    "header": {
                        "id": "00",
                        "version": "01.01.00"
                    },
                    "dnn_output_detections": 100,
                    "max_detections": self.max_detections_var.get(),
                    "threshold": self.threshold_var.get(),
                    "input_width": self.input_width_var.get(),
                    "input_height": self.input_height_var.get()
                }
            }
            
            # モードに応じたパラメーターを追加
            if mode in [0, 1]:  # 画像のみ または 画像と推論結果
                cmd_params.update({
                    "UploadMethod": self.upload_method_var.get(),
                    "StorageName": self.storage_name_var.get(),
                    "StorageSubDirectoryPath": storage_subdir,
                    "FileFormat": self.file_format_var.get()
                })
            
            if mode in [1, 2]:  # 推論結果のみ または 画像と推論結果
                cmd_params.update({
                    "UploadMethodIR": self.upload_method_ir_var.get(),
                    "StorageNameIR": self.storage_name_ir_var.get(),
                    "StorageSubDirectoryPathIR": storage_subdir_ir
                })
            
            # 最終的なパラメーター形式
            parameters = {
                "commands": [
                    {
                        "command_name": "StartUploadInferenceData",
                        "parameters": cmd_params
                    }
                ]
            }
            
            return parameters
            
        except Exception as e:
            self.params_result.config(
                text=f"パラメーター取得エラー: {str(e)}",
                foreground="red",
                background="#ffe6e6"
            )
            messagebox.showerror("パラメーター取得エラー", f"UIからのパラメーター取得中にエラーが発生しました:\n{str(e)}")
            return None
    
    def validate_parameters(self):
        """
        パラメーターのバリデーション
        
        Returns:
            bool: バリデーション結果
        """
        try:
            # 必須項目のチェック
            mode = self.mode_var.get()
            
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
            self.params_result.config(
                text=f"バリデーションエラー: {str(e)}",
                foreground="red",
                background="#ffe6e6"
            )
            messagebox.showerror("バリデーションエラー", f"パラメーターのバリデーション中にエラーが発生しました:\n{str(e)}")
            return False
    
    def apply_parameters(self):
        """パラメーターを適用"""
        device_id = self.device_id_var.get()
        
        if not device_id or device_id == "デバイスIDが設定されていません":
            messagebox.showerror("エラー", "有効なデバイスIDが設定されていません。")
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
        self.params_result.config(
            text=f"パラメーターを適用中... ({device_id})",
            foreground="blue",
            background="#e6e6ff"
        )
        self.parent.update()  # UI更新
        
        # ボタンを一時的に無効化
        self.apply_button.config(state=tk.DISABLED)
        self.cancel_button.config(state=tk.DISABLED)
        
        try:
            # パラメーターを適用
            result = self.command_param_manager.apply_parameters(device_id, parameters)
            
            # ボタンを再有効化
            self.apply_button.config(state=tk.NORMAL)
            self.cancel_button.config(state=tk.NORMAL)
            
            if result.get("success", False):
                self.params_result.config(
                    text=f"パラメーター適用完了: {result.get('message', '成功')}",
                    foreground="green",
                    background="#e6ffe6"
                )
                messagebox.showinfo("成功", f"パラメーターがデバイス {device_id} に適用されました")
            else:
                self.params_result.config(
                    text=f"パラメーター適用失敗: {result.get('message', 'エラー')}",
                    foreground="red",
                    background="#ffe6e6"
                )
                messagebox.showerror("エラー", f"パラメーターの適用に失敗しました:\n{result.get('message', 'エラー')}")
        except Exception as e:
            # ボタンを再有効化
            self.apply_button.config(state=tk.NORMAL)
            self.cancel_button.config(state=tk.NORMAL)
            
            self.params_result.config(
                text=f"エラー: {str(e)}",
                foreground="red",
                background="#ffe6e6"
            )
            messagebox.showerror("パラメーター適用エラー", f"パラメーターの適用中にエラーが発生しました:\n{str(e)}")
    
    def on_cancel(self):
        """キャンセルボタンのアクション"""
        # 親タブに戻る処理などをここに実装
        if messagebox.askyesno("確認", "変更を破棄してキャンセルしますか？"):
            # タブの選択等の処理が必要な場合は親オブジェクトから実行
            # 実装例: self.parent.master.select(0)  # メインタブに戻る
            pass
    
    def refresh(self):
        """
        タブの表示時に呼び出される更新処理
        """
        # デバイスIDを更新
        self.load_device_id()
        
        # パラメーター自動取得を実行
        self.fetch_parameters()