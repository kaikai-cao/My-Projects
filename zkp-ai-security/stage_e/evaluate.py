import json
from pathlib import Path

GROUND_TRUTH = {
    "safe_square.circom": "safe",
    "unsafe_square.circom": "unsafe",
    "boundary_square.circom": "unsafe",
}

CROSS = Path("results/stage_d/cross_check.json")
OUT = Path("results/stage_e")
OUT.mkdir(parents=True, exist_ok=True)


def main():
    rows = json.loads(CROSS.read_text(encoding="utf-8"))

    rule_correct = 0
    llm_correct = 0
    llm_conf = []

    for r in rows:
        truth = GROUND_TRUTH[r["file"]]
        if r["rule_verdict"] == truth:
            rule_correct += 1
        if r["llm_verdict"] == truth:
            llm_correct += 1
        if r["llm_confidence"] is not None:
            llm_conf.append(r["llm_confidence"])

    n = len(rows)
    summary = {
        "n_cases": n,
        "rule_accuracy": rule_correct / n if n else 0,
        "llm_accuracy": llm_correct / n if n else 0,
        "avg_llm_confidence": sum(llm_conf) / len(llm_conf) if llm_conf else None,
        "disagreements": [r for r in rows if not r["agree"]],
    }

    (OUT / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    print("\n=== Stage E: Summary ===")
    print(f" Cases          : {summary['n_cases']}")
    print(f" Rule accuracy  : {summary['rule_accuracy']:.2%}")
    print(f" LLM  accuracy  : {summary['llm_accuracy']:.2%}")
    print(f" Avg LLM conf.  : {summary['avg_llm_confidence']}")
    print(f" Disagreements  : {len(summary['disagreements'])}")
    print(f"\nSaved -> {OUT / 'summary.json'}")


if __name__ == "__main__":
    main()