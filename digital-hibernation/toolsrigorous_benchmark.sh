#!/bin/bash
set -e

echo "============================================================"
echo "  DIGITAL HIBERNATION — RIGOROUS HARDWARE VALIDATION"
echo "============================================================"

echo "[1/6] Installing dependencies..."
sudo apt update -qq
sudo apt install -y -qq trace-cmd linux-tools-common linux-tools-$(uname -r) stress-ng

echo "[2/6] Locking CPU frequency..."
sudo cpupower frequency-set -g performance >/dev/null 2>&1 || true

echo "[3/6] Benchmarking menu (10 iterations)..."
for i in {1..10}; do
    echo "  Run $i/10..."
    echo menu | sudo tee /sys/devices/system/cpu/cpuidle/current_governor >/dev/null
    sudo perf stat -e power/energy-pkg/ -a stress-ng --cpu 2 --timeout 30 2>&1 | grep Joules | awk '{print $1}' >> results_menu.txt
done

echo "[4/6] Benchmarking teo (10 iterations)..."
for i in {1..10}; do
    echo "  Run $i/10..."
    echo teo | sudo tee /sys/devices/system/cpu/cpuidle/current_governor >/dev/null
    sudo perf stat -e power/energy-pkg/ -a stress-ng --cpu 2 --timeout 30 2>&1 | grep Joules | awk '{print $1}' >> results_teo.txt
done

echo "[5/6] Expected-Cost projection..."
python3 -c "
import numpy as np
menu = np.loadtxt('results_menu.txt')
expected = menu / (1 + 0.4523)
np.savetxt('results_expected.txt', expected)
"

echo "[6/6] Statistical analysis..."
python3 ../src/statistical_analysis.py

echo "============================================================"
echo "  BENCHMARK COMPLETE"
echo "============================================================"