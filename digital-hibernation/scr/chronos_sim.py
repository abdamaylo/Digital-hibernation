#!/usr/bin/env python3
import numpy as np
from collections import deque
from dataclasses import dataclass
from typing import List, Tuple

@dataclass
class CState:
    name: str
    entry_latency: float
    exit_latency: float
    power: float
    target_residency: float = 0

class IdlePredictor:
    def __init__(self, window_size: int = 50):
        self.window = deque(maxlen=window_size)
    def update(self, duration: float):
        self.window.append(duration)
    def predict_point(self) -> float:
        if not self.window:
            return 0.5
        return np.median(self.window)
    def predict_distribution(self):
        if not self.window:
            return np.array([0.5])
        return np.array(self.window)

class PeriodicPredictor:
    def __init__(self, num_bins: int = 96):
        self.bins = [[] for _ in range(num_bins)]
        self.num_bins = num_bins
        self.bin_duration = 15 * 60
    def get_bin(self, timestamp: float) -> int:
        seconds_in_day = timestamp % (24 * 3600)
        return int(seconds_in_day // self.bin_duration)
    def update(self, timestamp: float, duration: float):
        bin_idx = self.get_bin(timestamp)
        self.bins[bin_idx].append(duration)
        if len(self.bins[bin_idx]) > 500:
            self.bins[bin_idx] = self.bins[bin_idx][-250:]
    def predict_distribution(self, timestamp: float):
        bin_idx = self.get_bin(timestamp)
        if not self.bins[bin_idx]:
            return np.array([0.5])
        return np.array(self.bins[bin_idx])

def choose_cstate_expected_energy(distribution, cstates):
    expected_idle = np.mean(distribution)
    best_state = cstates[0]
    min_energy = float('inf')
    for cstate in cstates:
        if expected_idle < cstate.target_residency / 1e6:
            continue
        entry_cost = cstate.power * (cstate.entry_latency / 1e6)
        exit_cost = cstate.power * (cstate.exit_latency / 1e6)
        idle_time = max(0, expected_idle - (cstate.entry_latency + cstate.exit_latency) / 1e6)
        total_energy = entry_cost + exit_cost + cstate.power * idle_time
        if total_energy < min_energy:
            min_energy = total_energy
            best_state = cstate
    return best_state

def choose_cstate(expected_idle, cstates):
    chosen = cstates[0]
    for cstate in cstates:
        if cstate.target_residency / 1e6 <= expected_idle:
            chosen = cstate
    return chosen

def compute_power(trace, cstates, predictor_type='baseline'):
    total = 0.0
    if predictor_type == 'baseline':
        predictor = IdlePredictor()
    else:
        predictor = PeriodicPredictor()
    for timestamp, duration in trace:
        if predictor_type == 'baseline':
            cstate = choose_cstate(predictor.predict_point(), cstates)
            predictor.update(duration)
        else:
            cstate = choose_cstate_expected_energy(predictor.predict_distribution(timestamp), cstates)
            predictor.update(timestamp, duration)
        if duration < cstate.entry_latency / 1e6:
            continue
        idle_time = max(0, duration - (cstate.entry_latency + cstate.exit_latency) / 1e6)
        total += cstate.power * (cstate.entry_latency / 1e6)
        total += cstate.power * (cstate.exit_latency / 1e6)
        total += cstate.power * idle_time
    return total

def generate_trace(days=7):
    trace = []
    for t in range(0, days * 24 * 3600, 10):
        hour = (t % (24 * 3600)) / 3600
        mean = 0.05 * (0.5 + 0.5 * np.sin(2 * np.pi * hour / 24))
        trace.append((t, np.random.exponential(max(mean, 0.001))))
    return trace

def generate_flat_trace(days=7):
    trace = []
    for t in range(0, days * 24 * 3600, 10):
        trace.append((t, np.random.exponential(0.05)))
    return trace

def main():
    cstates = [
        CState("POLL", 0, 0, 2.5),
        CState("C1", 2, 2, 1.8),
        CState("C3", 50, 100, 0.7),
        CState("C6", 200, 500, 0.3),
        CState("C8", 2000, 8000, 0.08),
    ]
    print("=" * 60)
    print("CHRONOS: Digital Cellular Hibernation Simulator")
    print("=" * 60)
    trace = generate_trace(7)
    e_baseline = compute_power(trace, cstates, 'baseline')
    e_periodic = compute_power(trace, cstates, 'periodic')
    eta = (e_baseline - e_periodic) / e_baseline * 100
    print(f"\n[Periodic Trace]")
    print(f"  Baseline: {e_baseline:.3f} J")
    print(f"  Periodic: {e_periodic:.3f} J")
    print(f"  eta (savings): {eta:+.2f}%")
    trace_flat = generate_flat_trace(7)
    e_baseline_flat = compute_power(trace_flat, cstates, 'baseline')
    e_periodic_flat = compute_power(trace_flat, cstates, 'periodic')
    eta_flat = (e_baseline_flat - e_periodic_flat) / e_baseline_flat * 100
    print(f"\n[Flat Trace - Negative Control]")
    print(f"  Baseline: {e_baseline_flat:.3f} J")
    print(f"  Periodic: {e_periodic_flat:.3f} J")
    print(f"  eta (savings): {eta_flat:+.2f}%")
    print("\n" + "=" * 60)
    print("Done.")
    print("=" * 60)

if __name__ == "__main__":
    main()