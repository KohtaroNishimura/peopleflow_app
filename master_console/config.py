"""
設定ファイル
"""
import os

# Flask設定
FLASK_HOST = os.getenv('FLASK_HOST', '0.0.0.0')
FLASK_PORT = int(os.getenv('FLASK_PORT', 5000))
DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'

# カメラ設定
MAX_CAMERAS = 4
# カメラサーバーのポート
# テスト環境（app.pyが5000を使用）: デフォルトは5001-5004
# 本番環境（子機が5000-5003を使用）: 環境変数 CAMERA_PORTS="5000,5001,5002,5003" で設定
CAMERA_PORTS_STR = os.getenv('CAMERA_PORTS', '5001,5002,5003,5004')
CAMERA_PORTS = [int(p.strip()) for p in CAMERA_PORTS_STR.split(',')]
# 子機のIPアドレス（環境変数または直接指定）
CAMERA_BASE_URL = os.getenv('CAMERA_BASE_URL', 'http://localhost')

# データ保存設定
DATA_DIR = os.getenv('DATA_DIR', 'data')

# YOLO設定
YOLO_MODEL_PATH = os.getenv('YOLO_MODEL_PATH', None)  # Noneの場合はデフォルトモデル
YOLO_CONFIDENCE_THRESHOLD = float(os.getenv('YOLO_CONFIDENCE_THRESHOLD', '0.5'))

# ストリーミング設定
STREAM_QUEUE_SIZE = int(os.getenv('STREAM_QUEUE_SIZE', '10'))  # フレームキューサイズ
FRAME_WIDTH = int(os.getenv('FRAME_WIDTH', '320'))  # 統合フレームの各カメラ幅
FRAME_HEIGHT = int(os.getenv('FRAME_HEIGHT', '240'))  # 統合フレームの各カメラ高さ

