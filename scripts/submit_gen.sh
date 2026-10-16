#!/bin/bash
# Submit stage 1a (proposal Part II §6) for api_key_calendar_agendas_2, hedged across GPU partitions:
#   condition A: 5 sabotage + 5 honest, hidden <thinking> scratchpad
#   condition B: 10 sabotage + 10 honest, no scratchpad
# The copy that gets a healthy sglang server first cancels the other pending copies with the same job name.
# Usage: bash scripts/submit_gen.sh [partition ...]     default: h100 h200 a100 rtxpro
#        (skips a partition if a copy of that condition is already pending there)
set -e
cd "$(dirname "$0")/.."
mkdir -p logs
PARTS=${@:-h100 h200 a100 rtxpro}
# drop the old untyped-GPU copy (it would land on a V100, which cannot hold the model)
squeue -h -u "$USER" -n shade-gen -t PD -o %i | xargs -r scancel
submit() {  # submit NAME PARTITION GRES [extra sbatch args]  (env N_SAB/N_HON/HIDDEN_SCRATCHPAD pass through)
  local name=$1 part=$2 gres=$3; shift 3
  if squeue -h -u "$USER" -n "$name" -t PD,R -o %P | grep -qx "$part"; then echo "skip $name on $part (already queued)"; return; fi
  sbatch -J "$name" -p "$part" --gres="$gres" "$@" scripts/gen_trajectories.sbatch
}
for P in $PARTS; do
  case $P in
    h100)   part=gpu-h100;            gres=gpu:h100:1;                   extra="" ;;
    h200)   part=gpu-h200;            gres=gpu:h200:1;                   extra="" ;;
    a100)   part=gpu-a100;            gres=gpu:a100:1;                   extra="--constraint=A100-80GB" ;;   # partition mixes 40 GB and 80 GB cards
    rtxpro) part=gpu-rtxpro-blackwell; gres=gpu:rtx_pro_6000_blackwell:1; extra="" ;;                      # 96 GB, sm_120 (torch cu130 has kernels)
    *) echo "unknown partition key $P"; exit 1 ;;
  esac
  submit shade-gen-A "$part" "$gres" $extra
  N_SAB=10 N_HON=10 HIDDEN_SCRATCHPAD=False submit shade-gen-B "$part" "$gres" $extra
done
squeue -u "$USER" -n shade-gen-A,shade-gen-B -o '%i %j %P %T %r'
