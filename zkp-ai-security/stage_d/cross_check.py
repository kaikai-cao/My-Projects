import json
from pathlib import Path

STAGE_A = Path("results/stage_a")
STAGE_C = Path("results/stage_c")
OUT_DIR = Path("results/stage_d")
OUT_DIR.mkdir(parents=True, exist_ok=True)


def rule_verdict(findings):
    return "unsafe" if findings else "safe"


def main():
    rows = []
    for a_file in sorted(STAGE_A.glob("*.json")):
        stem = a_file.stem
        a = json.loads(a_file.read_text(encoding="utf-8"))

        c_file = STAGE_C / (stem + ".llm.json")
        if not c_file.exists():
            print(f"[Stage D] skip {stem}: no LLM response")
            continue
        c = json.loads(c_file.read_text(encoding="utf-8"))

        rule_v = rule_verdict(a["rule_findings"])
        llm_v = c.get("verdict", "error")

        rows.append({
            "file": a["file"],
            "rule_verdict": rule_v,
            "rule_findings": a["rule_findings"],
            "llm_verdict": llm_v,
            "llm_vulns": c.get("vulnerabilities", []),
            "llm_confidence": c.get("confidence"),
            "agree": rule_v == llm_v,
        })

    out = OUT_DIR / "cross_check.json"
    out.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")

    print("\n=== Cross Check ===")
    for r in rows:
        mark = "OK" if r["agree"] else "XX"
        print(f" [{mark}] {r['file']:30s} rule={r['rule_verdict']:8s} llm={r['llm_verdict']:8s} conf={r['llm_confidence']}")
    print(f"\nSaved -> {out}")


if __name__ == "__main__":
    main()