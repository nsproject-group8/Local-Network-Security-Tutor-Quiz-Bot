#!/usr/bin/env bash
set -euo pipefail

# Script to build the frontend on the host and then build/start Docker Compose
# This avoids cross-arch native optional-dependency issues when building
# frontend assets inside a container (common on Apple Silicon).

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR/frontend"

echo "Installing frontend deps locally..."
npm ci

echo "Building frontend (produces ./dist)..."
npm run build

cd "$ROOT_DIR"

echo "Building and starting Docker Compose (frontend will reuse local dist)..."
docker compose build frontend
docker compose up -d

echo "Done. Frontend served at http://localhost:3000 and backend at http://localhost:8000" 
