#!/usr/bin/env bash
# WindowsWorld benchmark runner. Usage:
#   ./run_windowsworld.sh smoke    # 1 task (benchmark_smoke.json)
#   ./run_windowsworld.sh full     # all 181 tasks
set -euo pipefail
cd "$(dirname "$0")"
[ -f /home/tdx2/.windowsworld.env ] && set -a && . /home/tdx2/.windowsworld.env && set +a
: "${ANTHROPIC_API_KEY:?ANTHROPIC_API_KEY not set — put it in /home/tdx2/.windowsworld.env}"
MODE="${1:-smoke}"
# claude-* (no '/') routes to the direct Anthropic path (api.anthropic.com, x-api-key).
# A model id containing '/' (e.g. anthropic/claude-opus-4.8) routes via OPENAI_API_BASE (TrustedRouter).
MODEL="${MODEL:-claude-opus-4-8}"
BENCH="benchmark_smoke.json"
[ "$MODE" = "full" ] && BENCH="benchmark.json"
VMX=/home/tdx2/vms/WindowsWorld/Windows0/Windows0.vmx
echo "Running $MODE: -b $BENCH -m $MODEL -a pyautogui -o screenshot (via ${OPENAI_API_BASE:-api.anthropic.com})"
exec .venv/bin/python hf_run.py -b "$BENCH" -v "$VMX" \
  -m "$MODEL" -a pyautogui -o screenshot
