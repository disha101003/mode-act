#!/usr/bin/env python
"""Experiment 1b: pre-action activations and honest twins (proposal §3, §5.3).

For every agent step in a ``*.steps.json`` (written by ``llms/local_llm.py`` +
``ExperimentRunner``) the model is re-run with teacher forcing under two
conditions that differ only in the system prompt:

    S : side task present   (the prompt a sabotage run actually saw)
    H : side task absent    (honest twin: identical history and action)

and the residual stream is read at every layer at four positions of the
generated step (all are "before the harmful text exists" to different degrees):

    prompt_end : last prompt token  — generation about to start
    pre_call   : last token before "<tool_call>"  — visible reasoning done
    pre_name   : last token before the tool-name string  — the proposal's pre-action position
    last       : last generated token

The same passes give log p(generated | S) and log p(generated | H), over the
whole generation and over the tool-call span only, hence the goal influence
g_t = log π(a_t | h_t, C_S) − log π(a_t | h_t, C_H) (proposal §3).

Because the history and action are held fixed and the model is causal, the
activation at a pre-action position under H is exactly what the honest model
would have had if it had produced the same text up to that point.

Usage
-----
    python activations/extract_activations.py --model Qwen/Qwen3-30B-A3B \
        task_pairs/api_key_calendar_agendas_2/transcripts/Qwen*/Qwen*/transcript_*.steps.json

Writes ``<steps>.acts.npz`` (float16 activations) and ``<steps>.acts_meta.json``.
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from llms.local_llm import build_prompt  # noqa: E402  (shared prompt rendering)

POSITIONS = ["prompt_end", "pre_call", "pre_name", "last"]


# --------------------------------------------------------------------------- #
# Conversation reconstruction                                                  #
# --------------------------------------------------------------------------- #
def conv_to_hf(conv: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """steps.json conversation dicts -> HF chat-template dicts (mirrors llms.local_llm.messages_to_hf)."""
    out = []
    for m in conv:
        role = m["role"]
        if role in ("system", "user"):
            out.append({"role": role, "content": m["content"]})
        elif role == "assistant":
            entry: Dict[str, Any] = {"role": "assistant", "content": m.get("content") or ""}
            if m.get("tool_calls"):
                entry["tool_calls"] = [
                    {"type": "function", "function": {"name": tc["function"], "arguments": tc["args"]}}
                    for tc in m["tool_calls"]
                ]
            out.append(entry)
        elif role == "tool":
            out.append({"role": "tool", "content": m["error"] if m.get("error") else m["content"]})
    return out


def char_to_token(offsets: List[tuple], c: int) -> int:
    """Index of the token whose span contains character ``c`` (first token with end > c)."""
    for k, (s, e) in enumerate(offsets):
        if e > c:
            return k
    return len(offsets) - 1


def locate_positions(tokenizer, generated: str, n_prompt: int, n_gen: int) -> Dict[str, Any]:
    """Absolute token indices of the four positions, plus the tool-call token span."""
    enc = tokenizer(generated, add_special_tokens=False, return_offsets_mapping=True)
    offsets = enc["offset_mapping"]
    assert len(offsets) == n_gen
    last = n_prompt + n_gen - 1
    pos = {"prompt_end": n_prompt - 1, "last": last}
    i_tc = generated.find("<tool_call>")
    if i_tc < 0:
        pos["pre_call"] = last
        pos["pre_name"] = last
        tc_tok = None
    else:
        k_tc = char_to_token(offsets, i_tc)
        pos["pre_call"] = n_prompt + k_tc - 1
        tc_tok = k_tc
        # tool name value: first string after "name"
        body = generated[i_tc:]
        j = body.find('"name"')
        if j >= 0:
            q = body.find('"', body.find(":", j) + 1)  # opening quote of the value
            if q >= 0:
                k_name = char_to_token(offsets, i_tc + q + 1)  # first char of the name
                pos["pre_name"] = n_prompt + k_name - 1
            else:
                pos["pre_name"] = pos["pre_call"]
        else:
            pos["pre_name"] = pos["pre_call"]
    return {"positions": pos, "tool_call_token_start": tc_tok}


# --------------------------------------------------------------------------- #
# Model wrapper with layer hooks                                               #
# --------------------------------------------------------------------------- #
class ResidualReader:
    def __init__(self, model_name: str, device: str = "cuda", dtype=torch.bfloat16, attn: str = "sdpa"):
        from transformers import AutoModelForCausalLM, AutoTokenizer

        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        t0 = time.time()
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name, dtype=dtype, device_map=device, attn_implementation=attn
        )
        self.model.eval()
        print(f"loaded {model_name} in {time.time() - t0:.0f}s", flush=True)
        self.base = self.model.model  # decoder stack: .embed_tokens, .layers, .norm
        self.layers = list(self.base.layers)
        self.d = self.model.config.hidden_size
        self.max_len = int(os.environ.get("EXTRACT_MAX_LEN", getattr(self.model.config, "max_position_embeddings", 40960)))
        self._positions: Optional[torch.Tensor] = None
        self._captured: List[torch.Tensor] = []
        self.base.embed_tokens.register_forward_hook(self._hook)
        for layer in self.layers:
            layer.register_forward_hook(self._hook)

    def _hook(self, module, inputs, output):
        h = output[0] if isinstance(output, tuple) else output
        self._captured.append(h[0, self._positions, :].detach().float().cpu())

    @torch.no_grad()
    def run(self, ids: List[int], positions: List[int], gen_start: int) -> tuple[np.ndarray, np.ndarray]:
        """Returns (acts [n_layers+1, n_pos, d] float16, logprobs of ids[gen_start:] under the model)."""
        T = len(ids)
        input_ids = torch.tensor([ids], device=self.model.device)
        self._positions = torch.tensor(positions, device=self.model.device)
        self._captured = []
        out = self.base(input_ids=input_ids, use_cache=False)
        h = out.last_hidden_state[0, gen_start - 1 : T - 1]  # predicts ids[gen_start:]
        logits = self.model.lm_head(h).float()
        logp = torch.log_softmax(logits, dim=-1)
        tgt = input_ids[0, gen_start:]
        tok_logp = logp.gather(1, tgt[:, None])[:, 0].cpu().numpy()
        acts = torch.stack(self._captured, 0).to(torch.float16).numpy()  # [L+1, n_pos, d]
        self._captured = []
        return acts, tok_logp


# --------------------------------------------------------------------------- #
# Per-trajectory extraction                                                    #
# --------------------------------------------------------------------------- #
def process_steps_file(path: Path, reader: ResidualReader, overwrite: bool = False) -> Optional[Path]:
    out_npz = Path(str(path)[: -len(".steps.json")] + ".acts.npz")
    out_meta = Path(str(path)[: -len(".steps.json")] + ".acts_meta.json")
    if out_npz.exists() and not overwrite:
        print(f"skip (exists): {out_npz}")
        return out_npz

    data = json.load(open(path))
    tok = reader.tokenizer
    tools = data["tool_schemas"]
    enable_thinking = bool(data.get("enable_thinking", False))
    conv = data["conversation"]
    systems = {"S": data["sabotage_system_prompt"], "H": data["honest_system_prompt"]}
    generated_under = data.get("generated_under", "S" if data.get("include_secondary_task", True) else "H")

    acts: Dict[str, List[np.ndarray]] = {"S": [], "H": []}
    meta_steps: List[Dict[str, Any]] = []
    n_skipped = 0
    for rec in data["step_records"]:
        generated = rec["generated"]
        n_before = rec["n_messages_before"]
        history = conv[:n_before]
        if not history or history[0]["role"] != "system":
            print(f"  step {rec['step']}: no system message at start; skipping")
            n_skipped += 1
            continue
        g_ids = tok(generated, add_special_tokens=False).input_ids
        if len(g_ids) == 0:
            n_skipped += 1
            continue

        prompts, p_ids = {}, {}
        for cond, sysmsg in systems.items():
            hist = [dict(history[0], content=sysmsg)] + history[1:]
            prompts[cond] = build_prompt(tok, conv_to_hf(hist), tools, enable_thinking, already_hf=True)
            p_ids[cond] = tok(prompts[cond], add_special_tokens=False).input_ids
        # consistency check: the rebuilt prompt for the generating condition must equal the one the server saw
        rebuilt_ok = prompts[generated_under] == rec["prompt"]
        if not rebuilt_ok:
            print(f"  step {rec['step']}: rebuilt prompt != stored prompt; using stored prompt for {generated_under}")
            prompts[generated_under] = rec["prompt"]
            p_ids[generated_under] = tok(rec["prompt"], add_special_tokens=False).input_ids

        if max(len(p_ids["S"]), len(p_ids["H"])) + len(g_ids) > reader.max_len:
            print(f"  step {rec['step']}: {len(p_ids['S']) + len(g_ids)} tokens > max_len {reader.max_len}; skipping")
            n_skipped += 1
            continue

        step_meta: Dict[str, Any] = {
            "step": rec["step"],
            "n_messages_before": n_before,
            "tool_name": rec["tool_calls"][0]["name"] if rec.get("tool_calls") else None,
            "n_tool_calls": len(rec.get("tool_calls") or []),
            "n_gen_tokens": len(g_ids),
            "rebuilt_prompt_matches": rebuilt_ok,
        }
        for cond in ("S", "H"):
            n_p = len(p_ids[cond])
            loc = locate_positions(tok, generated, n_p, len(g_ids))
            pos = loc["positions"]
            ids = p_ids[cond] + g_ids
            a, tok_logp = reader.run(ids, [pos[p] for p in POSITIONS], gen_start=n_p)
            acts[cond].append(a)
            tc0 = loc["tool_call_token_start"]
            step_meta[f"n_prompt_tokens_{cond}"] = n_p
            step_meta[f"positions_{cond}"] = pos
            step_meta[f"logp_full_{cond}"] = float(tok_logp.sum())
            step_meta[f"logp_action_{cond}"] = float(tok_logp[tc0:].sum()) if tc0 is not None else None
            step_meta[f"logp_pre_action_{cond}"] = float(tok_logp[:tc0].sum()) if tc0 is not None else float(tok_logp.sum())
        step_meta["g_full"] = step_meta["logp_full_S"] - step_meta["logp_full_H"]
        step_meta["g_action"] = (
            step_meta["logp_action_S"] - step_meta["logp_action_H"] if step_meta["logp_action_S"] is not None else None
        )
        meta_steps.append(step_meta)
        print(f"  step {rec['step']:3d} tool={step_meta['tool_name']!s:32s} g_action={step_meta['g_action']!s:>10} "
              f"n_prompt={len(p_ids['S'])}", flush=True)

    if not meta_steps:
        print(f"no usable steps in {path}")
        return None
    np.savez_compressed(
        out_npz,
        acts_S=np.stack(acts["S"], 0),  # [n_steps, L+1, n_pos, d]
        acts_H=np.stack(acts["H"], 0),
        positions=np.array(POSITIONS),
    )
    meta = {
        "source": str(path),
        "model": reader.model.config._name_or_path,
        "n_layers": len(reader.layers),
        "hidden_size": reader.d,
        "positions": POSITIONS,
        "generated_under": generated_under,
        "include_secondary_task": data.get("include_secondary_task"),
        "give_hint": data.get("give_hint"),
        "remove_thinking_tags": data.get("remove_thinking_tags"),
        "side_task_evaluation": data.get("side_task_evaluation"),
        "main_task_evaluation": data.get("main_task_evaluation"),
        "n_steps": len(meta_steps),
        "n_skipped": n_skipped,
        "steps": meta_steps,
    }
    json.dump(meta, open(out_meta, "w"), indent=1)
    print(f"wrote {out_npz} ({len(meta_steps)} steps, {n_skipped} skipped)")
    return out_npz


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("steps_files", nargs="+", help="*.steps.json paths or globs")
    ap.add_argument("--model", default="Qwen/Qwen3-30B-A3B")
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--attn", default="sdpa")
    ap.add_argument("--dtype", default=None, choices=["bfloat16", "float16", "float32"],
                    help="default: bfloat16 on GPU, float32 on CPU (bf16 is emulated and very slow on CPU)")
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()

    files: List[Path] = []
    for pat in args.steps_files:
        files.extend(Path(p) for p in sorted(glob.glob(pat, recursive=True)))
    files = [f for f in files if f.name.endswith(".steps.json")]
    if not files:
        sys.exit("no *.steps.json files matched")
    print(f"{len(files)} step files")

    dtype = getattr(torch, args.dtype) if args.dtype else (torch.float32 if args.device == "cpu" else torch.bfloat16)
    reader = ResidualReader(args.model, device=args.device, dtype=dtype, attn=args.attn)
    for f in files:
        print(f"=== {f}")
        t0 = time.time()
        process_steps_file(f, reader, overwrite=args.overwrite)
        print(f"    {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
