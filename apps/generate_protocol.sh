#!/usr/bin/env bash

set -euo pipefail

echo "[grpc] Starting protobuf generation..."

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROTO_DIR="${PROJECT_ROOT}/proto"
OUT_DIR="${PROJECT_ROOT}/protocol"

echo "[grpc] Project root:  ${PROJECT_ROOT}"
echo "[grpc] Proto dir:     ${PROTO_DIR}"
echo "[grpc] Output dir:    ${OUT_DIR}"

if [[ ! -d "${PROTO_DIR}" ]]; then
  echo "[grpc][error] Proto directory not found: ${PROTO_DIR}"
  exit 1
fi

mkdir -p "${OUT_DIR}"
touch "${OUT_DIR}/__init__.py"

PROTO_FILES=("${PROTO_DIR}"/*.proto)

if [[ ${#PROTO_FILES[@]} -eq 0 ]]; then
  echo "[grpc][error] No .proto files found in ${PROTO_DIR}"
  exit 1
fi

echo "[grpc] Found proto files:"
for f in "${PROTO_FILES[@]}"; do
  echo "  - $(basename "${f}")"
done

echo "[grpc] Cleaning old generated files..."
rm -f "${OUT_DIR}"/*_pb2.py "${OUT_DIR}"/*_pb2_grpc.py

echo "[grpc] Generating gRPC Python code..."
python -m grpc_tools.protoc \
  -I "${PROTO_DIR}" \
  --python_out="${OUT_DIR}" \
  --grpc_python_out="${OUT_DIR}" \
  --pyi_out="${OUT_DIR}" \
  "${PROTO_FILES[@]}"

echo "[grpc] Updating imports in generated gRPC files..."
for file in "${OUT_DIR}"/*_pb2_grpc.py; do
  sed -i '' \
    -e 's/^import \(.*_pb2\) as/from protocol import \1 as/' \
    "${file}"
done

echo "[grpc] Generation completed successfully."

echo "[grpc] Generated files:"
ls -1 "${OUT_DIR}"/*_pb2.py "${OUT_DIR}"/*_pb2_grpc.py