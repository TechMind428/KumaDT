#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
コマンドパラメータータブUI
コマンドパラメーター設定画面のUIを実装
"""

import tkinter as tk
from tkinter import ttk, messagebox, StringVar, IntVar, DoubleVar
import json
import threading
import re
import asyncio
import functools

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
        
        # デバイスIDをプレーンテキストで表示
        self.device_id_var = StringVar()
        self.device_label = ttk.Label(device_selection_frame, textvariable=self.device_id_var, width=50)
        self.device_label.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        # 取得ボタン
        self.fetch_button = ttk.Button(device_selection_frame, text="取得", command=self.fetch_parameters)
        self.fetch_button.grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        
        # バインド情報表示ラベル
        self.bound_file_info = ttk.Label(device_selection_frame, text="", foreground="blue")
        self.bound_file_info.grid(row=1, column=0, columnspan=3, sticky=tk.W, padx=5, pady=2)
        
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
        ttk.Entry(img_upload_grid, textvariable=self.storage_name_var, width=40).grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)
        
        ttk.Label(img_upload_grid, text="サブディレクトリパス:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        self.storage_subdir_var = StringVar(value="/image/{device_id}")
        self.storage_subdir_entry = ttk.Entry(img_upload_grid, textvariable=self.storage_subdir_var, width=40)
        self.storage_subdir_entry.grid(row=2, column=1, sticky=tk.W, padx=5, pady=2)
        self.storage_subdir_entry.bind("<FocusOut>", lambda e: self.update_path_preview(self.storage_subdir_entry))
        
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
        self.storage_subdir_ir_entry = ttk.Entry(ir_upload_grid, textvariable=self.storage_subdir_ir_var, width=40)
        self.storage_subdir_ir_entry.grid(row=2, column=1, sticky=tk.W, padx=5, pady=2)
        self.storage_subdir_ir_entry.bind("<FocusOut>", lambda e: self.update_path_preview(self.storage_subdir_ir_entry))
        
        # デバイスIDの非表示フィールド（パスプレビュー用）
        self.command_params_device_id = StringVar()
        
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
        
        # ステータス表示
        self.status_var = StringVar()
        self.status_label = ttk.Label(self.params_frame, textvariable=self.status_var, foreground="blue")
        self.status_label.pack(fill=tk.X, padx=5, pady=5)
        
        # パラメーター適用結果
        self.params_result = ttk.Label(self.params_frame, text="", foreground="green")
        self.params_result.pack(fill=tk.X, padx=5, pady=5)
        self.params_result.pack_forget()  # 初期状態では非表示
        
        # 操作ボタン - 下部固定位置に配置
        button_frame = ttk.Frame(self.params_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=10, side=tk.BOTTOM)
        
        self.apply_button = ttk.Button(button_frame, text="適用", command=self.apply_command_parameters)
        self.apply_button.pack(side=tk.RIGHT, padx=5)
        
        self.reset_button = ttk.Button(button_frame, text="リセット", command=self.reset_parameters)
        self.reset_button.pack(side=tk.RIGHT, padx=5)
        
        # キャンバスの更新イベント
        self.scroll_frame.bind("<Configure>", self.on_frame_configure)
        self.canvas.bind("<Configure>", self.on_canvas_configure)
        
        # 初期UIの設定
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
        デバイス表示を更新
        """
        # 設定からデバイスリストを取得
        config = self.settings_manager.config
        device_id = config.get('DEVICE_ID', "")
        
        # デバイスIDを直接表示
        if device_id:
            self.device_id_var.set(device_id)
            self.command_params_device_id.set(device_id)
            self.fetch_button.config(state=tk.NORMAL)  # 取得ボタンを有効化
        else:
            self.device_id_var.set("デバイスが設定されていません")
            self.fetch_button.config(state=tk.DISABLED)  # 取得ボタンを無効化
            self.disable_parameters_ui()
    
    def update_path_preview(self, input_elem):
        """
        パスプレビューを更新
        
        Args:
            input_elem (ttk.Entry): 入力要素
        """
        device_id = self.command_params_device_id.get()
        path = input_elem.get()
        
        if device_id and path and '{device_id}' in path:
            # デバイスIDからサフィックスを抽出
            device_suffix = device_id.split('-')[-1]
            
            # プレビューでは完全なデバイスIDではなくサフィックスを使用
            preview_path = path.replace('{device_id}', device_suffix)
            input_elem.configure(cursor="question_arrow")  # ヒントがあることを示すカーソル
            input_elem.bind("<Enter>", lambda e, tooltip=f"実際のパス: {preview_path}": self.show_tooltip(e, tooltip))
            input_elem.bind("<Leave>", self.hide_tooltip)
        else:
            input_elem.configure(cursor="")
            input_elem.unbind("<Enter>")
            input_elem.unbind("<Leave>")
    
    def show_tooltip(self, event, text):
        """ツールチップを表示"""
        x, y, _, _ = event.widget.bbox("insert")
        x += event.widget.winfo_rootx() + 25
        y += event.widget.winfo_rooty() + 25
        
        # ツールチップウィンドウを作成
        self.tooltip = tk.Toplevel(event.widget)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")
        
        label = ttk.Label(self.tooltip, text=text, background="#FFFFDD", relief="solid", borderwidth=1)
        label.pack(padx=2, pady=2)
    
    def hide_tooltip(self, event=None):
        """ツールチップを非表示"""
        if hasattr(self, 'tooltip'):
            self.tooltip.destroy()
            self.tooltip = None
    
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
        
        # バインド情報をクリア
        self.bound_file_info.configure(text="")
        
        # 結果表示をクリア
        self.params_result.pack_forget()
    
    def enable_parameters_ui(self):
        """
        パラメーターUI要素を有効化
        """
        # パラメーター設定部分を有効化
        for child in self.params_frame.winfo_children():
            for widget in child.winfo_children():
                if isinstance(widget, (ttk.Entry, ttk.Radiobutton)):
                    widget.configure(state=tk.NORMAL)
                # コンボボックスはreadonlyに
                if isinstance(widget, ttk.Combobox):
                    widget.configure(state="readonly")
        
        # ボタンも有効化
        self.apply_button.configure(state=tk.NORMAL)
        self.reset_button.configure(state=tk.NORMAL)
    
    def run_async(self, coro_func, *args, **kwargs):
        """
        非同期関数を同期的に実行するためのヘルパーメソッド
        
        Args:
            coro_func: 実行する非同期関数
            *args: 引数
            **kwargs: キーワード引数
            
        Returns:
            関数の戻り値
        """
        async def wrapper():
            return await coro_func(*args, **kwargs)
            
        # 新しいイベントループを作成して実行
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(wrapper())
        finally:
            loop.close()
    
    def fetch_parameters(self):
        """
        デバイスからパラメーターを取得
        """
        # デバイスIDを直接取得
        device_id = self.device_id_var.get()
        
        if not device_id or device_id == "デバイスが設定されていません":
            self.status_var.set("デバイスが設定されていません")
            return
        
        # ステータス更新
        self.status_var.set(f"パラメーター取得中... ({device_id})")
        self.parent.update()  # UI更新
        
        # ボタンを無効化
        self.fetch_button.config(state=tk.DISABLED)
        
        # 結果表示をクリア
        self.params_result.pack_forget()
        
        # バックグラウンドスレッドで実行
        def run_in_thread():
            try:
                # デバイスがパラメーターファイルにバインドされているか確認
                bound_file_name, bound_file_info = None, None
                try:
                    # 非同期関数を同期的に実行
                    bound_file_name, bound_file_info = self.run_async(
                        self.command_param_manager.get_parameter_file_for_device, 
                        device_id
                    )
                except Exception as e:
                    print(f"バインド確認エラー: {str(e)}")
                
                if not bound_file_name or not bound_file_info:
                    def on_error():
                        self.fetch_button.config(state=tk.NORMAL)
                        error_message = "デバイスにコマンドパラメーターファイルがバインドされていません。コンソールでバインドしてください。"
                        self.status_var.set(error_message)
                        
                        # エラーメッセージを表示
                        self.params_result.configure(
                            text=error_message,
                            foreground="red"
                        )
                        self.params_result.pack(fill=tk.X, padx=5, pady=5)
                        
                        # バインド情報をクリア
                        self.bound_file_info.configure(text="")
                        
                        messagebox.showerror("パラメーター取得エラー", error_message)
                    
                    self.parent.after(0, on_error)
                    return
                
                # パラメーターを取得
                parameters = self.run_async(
                    self.command_param_manager.get_device_parameters, 
                    device_id
                )
                
                # 成功時の処理をメインスレッドで実行
                def on_success():
                    self.fetch_button.config(state=tk.NORMAL)
                    
                    # パラメーターをUIに設定
                    self.set_parameters_to_ui(parameters)
                    self.enable_parameters_ui()
                    
                    # バインド情報を表示
                    self.bound_file_info.configure(
                        text=f"バインドされているファイル: {bound_file_name}"
                    )
                    
                    self.status_var.set("パラメーター取得完了")
                
                self.parent.after(0, on_success)
                
            except Exception as e:
                # エラー時の処理をメインスレッドで実行
                def on_error():
                    self.fetch_button.config(state=tk.NORMAL)
                    error_message = f"エラー: {str(e)}"
                    self.status_var.set(error_message)
                    
                    # エラーメッセージを表示
                    self.params_result.configure(
                        text=error_message,
                        foreground="red"
                    )
                    self.params_result.pack(fill=tk.X, padx=5, pady=5)
                    
                    # バインド情報をクリア
                    self.bound_file_info.configure(text="")
                    
                    messagebox.showerror("パラメーター取得エラー", error_message)
                
                self.parent.after(0, on_error)
        
        # バックグラウンドで実行
        threading.Thread(target=run_in_thread, daemon=True).start()
    
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
            
            # パスプレビューを更新
            self.update_path_preview(self.storage_subdir_entry)
            self.update_path_preview(self.storage_subdir_ir_entry)
            
        except Exception as e:
            self.status_var.set(f"パラメーター設定エラー: {str(e)}")
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
            
            # パラメーター辞書を構築
            cmd_params = {
                "Mode": mode,
                "UploadMethod": self.upload_method_var.get(),
                "StorageName": self.storage_name_var.get(),
                "StorageSubDirectoryPath": self.storage_subdir_var.get(),
                "FileFormat": self.file_format_var.get(),
                "UploadMethodIR": self.upload_method_ir_var.get(),
                "StorageNameIR": self.storage_name_ir_var.get(),
                "StorageSubDirectoryPathIR": self.storage_subdir_ir_var.get(),
                "UploadInterval": self.upload_interval_var.get(),
                "NumberOfInferencesPerMessage": self.num_inferences_var.get(),
                "CropHOffset": self.crop_h_offset_var.get(),
                "CropVOffset": self.crop_v_offset_var.get(),
                "CropHSize": self.crop_h_size_var.get(),
                "CropVSize": self.crop_v_size_var.get(),
                "NumberOfImages": self.num_images_var.get()
            }
            
            # PPLパラメーター
            cmd_params["PPLParameter"] = {
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
            self.status_var.set(f"パラメーター取得エラー: {str(e)}")
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
            
            # モードによって必須チェック項目を変更
            if mode in [0, 1]:  # 画像のみまたは画像と推論結果
                if not self.storage_name_var.get().strip():
                    messagebox.showerror("バリデーションエラー", "ストレージ名は必須です")
                    return False
                
                if not self.storage_subdir_var.get().strip():
                    messagebox.showerror("バリデーションエラー", "サブディレクトリパスは必須です")
                    return False
            
            if mode in [1, 2]:  # 推論結果のみまたは画像と推論結果
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
    
    def apply_command_parameters(self):
        """
        パラメーターを適用
        """
        # デバイスIDを直接取得
        device_id = self.device_id_var.get()
        
        if not device_id or device_id == "デバイスが設定されていません":
            self.status_var.set("デバイスが設定されていません")
            return
        
        # パラメーターのバリデーション
        if not self.validate_parameters():
            return
        
        # UIからパラメーターを取得
        parameters = self.get_parameters_from_ui()
        if not parameters:
            return
        
        # 確認ダイアログを表示
        if not messagebox.askyesno("確認", f"パラメーターをデバイス {device_id} に適用しますか？\n"
                                  f"(これにより一時的に推論が中断される可能性があります)"):
            return
        
        # ステータス更新
        self.status_var.set(f"パラメーター適用中... ({device_id})")
        self.parent.update()  # UI更新
        
        # ボタンを無効化
        self.apply_button.config(state=tk.DISABLED)
        
        # 結果表示をクリア
        self.params_result.pack_forget()
        
        # バックグラウンドスレッドで実行
        def run_in_thread():
            try:
                # パラメーターを適用（非同期関数を同期的に実行）
                result = self.run_async(
                    self.command_param_manager.apply_parameters,
                    device_id,
                    parameters
                )
                
                # 成功時の処理をメインスレッドで実行
                def on_success():
                    self.apply_button.config(state=tk.NORMAL)
                    
                    if result["success"]:
                        self.status_var.set(f"パラメーター適用完了 ({device_id})")
                        
                        # 成功メッセージを表示
                        self.params_result.configure(
                            text=result["message"],
                            foreground="green"
                        )
                        self.params_result.pack(fill=tk.X, padx=5, pady=5)
                        
                        messagebox.showinfo("成功", result["message"])
                    else:
                        self.status_var.set(result["message"])
                        
                        # エラーメッセージを表示
                        self.params_result.configure(
                            text=result["message"],
                            foreground="red"
                        )
                        self.params_result.pack(fill=tk.X, padx=5, pady=5)
                        
                        messagebox.showerror("エラー", result["message"])
                
                self.parent.after(0, on_success)
                
            except Exception as e:
                # エラー時の処理をメインスレッドで実行
                def on_error():
                    self.apply_button.config(state=tk.NORMAL)
                    error_message = f"エラー: {str(e)}"
                    self.status_var.set(error_message)
                    
                    # エラーメッセージを表示
                    self.params_result.configure(
                        text=error_message,
                        foreground="red"
                    )
                    self.params_result.pack(fill=tk.X, padx=5, pady=5)
                    
                    messagebox.showerror("パラメーター適用エラー", error_message)
                
                self.parent.after(0, on_error)
        
        # バックグラウンドで実行
        threading.Thread(target=run_in_thread, daemon=True).start()
    
    def reset_parameters(self):
        """
        パラメーターを取得値にリセット
        """
        if not messagebox.askyesno("確認", "パラメーターを取得時の値にリセットしますか？"):
            return
        
        # デバイスIDを直接取得
        device_id = self.device_id_var.get()
        
        if not device_id or device_id == "デバイスが設定されていません":
            self.status_var.set("デバイスが設定されていません")
            return
        
        # パラメーターを再取得
        self.fetch_parameters()
    
    def refresh(self):
        """
        タブの表示時に呼び出される更新処理
        """
        # デバイスセレクタを更新
        self.update_device_selector()
        
        # タブ表示時に自動的にパラメーターを取得
        device_id = self.device_id_var.get()
        if device_id and device_id != "デバイスが設定されていません":
            self.fetch_parameters()