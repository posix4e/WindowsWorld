#!/usr/bin/env python3
"""Read-only WindowsWorld progress check. Does NOT mutate hf_result (unlike
show_result.py, which deletes result-less/in-progress task dirs). Safe to run
while the benchmark is live."""
import glob, re, os, subprocess

TOTAL = 181
inter, final, by_level = [], [], {}
for f in sorted(glob.glob("hf_result/win_*/*/result.json")):
    txt = open(f, encoding="utf-8", errors="replace").read()
    m = re.search(r"Intermediate Score:\s*([0-9.]+),\s*Final Result:\s*([0-9.]+)", txt)
    if not m:
        continue
    i, fi = float(m.group(1)), float(m.group(2))
    inter.append(i); final.append(fi)
    lvl = re.search(r"win_\w+?__(l\d)_", f)
    lvl = lvl.group(1).upper() if lvl else "?"
    by_level.setdefault(lvl, []).append((i, fi))

n = len(inter)
print(f"tasks scored: {n}/{TOTAL}")
if n:
    print(f"mean Intermediate: {100*sum(inter)/n:.1f}%   mean Final: {100*sum(final)/n:.1f}%")
    for lvl in sorted(by_level):
        v = by_level[lvl]
        mi = 100*sum(x[0] for x in v)/len(v)
        mf = 100*sum(x[1] for x in v)/len(v)
        print(f"  {lvl}: {len(v)} tasks, Inter {mi:.0f}%, Final {mf:.0f}%")

# run alive?
try:
    ps = subprocess.run(["ps", "-eo", "pid,etimes,cmd"], capture_output=True, text=True).stdout
    live = [l for l in ps.splitlines() if "hf_run.py" in l and "grep" not in l]
    print("RUN:", f"alive ({live[0].split()[0]}, {int(live[0].split()[1])//60}m)" if live else "NOT RUNNING (complete or stopped)")
except Exception as e:
    print("RUN: ?", e)

# LLM failures
log = "/tmp/windowsworld_full.log"
if os.path.exists(log):
    lt = open(log, encoding="utf-8", errors="replace").read()
    print(f"LLM failures: {lt.count('Failed to call LLM')} | tracebacks: {lt.count('Traceback')}")
