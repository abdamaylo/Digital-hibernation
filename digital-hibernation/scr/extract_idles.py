#!/usr/bin/env python3
import subprocess
import re

print("Extracting real idle durations from trace.dat (Per-Core accurate)...")
result = subprocess.run(['trace-cmd', 'report'], capture_output=True, text=True)
lines = result.stdout.split('\n')

idles = []
entry_times = {}
pattern = re.compile(r'(\d+\.\d+):\s+cpu_idle:\s+state=(\d+)\s+cpu_id=(\d+)')

for line in lines:
    match = pattern.search(line)
    if not match:
        continue
    t = float(match.group(1))
    state = int(match.group(2))
    cpu_id = match.group(3)
    if state == 4294967295:
        if cpu_id in entry_times:
            duration = t - entry_times[cpu_id]
            if duration > 0:
                idles.append(duration)
            del entry_times[cpu_id]
    else:
        entry_times[cpu_id] = t

with open('real_idle_trace.csv', 'w') as f:
    for d in idles:
        f.write(f"{d}\n")

print(f"Success! Extracted {len(idles)} CLEAN real idle events to real_idle_trace.csv")