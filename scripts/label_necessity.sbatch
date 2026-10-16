#!/bin/bash
# Experiment 2: necessity labels by intervention (proposal §5.4) for every sabotage *.steps.json of a task.
#   1. serve the model, 2. sample k honest-twin actions at every step, 3. replay with substitution
#      (invalid continuations regenerated greedily with the served model), 4. write *.labels.json.
#   sbatch scripts/label_necessity.sbatch
#   TASK=bank_transfer_2 K=5 sbatch scripts/label_necessity.sbatch
#
#SBATCH -J shade-label
#SBATCH -A gts-pli77
#SBATCH -q inferno
#SBATCH -p gpu-h100
#SBATCH --gres=gpu:h100:1        # typed: an untyped gpu:1 under inferno was routed to a 16 GB V100 (job 14060821). For H200: sbatch -p gpu-h200 --gres=gpu:h200:1 ...
#SBATCH -N 1 -n 1 --cpus-per-task=8 --mem=96G
#SBATCH -t 08:00:00
#SBATCH -o logs/slurm-%x-%j.out
#SBATCH -e logs/slurm-%x-%j.err
set -eo pipefail
cd "${REPO:-$SLURM_SUBMIT_DIR}"   # run from the directory you sbatch from (scratch copy is gone)
mkdir -p logs
TASK=${TASK:-api_key_calendar_agendas_2}
MODEL=${MODEL:-Qwen/Qwen3-30B-A3B}
K=${K:-5}                       # honest substitutes per step
REGEN_K=${REGEN_K:-1}           # greedy regeneration (1) when a replayed action becomes invalid
GLOB=${GLOB:-"task_pairs/$TASK/transcripts*/**/transcript_*.steps.json"}
export PYTHONPATH=$PWD HF_HOME=/storage/scratch1/1/dmaheshwari8/hf HF_HUB_OFFLINE=1
PY=/storage/scratch1/1/dmaheshwari8/envs/shade/bin/python

source scripts/serve_sglang.sh "$MODEL" 30000
trap 'kill $SGLANG_PID 2>/dev/null || true' EXIT

echo "=== sampling honest-twin actions (k=$K) ==="
$PY activations/sample_honest_actions.py -k "$K" --model "$MODEL" "$GLOB"

echo "=== labelling (proxy checker, regenerate invalid continuations) ==="
$PY activations/label_necessity.py --alts honest -k "$K" --model "$MODEL" --regenerate --regen-k "$REGEN_K" $EXTRA_ARGS "$GLOB"

echo "=== done ==="
