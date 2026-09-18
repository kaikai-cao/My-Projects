#!/usr/bin/env python3
"""
llm_experiment.py
Day 6: AI + Static Analysis 对照实验（全自动版）

用法：
  python llm_experiment.py run
       → 自动生成 prompt，调用 API，保存回答，算指标

环境变量（.env）：
  OPENAI_API_KEY / OPENAI_BASE_URL / OPENAI_MODEL
  或
  ANTHROPIC_API_KEY / ANTHROPIC_MODEL
"""

import json
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "baseline"))
from rules_v0_2 import analyze, extract_vars, parse_constraint

# ---------- 配置 ----------
ROOT = Path(__file__).parent.parent
CIRCUITS_DIR = ROOT / "circuits"
PROMPTS_DIR = ROOT / "llm" / "prompts"
RESULTS_DIR = ROOT / "llm" / "raw_outputs"

TEST_CIRCUITS = [
    # Safe
    "safe_selector",
    "safe_range_check",
    "safe_public_binding",
    # Under
    "under_selector",
    "tmp_unconstrained",
    "under_range",
    "unbound_public",
    # Over
    "over_range_check",
    "over_equality",
    # Ambiguous
    "ambiguous_dead_var",
    "ambiguous_domain",
]

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
    "ambiguous_dead_var":   "safe",
    "ambiguous_domain":     "safe",
}

load_dotenv(Path(__file__).parent.parent / ".env")


# ---------- 结构化摘要 ----------
def build_structured_summary(circuit: dict) -> str:
    lines = []
    lines.append(f"- Inputs: {circuit.get('inputs', [])}")
    lines.append(f"- Public Inputs: {circuit.get('public_inputs', [])}")
    lines.append(f"- Outputs: {circuit.get('outputs', [])}")
    lines.append(f"- Internal Signals: {circuit.get('internals', [])}")
    lines.append(f"- Assignments: {circuit.get('assignments', {})}")
    lines.append(f"- Constraints: {circuit.get('constraints', [])}")

    constrained_vars = set()
    for c in circuit.get("constraints", []):
        constrained_vars |= parse_constraint(c)
    lines.append(f"- Variables appearing in constraints: {sorted(constrained_vars)}")

    unbound = []
    for var, expr in circuit.get("assignments", {}).items():
        rhs_vars = extract_vars(expr)
        bound = False
        for c in circuit.get("constraints", []):
            c_vars = parse_constraint(c)
            if var in c_vars and (rhs_vars & c_vars):
                bound = True
                break
        if not bound:
            unbound.append(var)
    lines.append(f"- Variables with assignments but NOT bound by constraints: {unbound}")

    selectors = []
    for var, expr in circuit.get("assignments", {}).items():
        for candidate in extract_vars(expr):
            if f"(1-{candidate})" in expr.replace(" ", ""):
                selectors.append(candidate)
    lines.append(f"- Potential selector patterns: {selectors}")

    return "\n".join(lines)


# ---------- LLM 调用 ----------
def call_openai(prompt: str) -> str:
    from openai import OpenAI
    client = OpenAI(
        api_key=os.environ["OPENAI_API_KEY"],
        base_url=os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"),
    )
    model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )
    return resp.choices[0].message.content


def call_anthropic(prompt: str) -> str:
    from anthropic import Anthropic
    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    model = os.environ.get("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
    resp = client.messages.create(
        model=model,
        max_tokens=2000,
        temperature=0,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.content[0].text


def call_llm(prompt: str) -> str:
    if os.environ.get("OPENAI_API_KEY"):
        return call_openai(prompt)
    if os.environ.get("ANTHROPIC_API_KEY"):
        return call_anthropic(prompt)
    raise RuntimeError("No API key found. Set OPENAI_API_KEY or ANTHROPIC_API_KEY in .env")


# ---------- 解析 LLM JSON ----------
def parse_llm_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines)
    # 找第一个 { 和最后一个 }
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1:
        text = text[start:end + 1]
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        print(f"  [WARN] JSON parse failed: {e}")
        return {}


def llm_predict(resp: dict) -> str:
    if not resp:
        return "error"
    vtype = resp.get("vulnerability_type", "none")
    conf = resp.get("confidence", "low")
    if vtype in ("under-constrained", "over-constrained") and conf in ("high", "medium"):
        return "vulnerable"
    return "safe"


# ---------- 主流程 ----------
def run():
    RESULTS_DIR.mkdir(exist_ok=True)
    prompt_v1_tmpl = (PROMPTS_DIR / "prompt_v1.txt").read_text(encoding="utf-8")
    prompt_v2_tmpl = (PROMPTS_DIR / "prompt_v2.txt").read_text(encoding="utf-8")

    for cid in TEST_CIRCUITS:
        json_path = next(CIRCUITS_DIR.rglob(f"{cid}.json"))
        circom_path = next(CIRCUITS_DIR.rglob(f"{cid}.circom"))

        if not json_path.exists() or not circom_path.exists():
            print(f"[SKIP] {cid}: missing .json or .circom")
            continue

        circuit = json.loads(json_path.read_text(encoding="utf-8"))
        circom_code = circom_path.read_text(encoding="utf-8")
        summary = build_structured_summary(circuit)

        p1 = prompt_v1_tmpl.replace("{{CIRCUIT_CODE}}", circom_code)
        p2 = (prompt_v2_tmpl
              .replace("{{STRUCTURED_SUMMARY}}", summary)
              .replace("{{CIRCUIT_CODE}}", circom_code))

        (RESULTS_DIR / f"{cid}_v1_prompt.txt").write_text(p1, encoding="utf-8")
        (RESULTS_DIR / f"{cid}_v2_prompt.txt").write_text(p2, encoding="utf-8")

        for version, prompt in [("v1", p1), ("v2", p2)]:
            resp_path = RESULTS_DIR / f"{cid}_{version}_response.json"
            if resp_path.exists():
                print(f"[CACHE] {cid} {version}")
                continue
            print(f"[CALL]  {cid} {version} ...", end=" ", flush=True)
            try:
                raw = call_llm(prompt)
                parsed = parse_llm_json(raw)
                resp_path.write_text(
                    json.dumps(parsed, indent=2, ensure_ascii=False),
                    encoding="utf-8",
                )
                print(f"OK  type={parsed.get('vulnerability_type', '?')}  "
                      f"var={parsed.get('variable', '?')}  "
                      f"conf={parsed.get('confidence', '?')}")
            except Exception as e:
                print(f"FAIL: {e}")
                resp_path.write_text(
                    json.dumps({"error": str(e)}, indent=2),
                    encoding="utf-8",
                )
            time.sleep(1)  # 避免 rate limit

    print()
    print("All responses saved to llm_results/")
    print()
    evaluate()


# ---------- 评估 ----------
def evaluate():
    rows = []
    for cid in TEST_CIRCUITS:
        truth = GROUND_TRUTH.get(cid, "unknown")

        circuit = json.loads(next(CIRCUITS_DIR.rglob(f"{cid}.json")).read_text(encoding="utf-8"))
        findings = analyze(circuit)
        rule_pred = "vulnerable" if any(
            f.severity in ("high", "critical") for f in findings
        ) else "safe"

        p1 = RESULTS_DIR / f"{cid}_v1_response.json"
        v1_pred = llm_predict(parse_llm_json(p1.read_text(encoding="utf-8"))) if p1.exists() else "missing"

        p2 = RESULTS_DIR / f"{cid}_v2_response.json"
        v2_pred = llm_predict(parse_llm_json(p2.read_text(encoding="utf-8"))) if p2.exists() else "missing"

        rows.append((cid, truth, rule_pred, v1_pred, v2_pred))

    print("=" * 100)
    print(f"{'Circuit':<22} {'Truth':<12} {'Rule':<12} {'LLM-v1':<12} {'LLM-v2':<12}")
    print("-" * 100)
    for cid, truth, rule, v1, v2 in rows:
        print(f"{cid:<22} {truth:<12} {rule:<12} {v1:<12} {v2:<12}")

    def metrics(preds, truths):
        tp = fp = fn = tn = 0
        for t, p in zip(truths, preds):
            if p in ("missing", "error"):
                continue
            if t == "vulnerable" and p == "vulnerable":
                tp += 1
            elif t == "safe" and p == "vulnerable":
                fp += 1
            elif t == "vulnerable" and p == "safe":
                fn += 1
            else:
                tn += 1
        prec = tp / (tp + fp) if (tp + fp) else 0.0
        rec = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
        return tp, fp, fn, tn, prec, rec, f1

    truths = [r[1] for r in rows]
    for method, idx in [("Rule", 2), ("LLM-v1", 3), ("LLM-v2", 4)]:
        preds = [r[idx] for r in rows]
        tp, fp, fn, tn, p, r_, f1 = metrics(preds, truths)
        print()
        print(f"--- {method} ---")
        print(f"  TP={tp}  FP={fp}  FN={fn}  TN={tn}")
        print(f"  Precision={p:.3f}  Recall={r_:.3f}  F1={f1:.3f}")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "run"
    if cmd == "run":
        run()
    elif cmd == "evaluate":
        evaluate()
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)