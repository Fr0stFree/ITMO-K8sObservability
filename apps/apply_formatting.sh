#!/usr/bin/env bash

set -euo pipefail

echo "[styling] Formatting python files..."

isort --line-length 120 common/ monitoring_service/ api_service/
black --line-length 120 common/ monitoring_service/ api_service/

echo "[styling] Files has been formatted successfully"
