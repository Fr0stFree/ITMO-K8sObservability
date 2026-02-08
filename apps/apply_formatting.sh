#!/usr/bin/env bash

set -euo pipefail

echo "[formatting] Running ruff (fix)..."
ruff check . --fix

echo "[formatting] Running isort..."
isort .

echo "[formatting] Running black..."
black .

echo "[formatting] Formatting completed successfully."
