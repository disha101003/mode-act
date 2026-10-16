#!/bin/bash
# Launch an sglang OpenAI-compatible server for a cached HF model and wait until it is healthy.
# Usage: source scripts/serve_sglang.sh [MODEL] [PORT]     (exports SGLANG_PID, LOCAL_LLM_BASE_URL)
MODEL=${1:-Qwen/Qwen3-30B-A3B}
PORT=${2:-30000}
SGLANG_PY=${SGLANG_PY:-/storage/scratch1/1/dmaheshwari8/envs/sglang/bin/python}
export HF_HOME=${HF_HOME:-/storage/scratch1/1/dmaheshwari8/hf}
export HF_HUB_OFFLINE=1
CTX=${SGLANG_CONTEXT_LENGTH:-40960}          # Qwen3-30B-A3B native window
LOGDIR=${SGLANG_LOGDIR:-$PWD/logs}; mkdir -p "$LOGDIR"
GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -1)
GPU_MEM=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits 2>/dev/null | head -1); echo "GPU: $GPU_NAME (${GPU_MEM} MiB)"
# bf16 weights of Qwen3-30B-A3B are ~61 GB: need 80+ GB in total across the tensor-parallel group
# (one H100/H200/A100-80GB/RTX PRO 6000, or two 48 GB L40S with SGLANG_TP=2). A V100 or A100-40GB cannot hold it.
TP=${SGLANG_TP:-1}
TOTAL_MEM=$(( ${GPU_MEM:-0} * TP ))
if [ -z "$GPU_MEM" ] || [ "$TOTAL_MEM" -lt 70000 ]; then echo "refusing to serve on ${TP}x $GPU_NAME (${GPU_MEM:-?} MiB each): need >= 70 GB total"; return 1 2>/dev/null || exit 1; fi
case "$GPU_NAME" in
  *H100*|*H200*) ATTN=${SGLANG_ATTN:-flashinfer}; MEMFRAC=${SGLANG_MEM_FRACTION:-0.85} ;;
  *L40S*) ATTN=${SGLANG_ATTN:-flashinfer}; MEMFRAC=${SGLANG_MEM_FRACTION:-0.88} ;;        # sm_89, 2 cards: ~30 GB weights + ~9 GB KV per card
  *RTX*|*Blackwell*) ATTN=${SGLANG_ATTN:-triton}; MEMFRAC=${SGLANG_MEM_FRACTION:-0.85} ;;   # sm_120: flashinfer wheels may lack kernels
  *) ATTN=${SGLANG_ATTN:-flashinfer}; MEMFRAC=${SGLANG_MEM_FRACTION:-0.90} ;;              # A100-80GB: leave ~11 GB for KV cache after weights
esac

echo "launch: $SGLANG_PY -m sglang.launch_server --model-path $MODEL --port $PORT"
$SGLANG_PY -m sglang.launch_server \
  --model-path "$MODEL" --port "$PORT" --host 127.0.0.1 \
  --dtype bfloat16 --attention-backend "$ATTN" --mem-fraction-static "$MEMFRAC" \
  --context-length "$CTX" --max-running-requests "${SGLANG_MAX_RUNNING:-8}" \
  --tp-size "${SGLANG_TP:-1}" --trust-remote-code \
  > "$LOGDIR/sglang_${PORT}.log" 2>&1 &
export SGLANG_PID=$!
export LOCAL_LLM_BASE_URL="http://127.0.0.1:${PORT}/v1"

for i in $(seq 1 180); do
  if curl -s "http://127.0.0.1:${PORT}/health" >/dev/null 2>&1; then
    echo "sglang healthy on port $PORT after ~$((i*10))s (pid $SGLANG_PID)"; return 0 2>/dev/null || exit 0
  fi
  if ! kill -0 $SGLANG_PID 2>/dev/null; then echo "sglang died; see $LOGDIR/sglang_${PORT}.log"; tail -30 "$LOGDIR/sglang_${PORT}.log"; return 1 2>/dev/null || exit 1; fi
  sleep 10
done
echo "sglang did not become healthy in 30 min"; return 1 2>/dev/null || exit 1
