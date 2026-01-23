#!/usr/bin/env bash

set -euo pipefail

echo "Running ruff (fix)..."
ruff check . --fix

echo "Running isort..."
isort .

echo "Running black..."
black .

echo "Formatting completed successfully."
