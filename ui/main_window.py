#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
メインウィンドウUI
アプリケーションのメインウィンドウを実装
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
from datetime import datetime

import settings
from api.aitrios_client import AITRIOSClient
from core.detection_processor import DetectionProcessor
from core.settings_manager import SettingsManager
from core.command_parameter_manager import CommandParameterManager
from ui.main_tab import MainTab
from ui.settings_tab import SettingsTab
from ui.command_params_tab import CommandParamsTab

class KumakitaApp(tk.Tk):
    """アプリケーションのメインウィンドウクラス"""
    
    def __init__(self):
        """メインウィンドウの初期化"""
        super().__init__()
        
        # アプリケーションの基本設定
        self.title("Kumakita - AI Detection Monitor")
        self.geometry("1200x700")  # ウィンドウサイズを大きめに設定
        self.configure(bg="#f0f0f0")  # Mac風の背景色
        
        # 設定マネージャーの初期化
        self.settings_manager = SettingsManager(settings)
        
        # APIクライアントの初期化
        self.aitrios_client = AITRIOSClient(
            settings.DEVICE_ID,
            settings.CLIENT_ID,
            settings.CLIENT_SECRET
        )
        
        # コマンドパラメーターマネージャーの初期化
        self.command_param_manager = CommandParameterManager(self.aitrios_client)
        
        # 検出プロセッサの初期化
        self.processor = DetectionProcessor(
            self.aitrios_client,
            settings.objclass,
            self.handle_processor_callback
        )
        
        # 処理状態の管理用変数
        self.running_flag = threading.Event()
        self.processing_thread = None
        
        # 状態更新タイマーID
        self.status_update_timer = None
        
        # UIの初期化
        self.init_ui()
        
        # アプリケーション起動時にデバイス状態を初期確認
        self.check_device_status()
        
        # 定期的なデバイス状態の更新を開始
        self.start_periodic_status_update()
    
    def init_ui(self):
        """UIの初期化"""
        # メインフレームの作成
        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # タブコントロールの作成
        self.tab_control = ttk.Notebook(self.main_frame)
        
        # メインタブ
        self.main_tab_frame = ttk.Frame(self.tab_control)
        self.tab_control.add(self.main_tab_frame, text="監視画面")
        
        # 設定タブ
        self.settings_tab_frame = ttk.Frame(self.tab_control)
        self.tab_control.add(self.settings_tab_frame, text="設定")
        
        # コマンドパラメータタブ
        self.command_params_tab_frame = ttk.Frame(self.tab_control)
        self.tab_control.add(self.command_params_tab_frame, text="コマンドパラメーター")
        
        self.tab_control.pack(expand=True, fill=tk.BOTH)
        
        # タブ切り替えイベントの設定
        self.tab_control.bind("<<NotebookTabChanged>>", self.on_tab_changed)
        
        # メインタブのUI
        self.main_tab = MainTab(self.main_tab_frame)
        self.main_tab.set_button_commands(
            start_command=self.start_processing,
            stop_command=self.stop_processing,
            inference_start_command=self.start_inference,
            inference_stop_command=self.stop_inference
        )
        
        # 設定タブのUI
        self.settings_tab = SettingsTab(self.settings_tab_frame, self.settings_manager)
        self.settings_tab.set_cancel_command(lambda: self.tab_control.select(0))
        self.settings_tab.set_on_settings_changed(self.on_settings_changed)
        
        # コマンドパラメータータブのUI
        self.command_params_tab = CommandParamsTab(
            self.command_params_tab_frame,
            self.command_param_manager,
            self.settings_manager
        )
        
        # ステータスバー
        self.status_bar = tk.Label(self, text="準備完了", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # アプリケーション終了時の処理を設定
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def on_tab_changed(self, event):
        """タブ切り替え時の処理"""
        selected_tab = self.tab_control.index("current")
        
        # 設定タブが選択された場合（インデックス1）
        if selected_tab == 1:
            # 設定値を最新の状態に更新
            self.settings_tab.refresh_settings()
            self.update_status("設定画面に切り替えました")
        # コマンドパラメータータブが選択された場合（インデックス2）
        elif selected_tab == 2:
            # コマンドパラメーター画面を更新
            self.command_params_tab.refresh()
            self.update_status("コマンドパラメーター画面に切り替えました")
    
    def start_periodic_status_update(self):
        """定期的なデバイス状態更新を開始"""
        # 既存のタイマーがあればキャンセル
        if self.status_update_timer:
            self.after_cancel(self.status_update_timer)
        
        # 更新間隔（ミリ秒）
        update_interval = 2000  # 2秒ごと
        
        # 最初の更新を予約
        self.status_update_timer = self.after(update_interval, self.periodic_status_update)
    
    def stop_periodic_status_update(self):
        """定期的なデバイス状態更新を停止"""
        if self.status_update_timer:
            self.after_cancel(self.status_update_timer)
            self.status_update_timer = None
    
    def periodic_status_update(self):
        """定期的なデバイス状態更新の実行"""
        # デバイス状態を確認
        self.check_device_status()
        
        # 次の更新を予約（再帰的に呼び出し）
        self.status_update_timer = self.after(2000, self.periodic_status_update)
    
    def check_device_status(self):
        """アプリケーション起動時のデバイス状態確認"""
        try:
            # デバイス状態の取得
            connection_state, operation_state = self.aitrios_client.get_connection_state()
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # UI更新
            self.main_tab.update_device_state(connection_state, operation_state, timestamp)
            
            # ステータス更新
            status_message = "デバイス接続中" if connection_state == "Connected" else "デバイス未接続"
            self.update_status(f"{status_message} ({operation_state})")
            
        except Exception as e:
            self.update_status(f"デバイス状態取得エラー: {str(e)}")

    def start_inference(self):
        """推論処理を開始する"""
        try:
            # デバイス状態を取得
            connection_state, operation_state = self.aitrios_client.get_connection_state()
            
            # Connected && Idleの場合のみ実行
            if connection_state == "Connected" and operation_state == "Idle":
                # 推論開始APIを呼び出す
                result = self.aitrios_client.start_inference()
                if result.get("result") == "SUCCESS":
                    self.update_status("推論を開始しました")
                    
                    # 自動的に表示も開始
                    self.start_processing()
                    
                    # 1秒後にデバイス状態を再取得（APIが非同期のため）
                    self.after(1000, self.check_device_status)
                else:
                    error_message = result.get("message", "Unknown error")
                    self.update_status(f"推論開始エラー: {error_message}")
            else:
                self.update_status(f"推論開始条件を満たしていません: {connection_state} - {operation_state}")
        except Exception as e:
            self.update_status(f"推論開始エラー: {str(e)}")
    
    def stop_inference(self):
        """推論処理を停止する"""
        try:
            # デバイス状態を取得
            connection_state, operation_state = self.aitrios_client.get_connection_state()
            
            # Connectedでかつ、Idle以外の場合に実行
            if connection_state == "Connected" and operation_state != "Idle":
                # 推論停止APIを呼び出す
                result = self.aitrios_client.stop_inference()
                if result.get("result") == "SUCCESS":
                    self.update_status("推論を停止しました")
                    
                    # 1秒後にデバイス状態を再取得（APIが非同期のため）
                    self.after(1000, self.check_device_status)
                else:
                    error_message = result.get("message", "Unknown error")
                    self.update_status(f"推論停止エラー: {error_message}")
            else:
                self.update_status(f"推論停止条件を満たしていません: {connection_state} - {operation_state}")
        except Exception as e:
            self.update_status(f"推論停止エラー: {str(e)}")
    
    def on_settings_changed(self):
        """設定変更時のコールバック"""
        # APIクライアントの更新
        config = self.settings_manager.config
        self.aitrios_client = AITRIOSClient(
            config['DEVICE_ID'],
            config['CLIENT_ID'],
            config['CLIENT_SECRET']
        )
        
        # 検出プロセッサの更新
        self.processor.aitrios_client = self.aitrios_client
        self.processor.set_objclass(config['objclass'])
        
        # コマンドパラメーターマネージャーの更新
        self.command_param_manager.aitrios_client = self.aitrios_client
        
        self.update_status("設定が更新されました")
        
        # デバイス状態を再取得
        self.check_device_status()
    
    def handle_processor_callback(self, event_type, data):
        """
        検出プロセッサからのコールバック処理
        
        Args:
            event_type (str): イベントタイプ
            data: イベントデータ
        """
        if event_type == "status":
            self.update_status(data)
        elif event_type == "image":
            self.main_tab.update_image(data)
        elif event_type == "detection":
            self.main_tab.update_detection_info(data)
        elif event_type == "device_state":
            connection_state, operation_state, timestamp = data
            self.main_tab.update_device_state(connection_state, operation_state, timestamp)
    
    def update_status(self, message):
        """
        ステータスバーとログを更新
        
        Args:
            message (str): ステータスメッセージ
        """
        # UIスレッドからの呼び出しを保証
        def _update():
            # ステータスバーの更新
            self.status_bar.config(text=message)
            
            # ログの更新
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
            log_message = f"[{timestamp}] {message}"
            self.main_tab.update_log(log_message)
        
        # スレッドからの呼び出しの場合はafter()を使用
        if threading.current_thread() is not threading.main_thread():
            self.after(0, _update)
        else:
            _update()
    
    def start_processing(self):
        """処理を開始"""
        if not self.running_flag.is_set():
            self.running_flag.set()
            self.processing_thread = threading.Thread(
                target=self.processor.process_images,
                args=(self.running_flag,)
            )
            self.processing_thread.daemon = True
            self.processing_thread.start()
            
            self.main_tab.set_start_state(True)
            self.update_status("処理を開始しました")
    
    def stop_processing(self):
        """処理を停止"""
        if self.running_flag.is_set():
            self.running_flag.clear()
            if self.processing_thread and self.processing_thread.is_alive():
                self.processing_thread.join(1.0)  # 最大1秒待機
            
            self.main_tab.set_start_state(False)
            self.update_status("処理を停止しました")
    
    def on_closing(self):
        """アプリケーション終了時の処理"""
        # 実行中なら停止
        if self.running_flag.is_set():
            self.stop_processing()
        
        # 定期的な状態更新を停止
        self.stop_periodic_status_update()
        
        # 終了確認
        if messagebox.askokcancel("終了確認", "アプリケーションを終了しますか？"):
            self.destroy()