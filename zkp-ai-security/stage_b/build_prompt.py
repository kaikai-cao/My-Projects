import json
from pathlib import Path

TEMPLATE = Path("stage_b/prompt_template.md").read_text(encoding="utf-8")
STAGE_A_DIR = Path("results/stage_a")
OUT_DIR = Path("results/stage_b")
OUT_DIR.mkdir(parents=True, exist_ok=True)


def build(stage_a_file: Path) -> Path:
    data = json.loads(stage_a_file.read_text(encoding="utf-8"))
    prompt = (TEMPLATE
              .replace("{filename}", data["file"])
              .replace("{source}", data["source"])
              .replace("{stage_a_json}", json.dumps(
                  {k: v for k, v in data.items() if k != "source"}, indent=2, ensure_ascii=False))
              .replace("{intended_semantics}", data["intended_semantics"]))
    out = OUT_DIR / (stage_a_file.stem + ".prompt.txt")
    out.write_text(prompt, encoding="utf-8")
    return out


def main():
    for f in sorted(STAGE_A_DIR.glob("*.json")):
        out = build(f)
        print(f"[Stage B] {f.name} -> {out}  ({out.stat().st_size} bytes)")


if __name__ == "__main__":
    main()