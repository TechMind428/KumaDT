# KumaDT (Desktop)

KumaDTは、AITRIOSデバイスの監視と管理のためのデスクトップアプリケーションで、Object Detectionの推論結果の表示に焦点を当てています。
このプログラムでは、デバイスにBindされているコマンドパラメーターファイルを変更して適用することができますので、同じパラメーターファイル名をバインドしている他のデバイスにも影響を与えますので、操作するデバイス専用のコマンドパラメーターをあらかじめBindしておくようにしてください。
Custom Vison Object Detection, Mobiledet Object Detection以外のモデルを使用している場合、コマンドパラメーターファイルの不整合がおきますので、使用しないでください。（あらかじめバックアップをとっておき、戻せるようにすることを強くお勧めします）

Qiitaでは、画面のイメージも使った解説もしていますので、ご参照ください。

[https://qiita.com/Shibu-Shin/items/5477e10477baf2f53747](https://qiita.com/Shibu-Shin/items/5477e10477baf2f53747)

## 機能

- AITRIOSエッジデバイスの管理
- リアルタイム物体検出表示
- コマンドパラメーター設定

## インストール

Mac / Raspberry Piの場合
```
git clone https://github.com/TechMind428/KumaDT.git
cd KumaDT
python3 -m venv myenv #Pythonの仮想環境の作成
. myenv/bin/activate #Pythonの仮想環境をActivate
```
Windowsの場合
```
Mac / Raspberry Piの場合
git clone https://github.com/TechMind428/KumaDT.git
cd KumaDT
python3 -m venv myenvn #Pythonの仮想環境の作成
myenv/Scripts/activate #Pythonの仮想環境をActivate
```

### 前提条件

-MacOS, Windows11, Raspberry Pi OS
- Python 3.8以上
- AITRIOSコンソールアカウントとAPI認証情報

### 依存関係

必要なPythonパッケージをインストールします：

```bash
pip install -r requirements.txt
```

### 設定

1. `settings.py`ファイルをあなたのAITRIOSデバイス情報で修正します：(プログラムを起動して設定画面からでも設定できます）
   - `DEVICE_ID`: あなたのAITRIOSデバイスID
   - `CLIENT_ID`: あなたのAITRIOS APIクライアントID
   - `CLIENT_SECRET`: あなたのAITRIOS APIクライアントシークレット

## 使用方法

Pythonの仮想環境がactiveな状態で、以下のコマンドでアプリケーションを起動します：

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
KumaDT/
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
