#!/usr/bin/env bash
# start.sh — starts backend and frontend dev servers

echo "Starting GuardCharge backend..."
cd backend && uvicorn main:app --reload --port 8000 &

echo "Starting GuardCharge frontend..."
cd frontend && npm run dev
