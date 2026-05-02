#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 2 ]; then
  echo "Usage: ./scripts/run_demo.sh <INGEST_BATCH_ID> <FEATURE_SET_VERSION>"
  exit 1
fi

INGEST_BATCH_ID="$1"
FEATURE_SET_VERSION="$2"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

python -m src.features.cli --ingest-batch-id "$INGEST_BATCH_ID" --feature-set-version "$FEATURE_SET_VERSION" --window-spec 30d
python -m src.training.cli --ingest-batch-id "$INGEST_BATCH_ID" --feature-set-version "$FEATURE_SET_VERSION"
python -m src.evaluation.cli --ingest-batch-id "$INGEST_BATCH_ID" --feature-set-version "$FEATURE_SET_VERSION"
python -m src.visualization.cli --ingest-batch-id "$INGEST_BATCH_ID" --feature-set-version "$FEATURE_SET_VERSION"
