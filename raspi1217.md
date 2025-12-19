以下は、**次の会話・別GPT・チームメンバーにそのまま渡せる引き継ぎ用まとめ**です。
**Markdown（md）形式／コピペ前提**で書いています。

---

# 📷 Raspberry Pi Zero 2 W 遠隔ライブカメラ構築

引き継ぎまとめ（2025-12-18 時点）

## 1. プロジェクト概要

### 目的

* **Raspberry Pi Zero 2 W + USBカメラ**を使い
  **Wi-Fi経由でPCへライブ映像配信**
* PC側で **YOLOによる画像解析**
* **640x480 / 約8fps / 1秒程度の遅延OK**
* **複数台運用（まずは2台、将来4台以上）**

---

## 2. 使用機材・環境

### ハードウェア

* Raspberry Pi Zero 2 W
* USBカメラ：**Logicool C270**
* 接続：Wi-Fi（2.4GHz）

### ソフトウェア

* OS：Raspberry Pi OS
* Python 3
* OpenCV
* Flask（MJPEG配信）
* ffmpeg（動作確認用）
* ※ mDNS（hostname.local）利用

### ネットワーク

* PC：Windows（常時稼働）
* RasPi → PC：Wi-Fi経由

---

## 3. デバイス構成・命名

| 項目       | 内容                    |
| -------- | --------------------- |
| ユーザー     | `pi`                  |
| camera 1 | hostname: `camera001` |
| camera 2 | hostname: `camera002` |
| カメラ      | `/dev/video0`（C270）   |

---

## 4. 現在の到達点（重要）

### ✅ 確認済み

* USBカメラ認識（`lsusb`）
* `/dev/video0` から静止画取得成功（ffmpeg）
* Flaskアプリ起動確認
* ポート指定での起動（例：5002）
* 複数 `/dev/video*` が見えるが **実体は video0**

```bash
lsusb
ls /dev/video*
```

---

## 5. カメラ動作確認コマンド

### USBカメラ認識確認

```bash
lsusb
```

### 静止画取得テスト（重要）

```bash
ffmpeg -f v4l2 -i /dev/video0 -frames:v 1 test.jpg
ls -l test.jpg
```markdown
# 📷 Raspberry Pi Zero 2 W 遠隔ライブカメラ構築

**引き継ぎまとめ（最新版 / 2025-12-18）**

## 1. プロジェクト概要（最新）

### 目的

* Raspberry Pi Zero 2 W + USBカメラ（Logicool C270）
* Wi-Fi経由で **PCへライブ映像配信**
* PC側で **YOLO解析**
* **遅延：約1秒まで許容**
* **複数台運用（現在2台、将来拡張）**

### 📌 最新の映像設定（確定）

* **解像度：640 × 480**
* **FPS：8**
* 画質・帯域・CPU負荷のバランスを考慮して決定

---

## 2. 使用機材・環境

### ハードウェア

* Raspberry Pi Zero 2 W
* USBカメラ：Logicool C270
* Wi-Fi（2.4GHz）

### ソフトウェア

* Raspberry Pi OS
* Python 3
* OpenCV
* Flask（MJPEG配信）
* ffmpeg（動作確認）
* v4l2-utils

---

## 3. デバイス構成

| 項目       | 内容                    |
| -------- | --------------------- |
| ユーザー     | `pi`                  |
| camera 1 | hostname: `camera001` |
| camera 2 | hostname: `camera002` |
| カメラデバイス  | `/dev/video0`（C270）   |

※ `/dev/video*` は多数見えるが **実体は video0**

---

## 4. 現在の到達点（最新状態）

### ✅ 完了・確認済み

* USBカメラ認識（`lsusb`）
* `/dev/video0` から静止画取得成功
* Flask + OpenCV による MJPEG 配信動作
* **640×480 / 8fps 設定で安定動作**
* ポート指定での複数台起動想定

---

## 5. カメラ動作確認

### USBカメラ確認

```bash
lsusb
```

### カメラデバイス確認

```bash
v4l2-ctl --list-devices
```

### 静止画取得テスト

```bash
ffmpeg -f v4l2 -i /dev/video0 -frames:v 1 test.jpg
```

---

## 6. カメラサーバー起動方法（最新）

### 起動コマンド

```bash
python3 camera_server.py 0 5002
```

### camera_server.py 側の前提設定（重要）

```python
CAP_WIDTH  = 640
CAP_HEIGHT = 480
CAP_FPS    = 8
```

```python
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
cap.set(cv2.CAP_PROP_FPS, 8)
```

### ブラウザ確認（PC側）

```text
http://camera002.local:5002
```

または

```text
http://<IPアドレス>:5002
```

---

## 7. IP・ポート確認方法

### IPアドレス確認

```bash
hostname -I
```

または

```bash
ip a
```

### ホスト名確認

```bash
hostname
```

### 使用ポート確認

```bash
ss -tuln
```

### 特定ポートの使用プロセス

```bash
sudo lsof -i :5002
```

---

## 8. カメラサーバー停止方法

### フォアグラウンド実行時

```bash
Ctrl + C
```

### バックグラウンド実行時

```bash
ps aux | grep camera_server.py
kill <PID>
```

---

## 9. Raspberry Pi 電源操作

### 安全に電源OFF（必須）

```bash
sudo shutdown -h now
```

### 再起動

```bash
sudo reboot
```

※ LED消灯後に電源を抜く

---

## 10. 露出制御について（現状整理）

* v4l2-ctl による露出制御は **Zero 2 W で動作可能**
* 通信量への影響：ほぼなし
* CPU負荷：設定変更時のみ微増
* 常時制御しなければ問題なし

---

## 11. 今後の予定

* [ ] systemd による自動起動
* [ ] 複数台同時管理（camera003 以降）
* [ ] YOLO 側の受信・同期設計
* [ ] RTSP 化の検討（必要なら）

---

## 12. 引き継ぎ時の一言用

> 本システムは Raspberry Pi Zero 2 W + C270 を用いた
> **640×480 / 8fps の MJPEG 配信**構成です。
> カメラ側は配信専用、解析はPC側でYOLOを実行します。

---

この内容が **現時点の最新・正確な状態**です。
もし **camera_server.py の該当コード確認**や
**8fps設定が本当に反映されているかのチェック方法**も必要なら、そこも整理します。

上記はchat gptと作っていたraspi+camera_server.pyなどをまとめてもらったものです。参考にしてraspi1217.mdを修正が必要であれば修正してください。
- [ ] `raspi1217.md` の内容を最終版に整形（必要なら追記・修正）。

---

## 起動手順まとめ（再起動後もこれでOK）

### 子機（Raspberry Pi）📷
1. Piの電源を入れる（USBカメラを挿したまま）。
2. 親機からSSHで接続  
   - `ssh pi@192.168.10.106`  # camera001  
   - `ssh pi@192.168.10.107`  # camera002
3. リポジトリへ移動  
   - `cd ~/peopleflow_app`
4. カメラサーバーを起動（ターミナルは開いたまま）  
   - camera0 → `python3 camera_server.py 0 5001`  
   - camera1 → `python3 camera_server.py 1 5002`  
   - 停止は `Ctrl+C`
5. 動作確認（任意）  
   - 親機ブラウザで `http://192.168.10.106:5001/` などにアクセスし、映像/情報を確認。

### 親機（Windows PC）🖥️
1. リポジトリへ移動  
   - `cd C:\Users\TY\Desktop\PGM\peopleflow_app`
2. 仮想環境を有効化  
   - `.\.venv\Scripts\activate`
3. YOLO用の環境変数をセット（起動するターミナルごとに実行）  
   - `$env:YOLO_MODEL_PATH="C:\Users\TY\Desktop\PGM\peopleflow_app\yolov8n.pt"`  
   - `$env:KNOWN_CHILD_IPS="192.168.10.106,192.168.10.107"`  
   - `$env:CAMERA_PORTS="5001,5002,5003,5004"`
4. マスターコンソール起動  
   - `python master_console/app.py`
5. ブラウザで確認  
   - `http://localhost:5050` を開く → 「接続を更新」を押す  
   - カメラ0/1が緑ランプ・映像表示、統合フレームが緑ならOK  
   - 人物が映ればYOLOのバウンディングボックスが出る。

### YOLOが動かないときのチェック ✅
- プロンプト先頭に `(.venv)` が付いているか確認（仮想環境が有効か）。  
- 依存パッケージ確認:  
  - `pip show ultralytics torch torchvision matplotlib pandas`  
  - 足りない場合は順に（必要時のみ再実行）  
    - `pip install --no-cache-dir "torch==2.9.1+cpu" "torchvision==0.24.1+cpu" --extra-index-url https://download.pytorch.org/whl/cpu`  
    - `pip install --no-cache-dir --only-binary=:all: "matplotlib==3.8.4"`  
    - `pip install --no-cache-dir "ultralytics==8.3.21"`  
- 起動ログに `YOLOモデルを読み込みました` が出ているか確認。  
- 映像に人が映っているかを確認（人がいないと検出が出ません）。


再起動後の手順を簡潔にまとめます。

1) カメラをPiに接続して電源ON
camera001 用PiにUSBカメラを挿す → 電源投入。
camera002 用Piも同様。
2) PCからPiへSSHし、カメラサーバー起動
PowerShellで（IPは確認済みのものを使う）:

ssh pi@192.168.10.106   # camera001
# ログイン後:
cd ~/peopleflow_app
python3 camera_server.py 0 5001
別ターミナルで:

ssh pi@192.168.10.107   # camera002
cd ~/peopleflow_app
python3 camera_server.py 1 5002
※この2つのターミナルは開いたまま。止めるときは Ctrl+C。

3) PCでマスターコンソール起動
PowerShellで:

cd C:\Users\TY\Desktop\PGM\peopleflow_app
.\.venv\Scripts\activate
$env:KNOWN_CHILD_IPS="192.168.10.106,192.168.10.107"
python master_console/app.py
4) ブラウザで確認
http://localhost:5000 を開く → 「接続を更新」を押す。
カメラ0/1が緑ランプ＆映像が出ればOK。個別確認は http://192.168.10.106:5001/ と http://192.168.10.107:5002/。
以上です。

---

```bash
sudo shutdown -h now
```
