#!/usr/bin/env python3
from __future__ import annotations
import numpy as np
from dataclasses import dataclass
from collections import deque

rng = np.random.default_rng(0)

@dataclass
class CState:
    name: str
    power_w: float
    target_res_s: float
    entry_exit_j: float

LADDER = [
    CState("POLL", 3.50, 0.0, 1e-8),
    CState("C1E", 2.00, 20e-6, 1e-7),
    CState("C3", 0.70, 100e-6, 5e-6),
    CState("C6", 0.30, 200e-6, 50e-6),
    CState("C10", 0.08, 5000e-6, 300e-6),
]
N_ACTIONS = len(LADDER)

def state_energy(true_idle, s: CState) -> float:
    base = s.power_w * true_idle + s.entry_exit_j
    if true_idle < s.target_res_s:
        base += 3.0 * s.entry_exit_j
    return base

class RealHardwareTrace:
    def __init__(self, filepath="real_idle_trace.csv"):
        self.traces = []
        try:
            with open(filepath, 'r') as f:
                for row in f:
                    val = float(row.strip())
                    if val > 0:
                        self.traces.append(val)
        except FileNotFoundError:
            print("Warning: real_idle_trace.csv not found. Using synthetic.")
            self.traces = [np.random.exponential(0.001) for _ in range(100000)]
        print(f"Loaded {len(self.traces)} real idle events.")
        self.idx = 0
    def draw(self):
        val = self.traces[self.idx % len(self.traces)]
        self.idx += 1
        return val

_THRESH = np.array([s.target_res_s for s in LADDER[1:]])
_QLEVELS = 3
_N_SHAPE = _QLEVELS ** len(_THRESH)
_N_TREND = 3
N_STATES = _N_SHAPE * _N_TREND

def encode_state(recent) -> int:
    r = np.asarray(recent)
    fracs = np.mean(r[:, None] < _THRESH[None, :], axis=0)
    q = np.clip((fracs * _QLEVELS).astype(int), 0, _QLEVELS - 1)
    shape = 0
    for v in q:
        shape = shape * _QLEVELS + int(v)
    h = len(r) // 2
    if h >= 2:
        older, newer = r[:h].mean(), r[h:].mean()
        if newer > older * 1.3:
            trend = 2
        elif newer < older * 0.7:
            trend = 0
        else:
            trend = 1
    else:
        trend = 1
    return shape * _N_TREND + trend

class QAgent:
    def __init__(self, alpha=0.1, gamma=0.7, eps0=0.3, eps_decay=5e-6):
        self.Q = np.full((N_STATES, N_ACTIONS), 0.0)
        self.visits = np.zeros((N_STATES, N_ACTIONS), dtype=int)
        self.alpha, self.gamma = alpha, gamma
        self.eps, self.eps_decay = eps0, eps_decay
    def act(self, s: int) -> int:
        if np.any(self.visits[s] == 0):
            return int(np.argmin(self.visits[s]))
        if rng.random() < self.eps:
            return int(rng.integers(N_ACTIONS))
        return int(np.argmax(self.Q[s]))
    def learn(self, s, a, r, s_next):
        self.visits[s, a] += 1
        best_next = np.max(self.Q[s_next])
        td = r + self.gamma * best_next - self.Q[s, a]
        self.Q[s, a] += self.alpha * td
        self.eps = max(0.01, self.eps - self.eps_decay)

def pick_threshold(recent):
    med = float(np.median(recent))
    chosen = LADDER[0]
    for s in LADDER:
        if med >= s.target_res_s:
            chosen = s
    return chosen

def pick_expected(recent):
    r = np.asarray(recent)
    best, bestE = LADDER[0], np.inf
    for s in LADDER:
        base = s.power_w * r + s.entry_exit_j
        pen = np.where(r < s.target_res_s, 3.0 * s.entry_exit_j, 0.0)
        E = float(np.mean(base + pen))
        if E < bestE:
            bestE, best = E, s
    return best

def pick_oracle(ti):
    best, bestE = LADDER[0], np.inf
    for s in LADDER:
        E = state_energy(ti, s)
        if E < bestE:
            bestE, best = E, s
    return best

def run_hardware_replay(n=100000, window=64, trace_file="real_idle_trace.csv"):
    print(f"\n=== RUNNING ON REAL HARDWARE TRACE ({n} episodes) ===")
    trace = RealHardwareTrace(trace_file)
    agent = QAgent()
    recent = [800e-6] * 8
    C = {"threshold": 0.0, "expected": 0.0, "rl": 0.0, "oracle": 0.0}
    s = encode_state(recent)
    for t in range(n):
        ti = trace.draw()
        C["threshold"] += state_energy(ti, pick_threshold(recent))
        C["expected"] += state_energy(ti, pick_expected(recent))
        C["oracle"] += state_energy(ti, pick_oracle(ti))
        a = agent.act(s)
        e_rl = state_energy(ti, LADDER[a])
        C["rl"] += e_rl
        recent.append(ti)
        if len(recent) > window:
            del recent[0]
        s_next = encode_state(recent)
        agent.learn(s, a, -e_rl, s_next)
        s = s_next
    return agent, C

def regret(C, name):
    return (C[name] - C["oracle"]) / C["oracle"]

if __name__ == "__main__":
    agent, C = run_hardware_replay(n=100000)
    print(f"\n{'policy':>12} {'regret vs oracle':>18}")
    for name in ("threshold", "expected", "rl"):
        print(f"{name:>12} {regret(C,name)*100:>17.2f}%")