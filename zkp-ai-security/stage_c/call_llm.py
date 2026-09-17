import os
import json
import time
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.environ["OPENAI_API_KEY"],
    base_url=os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"),
)
MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

PROMPT_DIR = Path("results/stage_b")
OUT_DIR = Path("results/stage_c")
OUT_DIR.mkdir(parents=True, exist_ok=True)


def clean_json(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text
        if text.endswith("```"):
            text = text[:-3]
        text = text.replace("```json", "").replace("```", "").strip()
    return text


def call(prompt: str) -> dict:
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "You are a ZKP circuit security auditor. Always output valid JSON only."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.0,
    )
    raw = resp.choices[0].message.content
    return json.loads(clean_json(raw))


def main():
    for f in sorted(PROMPT_DIR.glob("*.prompt.txt")):
        print(f"[Stage C] calling LLM for {f.name} ...")
        try:
            result = call(f.read_text(encoding="utf-8"))
        except Exception as e:
            result = {"error": str(e)}

        out = OUT_DIR / (f.stem.replace(".prompt", "") + ".llm.json")
        out.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"          -> {out}")
        time.sleep(1)


if __name__ == "__main__":
    main()