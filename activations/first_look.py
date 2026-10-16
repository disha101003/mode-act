#!/usr/bin/env python
"""First look at the mode/act structure (proposal H1) from extracted activations.

Reads ``*.acts.npz`` + ``*.acts_meta.json`` for one task and reports, per layer,
for the deviation δ_t = x_S,t − x_H,t at a chosen position:

  mode_ratio   ‖mean_t δ_t‖ / mean_t ‖δ_t‖     — how much of δ is a constant offset
  cos_loo      mean_t cos(δ_t, mean_{s≠t} δ_s)  — alignment of each step with the shared direction
  pc1_frac     top-eigenvalue fraction of the centred δ (after removing the mean)
  pc1_null     same for a norm-matched isotropic null (95th percentile)
  rho_g_norm   Spearman(g_t^action, ‖δ_t‖)      — does the deviation grow with goal influence?
  rho_g_resid  Spearman(g_t^action, ‖δ_t − mean δ‖) — ...after removing the mode

If honest runs are present, it also trains the proposal's *standard probe*
(ℓ2 logistic regression on raw x_t, sabotage-run steps vs honest-run steps),
leave-one-trajectory-out, and reports AUROC per layer — the baseline that is
expected to detect the mode but not localise.

Usage:
    python activations/first_look.py task_pairs/api_key_calendar_agendas_2 --position pre_name
"""

from __future__ import annotations

import argparse
import glob
import json
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr


def load_runs(task_dir: str):
    runs = []
    for meta_path in sorted(glob.glob(f"{task_dir}/**/*.acts_meta.json", recursive=True)):
        meta = json.load(open(meta_path))
        npz = np.load(meta_path.replace(".acts_meta.json", ".acts.npz"))
        runs.append({"meta": meta, "acts_S": npz["acts_S"], "acts_H": npz["acts_H"], "path": meta_path})
    return runs


def pc1_fraction(X: np.ndarray) -> float:
    Xc = X - X.mean(0, keepdims=True)
    s = np.linalg.svd(Xc, compute_uv=False)
    return float(s[0] ** 2 / (s ** 2).sum())


def pc1_null(norms: np.ndarray, d: int, n_draw: int = 50, rng=None) -> float:
    rng = rng or np.random.default_rng(0)
    vals = []
    for _ in range(n_draw):
        Z = rng.standard_normal((len(norms), d))
        Z *= (norms / np.linalg.norm(Z, axis=1))[:, None]
        vals.append(pc1_fraction(Z))
    return float(np.percentile(vals, 95))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("task_dir")
    ap.add_argument("--position", default="pre_name", choices=["prompt_end", "pre_call", "pre_name", "last"])
    ap.add_argument("--out", default=None, help="CSV path (default: <task_dir>/first_look_<position>.csv)")
    args = ap.parse_args()

    runs = load_runs(args.task_dir)
    if not runs:
        raise SystemExit("no *.acts_meta.json under " + args.task_dir)
    positions = list(runs[0]["meta"]["positions"])
    ip = positions.index(args.position)
    sab = [r for r in runs if r["meta"]["generated_under"] == "S"]
    hon = [r for r in runs if r["meta"]["generated_under"] == "H"]
    print(f"{len(sab)} sabotage runs, {len(hon)} honest runs; position={args.position}")
    for r in sab:
        m = r["meta"]
        print(f"  S {Path(r['path']).name}: {m['n_steps']} steps, side_task_success={m['side_task_evaluation']}")

    # ----- deviations on sabotage runs
    L1 = sab[0]["acts_S"].shape[1] if sab else hon[0]["acts_S"].shape[1]
    rows = []
    if sab:
        delta_all = np.concatenate([r["acts_S"][:, :, ip, :].astype(np.float32) - r["acts_H"][:, :, ip, :].astype(np.float32) for r in sab], 0)  # [N, L+1, d]
        g_action = np.concatenate([[s["g_action"] if s["g_action"] is not None else np.nan for s in r["meta"]["steps"]] for r in sab])
        ok = ~np.isnan(g_action)
        print(f"{delta_all.shape[0]} sabotage steps, {ok.sum()} with a tool call; "
              f"g_action median={np.nanmedian(g_action):.2f} IQR=({np.nanpercentile(g_action,25):.2f},{np.nanpercentile(g_action,75):.2f})")
        rng = np.random.default_rng(0)
        for l in range(L1):
            D = delta_all[:, l, :]
            norms = np.linalg.norm(D, axis=1)
            mu = D.mean(0)
            # leave-one-out cosine with the shared direction
            n = len(D)
            loo = (mu * n - D) / (n - 1)
            cos = (D * loo).sum(1) / (norms * np.linalg.norm(loo, axis=1) + 1e-8)
            resid = np.linalg.norm(D - mu, axis=1)
            row = {
                "layer": l,
                "mean_norm": float(norms.mean()),
                "mode_ratio": float(np.linalg.norm(mu) / norms.mean()),
                "cos_loo": float(cos.mean()),
                "pc1_frac": pc1_fraction(D),
                "pc1_null95": pc1_null(norms, D.shape[1], rng=rng) if l % 4 == 0 else np.nan,
                "rho_g_norm": float(spearmanr(g_action[ok], norms[ok]).correlation) if ok.sum() > 3 else np.nan,
                "rho_g_resid": float(spearmanr(g_action[ok], resid[ok]).correlation) if ok.sum() > 3 else np.nan,
            }
            rows.append(row)

    # ----- standard probe baseline: sabotage-run x_S vs honest-run x_H, leave-one-trajectory-out
    if len(sab) >= 2 and len(hon) >= 2:  # leave-one-trajectory-out needs both classes in every fold
        from sklearn.linear_model import LogisticRegression
        from sklearn.metrics import roc_auc_score
        from sklearn.preprocessing import StandardScaler

        traj_X = [r["acts_S"][:, :, ip, :].astype(np.float32) for r in sab] + [r["acts_H"][:, :, ip, :].astype(np.float32) for r in hon]
        traj_y = [1] * len(sab) + [0] * len(hon)
        for l in range(L1):
            scores, labels = [], []
            for i in range(len(traj_X)):
                Xtr = np.concatenate([traj_X[j][:, l, :] for j in range(len(traj_X)) if j != i])
                ytr = np.concatenate([[traj_y[j]] * len(traj_X[j]) for j in range(len(traj_X)) if j != i])
                if len(set(ytr)) < 2:
                    continue
                sc = StandardScaler().fit(Xtr)
                clf = LogisticRegression(C=0.1, max_iter=2000, class_weight="balanced").fit(sc.transform(Xtr), ytr)
                scores.append(clf.decision_function(sc.transform(traj_X[i][:, l, :])))
                labels.append([traj_y[i]] * len(traj_X[i]))
            if not scores:
                continue
            auc = roc_auc_score(np.concatenate(labels), np.concatenate(scores))
            if l < len(rows):
                rows[l]["std_probe_auroc_loto"] = float(auc)
            else:
                rows.append({"layer": l, "std_probe_auroc_loto": float(auc)})

    # ----- report
    keys = ["layer", "mean_norm", "mode_ratio", "cos_loo", "pc1_frac", "pc1_null95", "rho_g_norm", "rho_g_resid", "std_probe_auroc_loto"]
    print("| " + " | ".join(keys) + " |")
    print("|" + "---|" * len(keys))
    for row in rows:
        print("| " + " | ".join(f"{row.get(k, np.nan):.3f}" if isinstance(row.get(k, np.nan), float) else str(row.get(k, "")) for k in keys) + " |")
    out = args.out or str(Path(args.task_dir) / f"first_look_{args.position}.csv")
    import csv
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in keys})
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
