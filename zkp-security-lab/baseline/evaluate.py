#!/usr/bin/env python3
"""
evaluate.py
Compare detection results against ground truth.
Computes TP / FP / FN / TN, Precision, Recall, F1.
"""

import json
from pathlib import Path
from rules_v0_2 import analyze  # 复用 detect.py 的 analyze 函数


# ---------- 人工标注的 Ground Truth ----------
# vulnerable = 有安全漏洞（under / over / public-input binding）
# safe       = 无安全漏洞（包括 dead variable 这种 ambiguous 情况）
GROUND_TRUTH = {
    # Safe
    "safe_selector":        "safe",
    "safe_range_check":     "safe",
    "safe_public_binding":  "safe",

    # Under
    "under_selector":       "vulnerable",
    "tmp_unconstrained":    "vulnerable",
    "under_range":          "vulnerable",
    "unbound_public":       "vulnerable",

    # Over
    "over_range_check":     "vulnerable",
    "over_equality":        "vulnerable",

    # Ambiguous
    "ambiguous_dead_var":   "safe",     # dead variable，不是漏洞
    "ambiguous_domain":     "safe",
}


def tool_predict(findings) -> str:
    """If any high/critical finding -> vulnerable."""
    for f in findings:
        if f.severity in ("high", "critical"):
            return "vulnerable"
    return "safe"


def main():
    circuits_dir = Path(__file__).parent.parent / "circuits"
    json_files = sorted(circuits_dir.rglob("*.json"))

    results = []  # (circuit_id, truth, prediction, outcome)

    for jf in json_files:
        with open(jf, "r", encoding="utf-8") as f:
            circuit = json.load(f)
        cid = circuit["circuit_id"]

        findings = analyze(circuit)
        pred = tool_predict(findings)

        if cid not in GROUND_TRUTH:
            print(f"WARNING: {cid} has no ground truth, skipping.")
            continue

        truth = GROUND_TRUTH[cid]

        if truth == "vulnerable" and pred == "vulnerable":
            outcome = "TP"
        elif truth == "safe" and pred == "vulnerable":
            outcome = "FP"
        elif truth == "vulnerable" and pred == "safe":
            outcome = "FN"
        else:
            outcome = "TN"

        results.append((cid, truth, pred, outcome))

    # ---------- Print per-circuit table ----------
    print("=" * 80)
    print(f"{'Circuit':<25} {'Truth':<12} {'Pred':<12} {'Outcome'}")
    print("-" * 80)
    for cid, truth, pred, outcome in results:
        print(f"{cid:<25} {truth:<12} {pred:<12} {outcome}")

    # ---------- Confusion matrix ----------
    tp = sum(1 for r in results if r[3] == "TP")
    fp = sum(1 for r in results if r[3] == "FP")
    fn = sum(1 for r in results if r[3] == "FN")
    tn = sum(1 for r in results if r[3] == "TN")

    print()
    print("=" * 80)
    print("CONFUSION MATRIX")
    print("=" * 80)
    print(f"{'':<20} {'Pred: vulnerable':<20} {'Pred: safe'}")
    print(f"{'Truth: vulnerable':<20} {tp:<20} {fn}")
    print(f"{'Truth: safe':<20} {fp:<20} {tn}")

    # ---------- Metrics ----------
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall    = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1        = (2 * precision * recall / (precision + recall)
                 if (precision + recall) > 0 else 0.0)

    print()
    print("=" * 80)
    print("METRICS")
    print("=" * 80)
    print(f"TP = {tp}")
    print(f"FP = {fp}")
    print(f"FN = {fn}")
    print(f"TN = {tn}")
    print(f"Precision = {precision:.3f}")
    print(f"Recall    = {recall:.3f}")
    print(f"F1        = {f1:.3f}")

    # ---------- Failure case list ----------
    print()
    print("=" * 80)
    print("FAILURE CASES")
    print("=" * 80)
    for cid, truth, pred, outcome in results:
        if outcome in ("FP", "FN"):
            print(f"  [{outcome}] {cid}: truth={truth}, pred={pred}")


if __name__ == "__main__":
    main()