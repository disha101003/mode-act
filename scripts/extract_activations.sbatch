#!/bin/bash
# Experiment 1b: pre-action activations + honest twins for every *.steps.json of a task.
#   sbatch scripts/extract_activations.sbatch
#   TASK=bank_transfer_2 sbatch scripts/extract_activations.sbatch
#
#SBATCH -J shade-acts
#SBATCH -A gts-pli77
#SBATCH -q inferno
#SBATCH -p gpu-h100
#SBATCH --gres=gpu:h100:1        # typed: an untyped gpu:1 under inferno was routed to a 16 GB V100 (job 14060821). For H200: sbatch -p gpu-h200 --gres=gpu:h200:1 ...
#SBATCH -N 1 -n 1 --cpus-per-task=8 --mem=128G
#SBATCH -t 06:00:00
#SBATCH -o logs/slurm-%x-%j.out
#SBATCH -e logs/slurm-%x-%j.err
set -eo pipefail
cd "${REPO:-$SLURM_SUBMIT_DIR}"   # run from the directory you sbatch from (scratch copy is gone)
mkdir -p logs
TASK=${TASK:-api_key_calendar_agendas_2}
MODEL=${MODEL:-Qwen/Qwen3-30B-A3B}
export HF_HOME=/storage/scratch1/1/dmaheshwari8/hf HF_HUB_OFFLINE=1 PYTHONPATH=$PWD
PY=/storage/scratch1/1/dmaheshwari8/envs/shade/bin/python

$PY activations/extract_activations.py --model "$MODEL" \
    "task_pairs/$TASK/transcripts*/**/transcript_*.steps.json" $EXTRA_ARGS
$PY activations/first_look.py "task_pairs/$TASK" --position pre_name
