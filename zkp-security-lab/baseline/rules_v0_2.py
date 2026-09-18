#!/usr/bin/env python3
"""
Detection Baseline v0.2
Minimal static analyzer for ZK circuits (JSON format).
Rules R1-R5.
"""

import json
import re
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Set


# ---------- 工具函数 ----------
def extract_vars(expr: str) -> Set[str]:
    """Extract variable names from an expression string."""
    if not expr:
        return set()
    tokens = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', expr)
    keywords = {'true', 'false', 'if', 'then', 'else'}
    return {t for t in tokens if t not in keywords and not t.isdigit()}


def parse_constraint(expr: str) -> Set[str]:
    """Parse 'lhs === rhs' and return all variables involved."""
    parts = expr.split('===')
    vars_all = set()
    for p in parts:
        vars_all |= extract_vars(p)
    return vars_all


@dataclass
class Finding:
    circuit_id: str
    rule_id: str
    risk_variable: str
    evidence: str
    severity: str
    manual_verdict: str = ""


# ---------- R1: boolean selector check ----------
def check_r1_boolean_selector(circuit: dict) -> List[Finding]:
    findings = []
    cid = circuit['circuit_id']
    assignments = circuit.get('assignments', {})
    constraints = circuit.get('constraints', [])
    constraints_clean = [c.replace(" ", "") for c in constraints]

    for var, expr in assignments.items():
        expr_clean = expr.replace(" ", "")
        for candidate in extract_vars(expr):
            if f"(1-{candidate})" in expr_clean:
                has_bool = False
                for c in constraints_clean:
                    if f"{candidate}*({candidate}-1)" in c:
                        has_bool = True
                        break
                    if f"{candidate}*(1-{candidate})" in c:
                        has_bool = True
                        break
                if not has_bool:
                    findings.append(Finding(
                        circuit_id=cid,
                        rule_id='R1',
                        risk_variable=candidate,
                        evidence=f'"{candidate}" used as selector in "{expr}" '
                                 f'but no boolean constraint found',
                        severity='high'
                    ))
                    break
    return findings


# ---------- R2: assignment without constraint ----------
def check_r2_unconstrained_assignment(circuit: dict) -> List[Finding]:
    findings = []
    cid = circuit['circuit_id']
    assignments = circuit.get('assignments', {})
    constraints = circuit.get('constraints', [])

    # 把每个约束拆成 "lhs === rhs"，提取所有变量
    constrained_vars = set()
    for c in constraints:
        constrained_vars |= parse_constraint(c)

    for var, expr in assignments.items():
        # 变量本身出现在约束里，不代表它的赋值关系被约束
        # 需要检查：var 是否在某个约束的“被绑定侧”出现过
        # 简化版：如果 var 有赋值，但没有任何约束包含 var 的赋值表达式中的变量
        rhs_vars = extract_vars(expr)
        if not rhs_vars:
            continue
        # 如果 RHS 中的变量都不在任何约束中，说明赋值关系完全没被约束
        # 更强的检查：var 是否在约束里出现过，且约束里包含 rhs_vars
        bound = False
        for c in constraints:
            c_vars = parse_constraint(c)
            if var in c_vars and (rhs_vars & c_vars):
                bound = True
                break
        if not bound:
            findings.append(Finding(
                circuit_id=cid,
                rule_id='R2',
                risk_variable=var,
                evidence=f'variable "{var}" is computed in "{expr}" '
                         f'but its assignment relation is not bound by any constraint',
                severity='high'
            ))
    return findings


# ---------- R3: output dependency ----------
def check_r3_output_dependency(circuit: dict) -> List[Finding]:
    findings = []
    cid = circuit['circuit_id']
    outputs = set(circuit.get('outputs', []))
    inputs = set(circuit.get('inputs', []))
    public_inputs = set(circuit.get('public_inputs', []))
    assignments = circuit.get('assignments', {})

    def deps_of(var, visited=None):
        if visited is None:
            visited = set()
        if var in visited:
            return set()
        visited.add(var)
        if var not in assignments:
            return {var}
        result = set()
        for v in extract_vars(assignments[var]):
            result |= deps_of(v, visited)
        return result

    critical = inputs | public_inputs
    for out in outputs:
        if out not in assignments:
            continue
        deps = deps_of(out)
        if not (deps & critical):
            findings.append(Finding(
                circuit_id=cid,
                rule_id='R3',
                risk_variable=out,
                evidence=f'output "{out}" (computed as "{assignments[out]}") '
                         f'does not depend on any input or public input',
                severity='medium'
            ))
    return findings


# ---------- R4: public input binding ----------
def check_r4_public_input_binding(circuit: dict) -> List[Finding]:
    findings = []
    cid = circuit['circuit_id']
    public_inputs = set(circuit.get('public_inputs', []))
    constraints = circuit.get('constraints', [])

    constrained_vars = set()
    for c in constraints:
        constrained_vars |= parse_constraint(c)

    for pub in public_inputs:
        if pub not in constrained_vars:
            findings.append(Finding(
                circuit_id=cid,
                rule_id='R4',
                risk_variable=pub,
                evidence=f'public input "{pub}" does not appear in any constraint',
                severity='critical'
            ))
    return findings


# ---------- R5: mutation sensitivity ----------
def check_r5_mutation_sensitivity(circuit: dict) -> List[Finding]:
    findings = []
    cid = circuit['circuit_id']
    constraints = circuit.get('constraints', [])
    outputs = set(circuit.get('outputs', []))
    public_inputs = set(circuit.get('public_inputs', []))
    critical = outputs | public_inputs

    constraint_vars = [parse_constraint(c) for c in constraints]

    for i, c in enumerate(constraints):
        remaining = set()
        for j, cv in enumerate(constraint_vars):
            if j != i:
                remaining |= cv
        only_here = constraint_vars[i] - remaining
        for v in only_here:
            if v in critical:
                findings.append(Finding(
                    circuit_id=cid,
                    rule_id='R5',
                    risk_variable=v,
                    evidence=f'constraint "{c}" is the only constraint '
                             f'binding "{v}"; removing it would unbind a critical variable',
                    severity='info'
                ))
                break
    return findings


def analyze(circuit: dict) -> List[Finding]:
    findings = []
    findings.extend(check_r1_boolean_selector(circuit))
    findings.extend(check_r2_unconstrained_assignment(circuit))
    findings.extend(check_r3_output_dependency(circuit))
    findings.extend(check_r4_public_input_binding(circuit))
    findings.extend(check_r5_mutation_sensitivity(circuit))
    return findings


def format_report(circuit: dict, findings: List[Finding]) -> str:
    lines = []
    lines.append("=" * 80)
    lines.append(f"Circuit: {circuit['circuit_id']}")
    lines.append(f"Description: {circuit.get('description', 'N/A')}")
    lines.append("=" * 80)
    if not findings:
        lines.append("No findings.")
    else:
        lines.append(f"{'Rule':<5} {'Risk Var':<15} {'Severity':<10} Evidence")
        lines.append("-" * 80)
        for f in findings:
            lines.append(f"{f.rule_id:<5} {f.risk_variable:<15} {f.severity:<10} {f.evidence}")
    lines.append("")
    return "\n".join(lines)


# ---------- 主程序 ----------
def main():
    circuits_dir = Path(__file__).parent.parent / "circuits"
    if not circuits_dir.exists():
        print("ERROR: circuits/ directory not found.")
        sys.exit(1)

    json_files = sorted(circuits_dir.rglob("*.json"))
    if not json_files:
        print("ERROR: no JSON files found in circuits/.")
        sys.exit(1)

    all_findings = []
    report_chunks = []

    for jf in json_files:
        with open(jf, 'r', encoding='utf-8') as f:
            circuit = json.load(f)
        findings = analyze(circuit)
        chunk = format_report(circuit, findings)
        report_chunks.append(chunk)
        all_findings.extend(findings)

    # Summary
    summary = []
    summary.append("=" * 80)
    summary.append("SUMMARY")
    summary.append("=" * 80)
    summary.append(f"Total circuits: {len(json_files)}")
    summary.append(f"Total findings: {len(all_findings)}")
    by_rule = {}
    for f in all_findings:
        by_rule[f.rule_id] = by_rule.get(f.rule_id, 0) + 1
    for rule, count in sorted(by_rule.items()):
        summary.append(f"  {rule}: {count}")
    summary.append("")
    report_chunks.append("\n".join(summary))

    full_report = "\n".join(report_chunks)
    print(full_report)
    with open("report.txt", "w", encoding="utf-8") as f:
        f.write(full_report)
    print("Report written to report.txt")


if __name__ == "__main__":
    main()



    # evaluate.py
