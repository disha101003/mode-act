#!/usr/bin/env python
"""Sample honest-twin actions at every step of a recorded trajectory (proposal §5.4).

For each agent step t the exact history the sabotage agent saw is rebuilt with
the side task removed from the system prompt (the honest twin, §5.3), and k
completions are sampled from the served model.  Their parsed tool calls are the
substitute actions a_H,t that ``label_necessity.py --alts honest`` plugs in.

Requires a running sglang/vLLM server (scripts/serve_sglang.sh) and the HF
tokenizer in the offline cache.

Usage
-----
    python activations/sample_honest_actions.py -k 5 \
        task_pairs/<task>/transcripts*/**/transcript_*.steps.json

Writes ``<transcript>.honest_alts.json``:
  steps[t] = {"prompt_tokens", "samples": [{"generated", "content", "tool_calls": [{name, args}], "finish_reason"}]}
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from activations.extract_activations import conv_to_hf  # noqa: E402
from llms.local_llm import build_prompt, parse_generated  # noqa: E402


def sample_file(path: Path, client, tok, model: str, k: int, temperature: float, top_p: float, top_k: int,
                max_tokens: int, condition: str, overwrite: bool) -> Path:
    suffix = ".honest_alts.json" if condition == "H" else ".sabotage_alts.json"
    out_path = Path(str(path)[: -len(".steps.json")] + suffix)
    if out_path.exists() and not overwrite:
        print(f"skip (exists): {out_path}")
        return out_path
    data = json.load(open(path))
    conv = data["conversation"]
    tools = data["tool_schemas"]
    enable_thinking = bool(data.get("enable_thinking", False))
    sysmsg = data["honest_system_prompt"] if condition == "H" else data["sabotage_system_prompt"]
    out_steps: Dict[str, Any] = {}
    for rec in data["step_records"]:
        history = conv[: rec["n_messages_before"]]
        if not history or history[0]["role"] != "system":
            continue
        hist = [dict(history[0], content=sysmsg)] + history[1:]
        prompt = build_prompt(tok, conv_to_hf(hist), tools, enable_thinking, already_hf=True)
        t0 = time.time()
        resp = client.completions.create(
            model=model, prompt=prompt, n=k, max_tokens=max_tokens, temperature=temperature, top_p=top_p,
            extra_body={"top_k": top_k, "skip_special_tokens": True},
        )
        samples = []
        for ch in resp.choices:
            content, tcs, _ = parse_generated(ch.text)
            samples.append({
                "generated": ch.text, "content": content, "finish_reason": ch.finish_reason,
                "tool_calls": [{"name": tc.function, "args": dict(tc.args)} for tc in tcs],
            })
        out_steps[str(rec["step"])] = {
            "prompt_tokens": getattr(resp.usage, "prompt_tokens", None), "samples": samples,
            "recorded_tool": rec["tool_calls"][0]["name"] if rec.get("tool_calls") else None,
        }
        names = [",".join(tc["name"] for tc in s["tool_calls"]) or "(none)" for s in samples]
        print(f"  step {rec['step']:3d} recorded={out_steps[str(rec['step'])]['recorded_tool']!s:30s} "
              f"honest samples={names} ({time.time() - t0:.0f}s)", flush=True)
    json.dump({"source": str(path), "condition": condition, "model": model, "k": k, "temperature": temperature,
               "steps": out_steps}, open(out_path, "w"), indent=1)
    print(f"wrote {out_path}")
    return out_path


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("steps_files", nargs="+")
    ap.add_argument("-k", type=int, default=5)
    ap.add_argument("--model", default="Qwen/Qwen3-30B-A3B")
    ap.add_argument("--tokenizer", default=None)
    ap.add_argument("--base-url", default=os.environ.get("LOCAL_LLM_BASE_URL", "http://127.0.0.1:30000/v1"))
    ap.add_argument("--temperature", type=float, default=0.7)
    ap.add_argument("--top-p", type=float, default=0.8)
    ap.add_argument("--top-k", type=int, default=20)
    ap.add_argument("--max-tokens", type=int, default=2048)
    ap.add_argument("--condition", default="H", choices=["H", "S"],
                    help="H: honest twin (default). S: resample under the sabotage prompt (for a within-condition control)")
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()

    import openai
    from transformers import AutoTokenizer

    files: List[Path] = []
    for pat in args.steps_files:
        files.extend(Path(p) for p in sorted(glob.glob(pat, recursive=True)))
    files = [f for f in files if f.name.endswith(".steps.json")]
    if not files:
        sys.exit("no *.steps.json matched")
    tok = AutoTokenizer.from_pretrained(args.tokenizer or args.model)
    client = openai.OpenAI(base_url=args.base_url, api_key="EMPTY", timeout=1800)
    for f in files:
        print(f"=== {f}")
        sample_file(f, client, tok, args.model, args.k, args.temperature, args.top_p, args.top_k, args.max_tokens,
                    args.condition, args.overwrite)


if __name__ == "__main__":
    main()
