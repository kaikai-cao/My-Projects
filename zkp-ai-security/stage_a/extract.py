import re
import json
from pathlib import Path
from collections import defaultdict, deque

KEYWORDS = {"signal", "input", "output", "intermediate",
            "template", "component", "main", "var", "pragma", "circom"}

CIRCUITS = [
    "circuits/safe_square.circom",
    "circuits/unsafe_square.circom",
    "circuits/boundary_square.circom",
]

INTENDED_SEMANTICS = {
    "safe_square.circom":     "The circuit must prove y = x^2. Any (x, y) with y != x^2 is business-invalid.",
    "unsafe_square.circom":   "The circuit must prove y = x^2. Any (x, y) with y != x^2 is business-invalid.",
    "boundary_square.circom": "The circuit must prove y = x^2 + 1, i.e. there exists z with z = x^2 and y = z + 1.",
}


def strip_comments(src: str) -> str:
    src = re.sub(r'//.*', '', src)
    src = re.sub(r'/\*.*?\*/', '', src, flags=re.DOTALL)
    return src


def identifiers(expr: str):
    toks = re.findall(r'\b[A-Za-z_]\w*\b', expr)
    return [t for t in toks if t not in KEYWORDS]


def parse_circuit(path: str):
    src = strip_comments(Path(path).read_text(encoding="utf-8"))

    signals = {}
    assignments = defaultdict(list)
    constraints = []

    for m in re.finditer(r'signal\s+(input|output|intermediate)?\s*(\w+)\s*;', src):
        kind = m.group(1) or "intermediate"
        signals[m.group(2)] = kind

    for m in re.finditer(r'(\w+)\s*(<--|<==)\s*([^;]+);', src):
        lhs, op, rhs = m.group(1), m.group(2), m.group(3).strip()
        assignments[lhs].append(op)
        if op == "<==":
            constraints.append({"lhs": lhs, "rhs": rhs, "type": "<=="})

    for m in re.finditer(r'([^;=]+?)\s*===\s*([^;]+?)\s*;', src):
        constraints.append({"lhs": m.group(1).strip(),
                            "rhs": m.group(2).strip(),
                            "type": "==="})

    return signals, assignments, constraints


def build_constraint_graph(constraints):
    g = defaultdict(set)
    for c in constraints:
        sigs = set(identifiers(c["lhs"]) + identifiers(c["rhs"]))
        for a in sigs:
            for b in sigs:
                if a != b:
                    g[a].add(b)
    return {k: sorted(v) for k, v in g.items()}


def bfs(graph, start):
    seen, q = set(), deque([start])
    while q:
        n = q.popleft()
        for nb in graph.get(n, []):
            if nb not in seen:
                seen.add(nb)
                q.append(nb)
    return seen


def apply_rules(signals, assignments, constraints, graph):
    findings = []
    constrained = set()
    for c in constraints:
        constrained.update(identifiers(c["lhs"]))
        constrained.update(identifiers(c["rhs"]))

    # R1
    for name, ops in assignments.items():
        if "<--" in ops and name not in constrained:
            findings.append({"rule": "R1", "signal": name,
                             "message": f"'{name}' assigned via <-- but never constrained"})

    # R2
    for name, kind in signals.items():
        if kind == "output" and name not in constrained:
            findings.append({"rule": "R2", "signal": name,
                             "message": f"output '{name}' never appears in any constraint"})

    # R3
    inputs = {n for n, k in signals.items() if k == "input"}
    outputs = {n for n, k in signals.items() if k == "output"}
    reachable = set()
    for inp in inputs:
        reachable |= bfs(graph, inp)
    for out in outputs:
        if out not in reachable:
            findings.append({"rule": "R3", "signal": out,
                             "message": f"output '{out}' has no constraint-path to any input"})

    # R4
    if signals and len(constraints) < len(signals) / 2:
        findings.append({"rule": "R4", "signal": "-",
                         "message": f"low constraint density: {len(constraints)} constraints / {len(signals)} signals"})
    return findings


def process(path: str):
    signals, assignments, constraints = parse_circuit(path)
    graph = build_constraint_graph(constraints)
    findings = apply_rules(signals, assignments, constraints, graph)

    return {
        "file": Path(path).name,
        "source": Path(path).read_text(encoding="utf-8"),
        "signals": signals,
        "assignments": {k: v for k, v in assignments.items()},
        "constraints": constraints,
        "constraint_graph_edges": [[k, v] for k, vs in graph.items() for v in vs],
        "rule_findings": findings,
        "intended_semantics": INTENDED_SEMANTICS[Path(path).name],
    }


def main():
    out_dir = Path("results/stage_a")
    out_dir.mkdir(parents=True, exist_ok=True)
    for path in CIRCUITS:
        result = process(path)
        out_file = out_dir / (Path(path).stem + ".json")
        out_file.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"[Stage A] {path} -> {out_file}  ({len(result['rule_findings'])} findings)")


if __name__ == "__main__":
    main()