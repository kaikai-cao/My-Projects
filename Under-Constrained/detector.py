# detector.py
import re
import sys
from collections import defaultdict, deque

KEYWORDS = {"signal", "input", "output", "intermediate",
            "template", "component", "main", "var", "pragma", "circom"}


def strip_comments(src: str) -> str:
    src = re.sub(r'//.*', '', src)
    src = re.sub(r'/\*.*?\*/', '', src, flags=re.DOTALL)
    return src


def identifiers(expr: str):
    toks = re.findall(r'\b[A-Za-z_]\w*\b', expr)
    return [t for t in toks if t not in KEYWORDS]


def parse(path):
    src = strip_comments(open(path, encoding='utf-8').read())

    signals = {}                      # name -> "input"/"output"/"intermediate"
    assignments = defaultdict(list)   # name -> ["<--", "<=="]
    constraints = []                  # [(lhs, rhs), ...]

    for m in re.finditer(r'signal\s+(input|output|intermediate)?\s*(\w+)\s*;', src):
        kind = m.group(1) or "intermediate"
        signals[m.group(2)] = kind

    for m in re.finditer(r'(\w+)\s*(<--|<==)\s*([^;]+);', src):
        lhs, op, rhs = m.group(1), m.group(2), m.group(3).strip()
        assignments[lhs].append(op)
        if op == "<== " or op == "<==":
            constraints.append((lhs, rhs))

    for m in re.finditer(r'([^;=]+?)\s*===\s*([^;]+?)\s*;', src):
        constraints.append((m.group(1).strip(), m.group(2).strip()))

    return signals, assignments, constraints


def build_constraint_graph(constraints):
    g = defaultdict(set)
    for lhs, rhs in constraints:
        sigs = set(identifiers(lhs) + identifiers(rhs))
        for a in sigs:
            for b in sigs:
                if a != b:
                    g[a].add(b)
    return g


def bfs(graph, start):
    seen, q = set(), deque([start])
    while q:
        n = q.popleft()
        for nb in graph[n]:
            if nb not in seen:
                seen.add(nb)
                q.append(nb)
    return seen


def detect(path):
    signals, assignments, constraints = parse(path)
    graph = build_constraint_graph(constraints)

    constrained = set()
    for lhs, rhs in constraints:
        constrained.update(identifiers(lhs))
        constrained.update(identifiers(rhs))

    findings = []

    # R1: assigned via <-- but never constrained
    for name, ops in assignments.items():
        if "<--" in ops and name not in constrained:
            findings.append(("R1", name,
                             f"signal '{name}' assigned via <-- but never constrained"))

    # R2: output never appears in any constraint
    for name, kind in signals.items():
        if kind == "output" and name not in constrained:
            findings.append(("R2", name,
                             f"output '{name}' never appears in any constraint"))

    # R3: output not reachable from any input in the constraint graph
    inputs  = {n for n, k in signals.items() if k == "input"}
    outputs = {n for n, k in signals.items() if k == "output"}

    reachable = set()
    for inp in inputs:
        reachable |= bfs(graph, inp)

    for out in outputs:
        if out not in reachable:
            findings.append(("R3", out,
                             f"output '{out}' has no constraint-path to any input"))

    # R4: global constraint density
    n_sig, n_con = len(signals), len(constraints)
    if n_sig and n_con < n_sig / 2:
        findings.append(("R4", "-",
                         f"low constraint density: {n_con} constraints for {n_sig} signals"))

    return findings


if __name__ == "__main__":
    for path in sys.argv[1:]:
        print(f"\n=== {path} ===")
        fs = detect(path)
        if not fs:
            print("  (no findings)")
        for rule, sig, msg in fs:
            print(f"  [{rule}] {msg}")