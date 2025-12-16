# YOLO Takoyaki 人流検出システム

## 概要

最大4台のカメラからストリーミング画像を取得し、YOLOで人物検出を行い、人流データを収集・分析するシステムです。

## 必要なファイル

### 親機（母艦PC）
- `app.py` - メインアプリケーション
- `camera_discovery.py` - カメラ検出
- `config.py` - 設定
- `yolo_processor.py` - YOLO処理
- `templates/index.html` - フロントエンド
- `requirements.txt` - 依存関係

### 子機（Raspberry Pi）
- `camera_server.py` - カメラストリーミングサーバー
- `requirements_child.txt` - 依存関係

## セットアップ

### 親機

```bash
# 依存関係のインストール
pip install -r requirements.txt

# 起動
python app.py
```

ブラウザで `http://localhost:5000` にアクセスし、「接続を更新」ボタンをクリック。

### 子機

```bash
# 依存関係のインストール
pip install -r requirements_child.txt

# 起動（カメラID ポート番号）
python camera_server.py 0 5001  # カメラ0（ポート5001）
python camera_server.py 1 5002  # カメラ1（ポート5002）
python camera_server.py 2 5003  # カメラ2（ポート5003）
python camera_server.py 3 5004  # カメラ3（ポート5004）
```

## 環境変数

### 親機

```bash
# 本番環境（子機が5001-5004を使用）
export CAMERA_PORTS="5001,5002,5003,5004"

# 既知の子機IPアドレスを指定（オプション）
export KNOWN_CHILD_IPS="192.168.0.131,192.168.0.132"
```

### 子機

```bash
export CAMERA_ID=0
export CAMERA_PORT=5001  # カメラ0はポート5001
export CAMERA_DEVICE_ID=0  # USBカメラのデバイスID
```

## トラブルシューティング

### カメラが見つからない

1. 子機が起動しているか確認
2. 同じWiFiネットワークに接続されているか確認
3. ファイアウォールでポートが開いているか確認（子機側）
   ```bash
   sudo ufw allow 5001/tcp
   sudo ufw allow 5002/tcp
   sudo ufw allow 5003/tcp
   sudo ufw allow 5004/tcp
   ```

### 接続できない

```bash
# 親機から子機への接続確認
ping 子機のIPアドレス
curl http://子機のIPアドレス:ポート/info
```

### カメラが開けない（子機）

```bash
# USBカメラのデバイスIDを確認
ls -l /dev/video*
```

## データファイル

- `data/detections.jsonl` - リアルタイム検出データ（30分で自動削除）
- `data/detections_minutely.jsonl` - 1分ごとの集計データ

