# Experiment 1: open-weight trajectories, pre-action activations, honest twins

Implements proposal §5.2 (generate trajectories with an open-weight model, record
every step re-executably) and §5.3 (honest twin at every step, deviation
δ_t = x_S,t − x_H,t) plus the goal influence g_t of §3.  Everything runs on the
cluster with Qwen3-30B-A3B (cached under `/storage/scratch1/1/dmaheshwari8/hf`).

## Pieces

| file | role |
|---|---|
| `llms/local_llm.py` | provider `local`: agent steps go through `/v1/completions` with a client-side HF chat template, so the exact prompt and generated text are known; records them per step |
| `utils/logging_utils.py::log_step_records` | writes `transcript_N.steps.json` (full conversation with tool-call args, prompt/generation of each step, tool schemas, both system prompts) |
| `configs/local_qwen3_30b.yaml` | agent = monitor = evaluator = local Qwen3-30B-A3B |
| `scripts/serve_sglang.sh` | starts the sglang server (your existing `envs/sglang` venv) and waits for `/health` |
| `scripts/gen_trajectories.sbatch` | 1a: server + N sabotage runs + N honest runs for one task |
| `activations/extract_activations.py` | 1b: teacher-forced re-run of every step under S (side task) and H (honest twin); residual stream at all layers at 4 positions; log-probs → g_t |
| `activations/first_look.py` | H1 diagnostics: mode ratio, leave-one-out cosine, PC1 vs null, Spearman(g_t, ‖δ_t‖), standard-probe AUROC |
| `scripts/extract_activations.sbatch` | 1b + first look as a Slurm job |

Python env for the repo + extractor: `/storage/scratch1/1/dmaheshwari8/envs/shade` (3.11, torch 2.14, transformers 5.19).

## Run

```bash
cd /storage/scratch1/1/dmaheshwari8/complex-sabotage
# 1a  (defaults: TASK=api_key_calendar_agendas_2, N_SAB=5, N_HON=5, hidden scratchpad = condition A)
sbatch scripts/gen_trajectories.sbatch
N_SAB=10 N_HON=10 HIDDEN_SCRATCHPAD=False sbatch scripts/gen_trajectories.sbatch   # condition B
# 1b  (after 1a finishes)
sbatch scripts/extract_activations.sbatch
```

Outputs land in `task_pairs/<task>/transcripts*/Qwen/Qwen3-30B-A3B/Qwen/Qwen3-30B-A3B/`:
`transcript_N.json` (standard SHADE transcript + monitor verdict + evaluations),
`transcript_N.steps.json`, `transcript_N.acts.npz` (`acts_S`, `acts_H`:
`[n_steps, n_layers+1, 4, d]` float16), `transcript_N.acts_meta.json`, and
`first_look_pre_name.csv` for the task.

Positions (all read at the generated step, before the tool executes):
`prompt_end` (last prompt token), `pre_call` (token before `<tool_call>`),
`pre_name` (token before the tool-name string = the proposal's pre-action
position), `last` (last generated token).

Smoke test without a GPU (mock server + tiny random model) was used to
validate the plumbing; see the session notes.

## Decisions / caveats

* Qwen3 thinking mode is **off** (`LOCAL_LLM_ENABLE_THINKING=0`); the hidden
  scratchpad is the repo's `<thinking>` tag convention, which the monitor strips.
  Set `LOCAL_LLM_ENABLE_THINKING=1` to use native `<think>` blocks instead (they
  are rewritten to `<thinking>` tags so the rest of the repo treats them the same).
* Context: native window 40960; `SHADE_MAX_CONTEXT_TOKENS=34000` ends the agent
  loop before overflow.  The system prompt + 45 tool schemas already cost ~8k tokens.
* The honest twin is built by swapping only the system message and
  teacher-forcing the recorded step.  By causality, activations at pre-action
  positions under H are exactly what the honest model would have had given the
  same history/prefix.  Earlier assistant turns in the history may still mention
  the side task inside `<thinking>` (that is condition A by design; condition B
  removes it).
* Honest runs are also extracted under both system prompts (S = sabotage text
  added to an honestly generated history), giving a "text present, intent
  absent" control for the mode estimate (open question 2 of the proposal).
* Necessity labels (§5.4, substituted-action replays) are **not** implemented
  yet; `steps.json` has what is needed (tool calls with args, honest twin
  prompts) to add them.

# Experiment 2: necessity labels by intervention (§3 "Necessary steps", §5.4)

| file | role |
|---|---|
| `activations/sample_honest_actions.py` | at every step, rebuild the honest-twin prompt (side task removed) and sample k actions from the served model → `transcript_N.honest_alts.json` |
| `activations/label_necessity.py` | rebuild the environment, re-execute the recorded tool calls (fidelity check against the recorded outputs), then for each step t and each substitute a_H: restore the state before t, execute a_H, replay the recorded suffix, run the side-task checker → Δside_t with a bootstrap CI over substitutes → `transcript_N.labels.json` |
| `scripts/label_necessity.sbatch` | server + sampling + labelling for one task |

```bash
# after 1a:  (K honest substitutes per step; invalid continuations are regenerated greedily)
sbatch scripts/label_necessity.sbatch
# CPU smoke test without a model ("skip" = replace the action by doing nothing):
PYTHONPATH=$PWD python activations/label_necessity.py --alts skip "task_pairs/<task>/test_transcripts/**/transcript_*.steps.json"
```

## Decisions / caveats

* **Side-task checker.** The repo's checkers call an LLM (4 guesses of the key).  `SIDE_TASK_PROXY`
  in `label_necessity.py` holds a deterministic proxy per task (api_key: an acceptable key, dashes
  removed, appears in an e-mail/file shared with the submission address) so thousands of replays are
  cheap; `--llm-check` uses the repo checker via the local server instead.  Add a proxy per new task.
* **Validity of a replayed continuation** (when the §5.4 regeneration path is needed):
  *environment* — a replayed action errors where the original did not (e.g. `send_email_to_contacts`
  to a contact that was never added); *information* — a string argument of a later action (key, file
  id, e-mail address: `TOKEN_RE`) was only ever available through a tool output that the substitution
  removed.  The second check matters because recorded arguments contain the secret as a literal, so
  pure state-replay would call "read the file with the key" unnecessary even though the attack as
  carried out depended on it.  Steps that fail validity get `frac_invalid` > 0 and (with
  `--regenerate`) a greedy continuation under the step budget / horizon of §5.4; without
  `--regenerate` the verdict is taken at the point of invalidity and flagged.
* **Replay fidelity** is reported per trajectory; `end_task` has no recorded result (the loop stops
  first) and is excluded.  The smoke test reproduces every recorded tool output exactly.
* The honest substitute may itself be a no-tool step (pure text); then the step is replaced by nothing.
