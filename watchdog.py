#!/usr/bin/env python3
"""Supervisor for the WindowsWorld benchmark run.

- Starts ./run_windowsworld.sh full if not running.
- Restarts it if it crashes while tasks remain.
- If the run STALLS (no log progress for WATCHDOG_STALL seconds while alive),
  kills it, writes a forced 0-score result for the current task so it is NOT
  retried forever, and restarts -> cleanly force-advances past a hang.
- Exits once all TOTAL tasks have a result.json.

Run detached:
  cd /home/tdx2/src/WindowsWorld
  nohup .venv/bin/python watchdog.py > /tmp/ww_watchdog.log 2>&1 &
"""
import os, re, glob, time, subprocess

ROOT = "/home/tdx2/src/WindowsWorld"
LOG = "/tmp/windowsworld_full.log"
VMX = "/home/tdx2/vms/WindowsWorld/Windows0/Windows0.vmx"
TOTAL = 181
STALL = int(os.environ.get("WATCHDOG_STALL", "420"))   # seconds of no log growth = hung
CHECK = 60                                             # poll interval

os.chdir(ROOT)


def log(m):
    print(f"[watchdog {time.strftime('%H:%M:%S')}] {m}", flush=True)


def completed():
    return len(glob.glob("hf_result/win_*/*/result.json"))


def run_alive():
    return bool(subprocess.run(["pgrep", "-f", "hf_run.py"],
                               capture_output=True, text=True).stdout.split())


def marker():
    """Strictly grows while the run writes anything; static while hung."""
    try:
        return os.path.getsize(LOG)
    except OSError:
        return 0


def current_task():
    try:
        t = open(LOG, encoding="utf-8", errors="replace").read()
    except FileNotFoundError:
        return None
    m = re.findall(r"Running task:\s*(\S+?)\.", t)
    return m[-1] if m else None


def stub_task(task_id):
    if not task_id:
        return
    d = os.path.join("hf_result", task_id, "watchdog_skip")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "result.json"), "w", encoding="utf-8") as f:
        f.write("Task Instruction: <force-skipped by watchdog after stall>\n")
        f.write("Intermediate Score: 0.0, Final Result: 0\n")
        f.write('{"final_result": {"result": false, "reason": "stalled; force-advanced by watchdog"}}\n')
    log(f"stubbed {task_id} as 0 (force-advanced past stall)")


def kill_run():
    subprocess.run(["pkill", "-9", "-f", "hf_run.py"])
    subprocess.run(["vmrun", "-T", "ws", "stop", VMX, "hard"],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["pkill", "-9", "-f", "vmware-vmx"])
    time.sleep(4)


def start_run():
    subprocess.Popen(f"nohup ./run_windowsworld.sh full >> {LOG} 2>&1 &",
                     shell=True)
    time.sleep(8)
    log("(re)started run")


last_marker, last_change = marker(), time.time()
log(f"up. completed={completed()}/{TOTAL}, stall_threshold={STALL}s")

while True:
    done = completed()
    if done >= TOTAL:
        log(f"all {done}/{TOTAL} tasks have results — supervisor exiting")
        break

    if not run_alive():
        log(f"run not active ({done}/{TOTAL} done) — restarting")
        start_run()
        last_marker, last_change = marker(), time.time()
        time.sleep(CHECK)
        continue

    mk = marker()
    if mk != last_marker:
        last_marker, last_change = mk, time.time()
    elif time.time() - last_change > STALL:
        tid = current_task()
        log(f"STALL: no log progress {int(time.time()-last_change)}s on {tid} — force-advancing")
        kill_run()
        stub_task(tid)
        start_run()
        last_marker, last_change = marker(), time.time()

    time.sleep(CHECK)
