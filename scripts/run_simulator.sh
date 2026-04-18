#!/usr/bin/env bash
# run_simulator.sh — runs the EV simulator

echo "Starting EV simulator..."
cd ev_simulator && python ev_simulator.py "$@"
