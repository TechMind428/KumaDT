#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
設定タブUI
設定画面のUIを実装
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from utils.file_utils import export_classes_to_csv, import_classes_from_csv

class SettingsTab:
    """設定タブのUI実装"""
    
    def __init__(self, parent, settings_manager):
        """
        設定タブの初期化
        
        Args:
            parent (tk.Frame): 親ウィジェット
            settings_manager (SettingsManager): 設定管理オブジェクト
        """
        self.parent = parent
        self.settings_manager = settings_manager
        self.config = settings_manager.load_settings()
        
        # クラスリスト表示用の変数
        self.class_list = None
        self.class_index_var = None
        self.class_name_var = None
        
        # 設定値を保持する変数
        self.device_id_var = tk.StringVar()
        self.client_id_var = tk.StringVar()
        self.client_secret_var = tk.StringVar()
        self.num_classes_var = tk.IntVar()
        
        # UIの初期化
        self.setup_ui()
        
        # 初期値の設定
        self.load_config_to_ui()
    
    def setup_ui(self):
        """UIコンポーネントの初期化と配置"""
        # 設定フレーム
        self.settings_frame = ttk.LabelFrame(self.parent, text="AITRIOS API設定")
        self.settings_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 設定フィールド
        row = 0
        
        # デバイスID
        ttk.Label(self.settings_frame, text="デバイスID:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Entry(self.settings_frame, textvariable=self.device_id_var, width=50).grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)
        row += 1
        
        # クライアントID
        ttk.Label(self.settings_frame, text="クライアントID:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Entry(self.settings_frame, textvariable=self.client_id_var, width=50).grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)
        row += 1
        
        # クライアントシークレット
        ttk.Label(self.settings_frame, text="クライアントシークレット:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Entry(self.settings_frame, textvariable=self.client_secret_var, width=50, show="*").grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)
        row += 1
        
        # クラス数
        ttk.Label(self.settings_frame, text="クラス数:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        
        # クラス数入力と更新ボタンをまとめる
        class_num_frame = ttk.Frame(self.settings_frame)
        class_num_frame.grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)
        
        # クラス数入力（上限を256に設定）
        class_spinbox = ttk.Spinbox(class_num_frame, from_=1, to=256, textvariable=self.num_classes_var, width=5)
        class_spinbox.pack(side=tk.LEFT, padx=5)
        
        # 行数更新ボタン
        update_button = ttk.Button(class_num_frame, text="適用", command=self.update_class_editor_rows)
        update_button.pack(side=tk.LEFT, padx=5)
        
        row += 1
        
        # オブジェクトクラス
        ttk.Label(self.settings_frame, text="オブジェクトクラス:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        
        # オブジェクトクラスのリスト編集用フレーム
        classes_frame = ttk.LabelFrame(self.settings_frame, text="クラス一覧 (0から始まるインデックス)")
        classes_frame.grid(row=row, column=1, sticky=tk.NSEW, padx=5, pady=5)
        self.settings_frame.grid_columnconfigure(1, weight=1)
        self.settings_frame.grid_rowconfigure(row, weight=1)
        
        # Treeviewとスクロールバーのフレーム
        tree_frame = ttk.Frame(classes_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # クラスリスト表示用のテーブル
        self.class_list = ttk.Treeview(tree_frame, columns=("index", "name"), show="headings", height=10)
        self.class_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 縦スクロールバー
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.class_list.yview)
        self.class_list.configure(yscrollcommand=vsb.set)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 横スクロールバー
        hsb = ttk.Scrollbar(classes_frame, orient="horizontal", command=self.class_list.xview)
        self.class_list.configure(xscrollcommand=hsb.set)
        hsb.pack(fill=tk.X)
        
        # カラム設定
        self.class_list.heading("index", text="Index")
        self.class_list.heading("name", text="クラス名")
        self.class_list.column("index", width=80, anchor="center", minwidth=50)
        self.class_list.column("name", width=300, minwidth=150)
        
        # クラス編集用フレーム
        edit_frame = ttk.Frame(classes_frame)
        edit_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(edit_frame, text="インデックス:").pack(side=tk.LEFT, padx=5)
        self.class_index_var = tk.StringVar()
        index_entry = ttk.Entry(edit_frame, textvariable=self.class_index_var, width=5, state="readonly")
        index_entry.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(edit_frame, text="クラス名:").pack(side=tk.LEFT, padx=5)
        self.class_name_var = tk.StringVar()
        self.class_name_entry = ttk.Entry(edit_frame, textvariable=self.class_name_var, width=30)
        self.class_name_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        ttk.Button(edit_frame, text="更新", command=self.update_selected_class).pack(side=tk.LEFT, padx=5)
        
        # 選択変更時の処理
        self.class_list.bind("<<TreeviewSelect>>", self.on_class_selected)
        
        # 操作ボタンフレーム
        button_frame = ttk.Frame(classes_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        ttk.Button(button_frame, text="CSV出力", command=self.export_classes).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="CSV読込", command=self.import_classes).pack(side=tk.LEFT, padx=5)
        
        row += 1
        
        # ボタンフレーム
        button_frame = ttk.Frame(self.settings_frame)
        button_frame.grid(row=row, column=0, columnspan=2, pady=10)
        
        # 設定保存ボタン
        ttk.Button(button_frame, text="設定を保存", command=self.save_settings).pack(side=tk.LEFT, padx=5)
        
        # キャンセルボタン（タブ移動用にコールバックは別途設定）
        self.cancel_button = ttk.Button(button_frame, text="キャンセル")
        self.cancel_button.pack(side=tk.LEFT, padx=5)
    
    def set_cancel_command(self, command):
        """
        キャンセルボタンのコマンドを設定
        
        Args:
            command (function): キャンセルボタンのコマンド
        """
        self.cancel_button.config(command=command)
    
    def load_config_to_ui(self):
        """設定を読み込んでUIに反映"""
        # 変数に設定を反映
        self.device_id_var.set(self.config['DEVICE_ID'])
        self.client_id_var.set(self.config['CLIENT_ID'])
        self.client_secret_var.set(self.config['CLIENT_SECRET'])
        self.num_classes_var.set(self.config['numberofclass'])
        
        # クラスリストを更新
        self.fill_class_list(self.config['objclass'])
    
    def fill_class_list(self, classes):
        """
        クラスリストをTreeviewに表示
        
        Args:
            classes (list): クラスリスト
        """
        # 既存の項目をクリア
        for item in self.class_list.get_children():
            self.class_list.delete(item)
        
        # クラスをリストに追加
        for i, class_name in enumerate(classes):
            self.class_list.insert("", "end", values=(i, class_name))
        
        # リストの先頭を選択（あれば）
        if self.class_list.get_children():
            first_item = self.class_list.get_children()[0]
            self.class_list.selection_set(first_item)
            self.class_list.see(first_item)  # 視界内に表示
            try:
                self.on_class_selected()
            except:
                pass  # 初期化時はエラーを無視
    
    def on_class_selected(self, event=None):
        """
        リストで選択されたクラスをエントリーに表示
        
        Args:
            event: イベント情報（省略可能）
        """
        selected_items = self.class_list.selection()
        if selected_items:
            item = selected_items[0]
            index, name = self.class_list.item(item, "values")
            self.class_index_var.set(index)
            self.class_name_var.set(name)
    
    def update_selected_class(self):
        """選択されたクラス名を更新"""
        selected_items = self.class_list.selection()
        if selected_items:
            item = selected_items[0]
            index, old_name = self.class_list.item(item, "values")
            new_name = self.class_name_var.get()
            
            # Treeviewの更新
            self.class_list.item(item, values=(index, new_name))
    
    def update_class_editor_rows(self):
        """クラス数に合わせてクラスリストを調整する"""
        # 現在のクラスリストを取得
        current_classes = []
        for item in self.class_list.get_children():
            index, name = self.class_list.item(item, "values")
            current_classes.append(name)
        
        # 必要な行数
        num_classes = self.num_classes_var.get()
        
        # クラス数の範囲チェック
        if num_classes > 256:
            messagebox.showwarning("警告", "クラス数は256以下にしてください")
            self.num_classes_var.set(256)
            num_classes = 256
        
        # 現在のクラスリストをクラス数に合わせる
        adjusted_classes = current_classes[:num_classes]  # クラス数より多い場合は切り捨て
        
        # 足りない場合は空の行を追加
        while len(adjusted_classes) < num_classes:
            adjusted_classes.append(f"CLASS{len(adjusted_classes)}")
        
        # Treeviewを更新
        self.fill_class_list(adjusted_classes)
        
        # 更新メッセージ
        messagebox.showinfo("クラス数更新", f"クラス数を{num_classes}に調整しました。")
    
    def export_classes(self):
        """クラスリストをCSVファイルとして出力"""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="クラスリストを保存"
        )
        
        if file_path:
            # Treeviewから現在のクラスリストを取得
            classes = []
            for item in self.class_list.get_children():
                index, name = self.class_list.item(item, "values")
                classes.append(name)
            
            # CSVファイルとして保存
            if export_classes_to_csv(classes, file_path):
                messagebox.showinfo("CSV出力", f"クラスリストを{file_path}に保存しました。")
            else:
                messagebox.showerror("エラー", "CSVファイルの保存に失敗しました。")
    
    def import_classes(self):
        """CSVファイルからクラスリストを読み込み"""
        file_path = filedialog.askopenfilename(
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="クラスリストを読み込み"
        )
        
        if file_path:
            # CSVからクラスリストを読み込み
            classes = import_classes_from_csv(file_path)
            
            if classes:
                # クラス数の更新
                self.num_classes_var.set(len(classes))
                
                # Treeviewの更新
                self.fill_class_list(classes)
                
                messagebox.showinfo("CSV読込", f"{len(classes)}個のクラスを読み込みました。")
            else:
                messagebox.showerror("エラー", "CSVファイルの読み込みに失敗しました。")
    
    def get_current_settings(self):
        """
        現在のUI設定を取得
        
        Returns:
            dict: 現在の設定
        """
        # クラスリストを取得
        objclass_list = []
        for item in self.class_list.get_children():
            index, name = self.class_list.item(item, "values")
            objclass_list.append(name)
        
        # クラス数とリスト長を一致させる
        num_classes = self.num_classes_var.get()
        if len(objclass_list) != num_classes:
            # リストが短い場合は拡張
            while len(objclass_list) < num_classes:
                objclass_list.append(f"CLASS{len(objclass_list)}")
            # リストが長い場合は切り詰め
            objclass_list = objclass_list[:num_classes]
        
        # 新しい設定を作成
        return {
            'DEVICE_ID': self.device_id_var.get(),
            'CLIENT_ID': self.client_id_var.get(),
            'CLIENT_SECRET': self.client_secret_var.get(),
            'numberofclass': num_classes,
            'objclass': objclass_list
        }
    
    def save_settings(self):
        """設定を保存"""
        try:
            # 現在の設定を取得
            new_settings = self.get_current_settings()
            
            # 設定を保存
            try:
                save_result = self.settings_manager.save_settings(new_settings)
                if save_result:
                    messagebox.showinfo("設定保存", "設定を保存しました。変更を反映するには、監視を再開始してください。")
                    
                    # 設定変更通知用のコールバックがあれば実行
                    if hasattr(self, 'on_settings_changed') and callable(self.on_settings_changed):
                        self.on_settings_changed()
                    
                    # メインタブに戻る場合はここでタブ移動（cancel_commandが設定されている前提）
                    self.cancel_button.invoke()
                else:
                    messagebox.showerror("エラー", "設定の保存に失敗しました。")
            except TypeError as te:
                # 引数の問題を詳細に表示
                import inspect
                sig = inspect.signature(self.settings_manager.save_settings)
                messagebox.showerror("エラー", f"設定保存メソッドの呼び出しに問題があります: {str(te)}\n"
                                              f"メソッドの定義: {sig}")
        
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(error_details)  # コンソールにトレースバックを出力
            messagebox.showerror("エラー", f"設定の保存中にエラーが発生しました: {str(e)}\n\n詳細: {type(e).__name__}")
    
    def set_on_settings_changed(self, callback):
        """
        設定変更時のコールバックを設定
        
        Args:
            callback (function): 設定変更時に呼び出すコールバック関数
        """
        self.on_settings_changed = callback
    
    def refresh_settings(self):
        """
        設定値を再読み込みしてUIに反映する
        設定画面に移動する際に呼び出される
        """
        # 設定マネージャーから最新の設定を取得
        self.config = self.settings_manager.load_settings()
        
        # UIに設定値を反映
        self.load_config_to_ui()
        
        # 変更を示すために少し点滅効果を加える（任意）
        self.flash_fields()
        
    def flash_fields(self):
        """
        フィールドを点滅させて変更を示す視覚的効果
        """
        try:
            # ttk ウィジェットでは 'background' ではなく 'style' を使って色を変更
            # 代わりに他の方法で視覚的なフィードバックを提供
            
            # 一時的なラベルによるフィードバック
            feedback_label = ttk.Label(
                self.settings_frame,
                text="設定を更新しました",
                foreground="green"
            )
            feedback_label.grid(row=0, column=2, padx=5, pady=5)
            
            def remove_label():
                """フィードバックラベルを削除"""
                feedback_label.destroy()
            
            # 1秒後にラベルを削除
            self.parent.after(1000, remove_label)
            
        except Exception as e:
            # エラーが発生しても機能に影響しないよう静かに失敗
            print(f"視覚的フィードバックでエラー: {str(e)}")