#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="$ROOT_DIR/.venv"

if [[ -d "$VENV_DIR" ]]; then
  # shellcheck source=/dev/null
  . "$VENV_DIR/bin/activate"
fi

export PREDICTOR_DETECTIONS_FILE="${PREDICTOR_DETECTIONS_FILE:-$ROOT_DIR/data/detections_minutely.jsonl}"
export PREDICTOR_ORDERS_FILE="${PREDICTOR_ORDERS_FILE:-$ROOT_DIR/predictor/data/orders.jsonl}"
export PREDICTOR_RESULTS_FILE="${PREDICTOR_RESULTS_FILE:-$ROOT_DIR/predictor/data/prediction_results.txt}"
export PREDICTOR_MODEL_FILE="${PREDICTOR_MODEL_FILE:-$ROOT_DIR/predictor/data/model_real.json}"
export PREDICTOR_CAMERA_IDS="${PREDICTOR_CAMERA_IDS:-0}"
export PREDICT_PORT="${PREDICT_PORT:-5100}"

exec python "$ROOT_DIR/predictor/app.py"
