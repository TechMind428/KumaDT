# KumaDesktop

KumaDesktopは、AITRIOSデバイスの監視と管理のためのデスクトップアプリケーションで、Object Detectionの推論結果の表示に焦点を当てています。

## 機能

- AITRIOSエッジデバイスの管理
- リアルタイム物体検出表示
- コマンドパラメーター設定

## インストール

### 前提条件

- Python 3.8以上
- AITRIOSコンソールアカウントとAPI認証情報

### 依存関係

必要なPythonパッケージをインストールします：

```bash
pip install -r requirements.txt
```

### 設定

1. `settings.py`ファイルをあなたのAITRIOSデバイス情報で修正します：
   - `DEVICE_ID`: あなたのAITRIOSデバイスID
   - `CLIENT_ID`: あなたのAITRIOS APIクライアントID
   - `CLIENT_SECRET`: あなたのAITRIOS APIクライアントシークレット

## 使用方法

以下のコマンドでアプリケーションを起動します：

```bash
python main.py
```

### メインインターフェース

アプリケーションはデバイスの監視のためのシンプルなインターフェースを提供します：

- **監視画面**: リアルタイムの検出結果とデバイスステータスを表示
- **設定**: デバイスIDとAPI認証情報を設定
- **コマンドパラメーター**: デバイスのアップロードと推論パラメーターを設定

### コマンドパラメーター設定

コマンドパラメーター画面では、様々なデバイス設定を構成できます：

1. **アップロードモード**: アップロードするデータ（画像、推論結果、または両方）を設定
2. **画像アップロード設定**: 画像のストレージ設定を構成
3. **推論結果設定**: 推論結果のアップロード設定を構成
4. **PPLパラメーター**: 検出閾値やその他のモデルパラメーターを設定

## プロジェクト構造

```
KumaDesktop/
├── main.py                            # アプリケーションエントリーポイント
├── api/                               # API通信モジュール
│   ├── __init__.py                    # APIモジュールパッケージ定義
│   └── aitrios_client.py              # AITRIOS APIクライアント
├── core/                              # コアロジックモジュール
│   ├── __init__.py                    # コアモジュールパッケージ定義
│   ├── detection_processor.py         # 画像処理と物体検出
│   ├── settings_manager.py            # 設定管理
│   └── command_parameter_manager.py   # コマンドパラメーター管理
├── ui/                                # UIモジュール
│   ├── __init__.py                    # UIモジュールパッケージ定義
│   ├── main_window.py                 # メインウィンドウ
│   ├── main_tab.py                    # メインタブ
│   ├── settings_tab.py                # 設定タブ
│   └── command_params_tab.py          # コマンドパラメータータブ
├── utils/                             # ユーティリティモジュール
│   ├── __init__.py                    # ユーティリティモジュールパッケージ定義
│   ├── image_utils.py                 # 画像処理ユーティリティ
│   └── file_utils.py                  # ファイル操作ユーティリティ
├── BoundingBox.py                     # FlatBuffers生成クラス
├── BoundingBox2d.py                   # FlatBuffers生成クラス
├── GeneralObject.py                   # FlatBuffers生成クラス
├── ObjectDetectionData.py             # FlatBuffers生成クラス
└── ObjectDetectionTop.py              # FlatBuffers生成クラス
```

## ライセンス

このプロジェクトはApache License 2.0の下でライセンスされています。詳細はLICENSEファイルを参照してください。