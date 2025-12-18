# Peopleflow App - AI Handover Prompt

You are assisting with a Windows + Raspberry Pi multi-camera peopleflow system. Keep these facts in context and avoid conflicting guidance from older docs.

## Topology / Hosts
- Mother PC (Windows) runs the main apps.
- Child Pis (camera servers):
  - camera001: 192.168.10.106, port 5001, camera_id 0
  - camera002: 192.168.10.107, port 5002, camera_id 1
  - camera_server.py is already running on each Pi (assumed).

## Apps & Ports
- order_counter/app.py → port 5000 (daily counter + stream/master control UI)
- master_console/app.py → port 5050 (integrated YOLO view/console)
- predictor/app.py → port 5100 (demand forecast UI). Set with env `PREDICT_PORT`.

## Key Env Vars (set in the shell before starting apps)
- `YOLO_MODEL_PATH="C:\Users\TY\Desktop\PGM\peopleflow_app\yolov8n.pt"`
- `KNOWN_CHILD_IPS="192.168.10.106,192.168.10.107"`
- `CAMERA_PORTS="5001,5002,5003,5004"`
- `PREDICT_PORT="5100"` (for predictor/app.py)

## Python Interpreter Handling (Windows)
- order_counter/app.py now auto-selects `.venv\Scripts\python.exe` (else .venv/bin/python, else sys.executable).
- PID files are written to the OS temp dir (tempfile.gettempdir()) to be cross-platform.
- Subprocesses inherit the above env vars via `_child_env()`.

## Data Files & Sync (important)
- YOLO writes people counts to `data/detections_minutely.jsonl` (repo root).
- Predictor reads `predictor/data/detections_minutely.jsonl`.
- To avoid manual copies, create a symlink (PowerShell admin/dev mode):
  ```
  cd C:\Users\TY\Desktop\PGM\peopleflow_app
  Remove-Item predictor\data\detections_minutely.jsonl -Force
  cmd /c mklink "C:\Users\TY\Desktop\PGM\peopleflow_app\predictor\data\detections_minutely.jsonl" "C:\Users\TY\Desktop\PGM\peopleflow_app\data\detections_minutely.jsonl"
  ```
- Orders live in `predictor/data/orders.jsonl`. Model in `predictor/data/model.json`.

## Start/Stop Cheat Sheet (Windows PowerShell)
```
cd C:\Users\TY\Desktop\PGM\peopleflow_app
.venv\Scripts\activate
$env:YOLO_MODEL_PATH="C:\Users\TY\Desktop\PGM\peopleflow_app\yolov8n.pt"
$env:KNOWN_CHILD_IPS="192.168.10.106,192.168.10.107"
$env:CAMERA_PORTS="5001,5002,5003,5004"

# Master console (YOLO integrated view)
python master_console\app.py   # opens 5050

# Daily counter + stream/master control
python order_counter\app.py    # opens 5000

# Predictor dashboard
$env:PREDICT_PORT="5100"
python predictor\app.py        # opens 5100

# Stop: Ctrl+C in each terminal
```

## Predictor Model Lifecycle
1) Ensure detections_minutely.jsonl is current (via symlink or Copy-Item).  
2) Train: `python predictor\train_model.py` (uses detections_minutely.jsonl + orders.jsonl).  
3) Run: `python predictor\app.py` (with PREDICT_PORT).  
4) If data changes, retrain and restart predictor.

## Dummy Data
- UI button “ダミー開始” or `python predictor\dummy.py` generates synthetic people counts every minute into `predictor/data/detections_minutely.jsonl`. Use for testing when real YOLO data is absent.

## Known Good URLs
- Counter UI: http://localhost:5000
- Master console/YOLO: http://localhost:5050
- Predictor UI: http://localhost:5100

## Pi Notes (from raspi1217.md)
- Camera servers run on 5001/5002 (extendable to 5003/5004). Device is usually `/dev/video0` (Logitech C270). Use ffmpeg/v4l2 for checks on Pi.

## Troubleshooting Quickies
- Predictor not changing: ensure detections_minutely.jsonl has fresh data and model retrained; start predictor with correct env vars.
- Stream/master buttons in 5000 UI failed on Windows because of Linux-only paths; fixed by tempdir + python selection + env propagation. Still need actual camera_server on Pi to see real streams.
