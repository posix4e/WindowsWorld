#!/usr/bin/env bash
# WindowsWorld benchmark runner. Usage:
#   ./run_windowsworld.sh smoke    # 1 task (benchmark_smoke.json)
#   ./run_windowsworld.sh full     # all 181 tasks
set -euo pipefail
cd "$(dirname "$0")"
[ -f /home/tdx2/.windowsworld.env ] && set -a && . /home/tdx2/.windowsworld.env && set +a
MODE="${1:-smoke}"
# Model routing (mm_agents/agent.py):
#   id WITH '/'  (e.g. anthropic/claude-opus-4.8) -> OpenAI-compatible router at OPENAI_API_BASE (OpenRouter)
#   id like claude-* (no '/')                     -> direct Anthropic (api.anthropic.com, x-api-key)
MODEL="${MODEL:-anthropic/claude-opus-4.8}"
if [[ "$MODEL" == */* ]]; then
  : "${OPENAI_API_KEY:?OPENAI_API_KEY not set — put it in /home/tdx2/.windowsworld.env}"
  : "${OPENAI_API_BASE:?OPENAI_API_BASE not set — put it in /home/tdx2/.windowsworld.env}"
else
  : "${ANTHROPIC_API_KEY:?ANTHROPIC_API_KEY not set — put it in /home/tdx2/.windowsworld.env}"
fi
BENCH="benchmark_smoke.json"
[ "$MODE" = "full" ] && BENCH="benchmark.json"
VMX=/home/tdx2/vms/WindowsWorld/Windows0/Windows0.vmx
echo "Running $MODE: -b $BENCH -m $MODEL -a pyautogui -o screenshot (via ${OPENAI_API_BASE:-api.anthropic.com})"
exec .venv/bin/python hf_run.py -b "$BENCH" -v "$VMX" \
  -m "$MODEL" -a pyautogui -o screenshot
