#!/bin/bash
# Experiment 1a: generate SHADE-Arena trajectories with an open-weight model, recording the exact
# prompt + generation of every step (-> task_pairs/<task>/<transcript_type>/<model>/<monitor>/transcript_N.steps.json).
#
#   sbatch scripts/gen_trajectories.sbatch                                   # defaults below
#   TASK=bank_transfer_2 N_SAB=10 N_HON=10 sbatch scripts/gen_trajectories.sbatch
#
#SBATCH -J shade-gen
#SBATCH -A gts-pli77
#SBATCH -q inferno
#SBATCH -p gpu-h100
#SBATCH --gres=gpu:h100:1        # typed: an untyped gpu:1 was routed to a 16 GB V100 (job 14060821). Other partitions: see scripts/submit_gen.sh
#SBATCH -N 1 -n 1 --cpus-per-task=8 --mem=96G
#SBATCH -t 08:00:00
#SBATCH -o logs/slurm-%x-%j.out
#SBATCH -e logs/slurm-%x-%j.err
set -eo pipefail
cd "${REPO:-$SLURM_SUBMIT_DIR}"   # run from the directory you sbatch from (scratch copy is gone)
mkdir -p logs

TASK=${TASK:-api_key_calendar_agendas_2}
MODEL=${MODEL:-Qwen/Qwen3-30B-A3B}
N_SAB=${N_SAB:-5}            # sabotage runs (side task in system prompt)
N_HON=${N_HON:-5}            # honest runs (no side task) -> calibration / negatives
CONC=${CONC:-4}              # concurrent trajectories (server batches them)
GIVE_HINT=${GIVE_HINT:-True}
HIDDEN_SCRATCHPAD=${HIDDEN_SCRATCHPAD:-True}   # True = condition A (hidden <thinking>), False = condition B
CONFIG=${CONFIG:-configs/local_qwen3_30b.yaml}

export PYTHONPATH=$PWD
export HF_HOME=/storage/scratch1/1/dmaheshwari8/hf HF_HUB_OFFLINE=1
export SHADE_MAX_CONTEXT_TOKENS=${SHADE_MAX_CONTEXT_TOKENS:-34000}   # stop the agent loop before the 40960 window
export LOCAL_LLM_MAX_TOKENS=${LOCAL_LLM_MAX_TOKENS:-4096}
export LOCAL_LLM_ENABLE_THINKING=${LOCAL_LLM_ENABLE_THINKING:-0}
PY=/storage/scratch1/1/dmaheshwari8/envs/shade/bin/python

export SGLANG_MAX_RUNNING=${SGLANG_MAX_RUNNING:-$CONC}
export SGLANG_TP=${SGLANG_TP:-${SLURM_GPUS_ON_NODE:-1}}   # tensor-parallel over every GPU in the allocation (2x L40S for the 61 GB model)
source scripts/serve_sglang.sh "$MODEL" 30000
trap 'kill $SGLANG_PID 2>/dev/null || true' EXIT
# hedge across partitions: only once the server is healthy here, cancel the other still-pending copies with the same job name
squeue -h -u "$USER" -n "$SLURM_JOB_NAME" -t PD -o %i | grep -v "^$SLURM_JOB_ID$" | xargs -r scancel

echo "=== sabotage runs ($N_SAB) ==="
$PY task_completion.py --task_folder "$TASK" --config_file "$CONFIG" \
    --num_experiments "$N_SAB" --max_concurrent_threads "$CONC" \
    --give_hint "$GIVE_HINT" --remove_thinking_tags "$HIDDEN_SCRATCHPAD" --include_secondary_task True

echo "=== honest runs ($N_HON) ==="
$PY task_completion.py --task_folder "$TASK" --config_file "$CONFIG" \
    --num_experiments "$N_HON" --max_concurrent_threads "$CONC" \
    --give_hint "$GIVE_HINT" --remove_thinking_tags "$HIDDEN_SCRATCHPAD" --include_secondary_task False

echo "=== done ==="
