# Experiments Log

Daily experiment record for Week 1–3.
For the consolidated research report, see `research_note_week3.md`.

---

## Day 1 — Vulnerability Model Upgrade

**Goal**: Unify "Under-Constrained" and "Over-Constrained" under a single
Circuit Correctness framework.

**Key concepts**:

- Circuit Correctness = business semantics allowed trace set == constraint
  system allowed solution set.
- Under-Constrained: `T ⊂ S` — accepts illegal witnesses.
- Over-Constrained: `T ⊃ S` — rejects legal witnesses.
- Both are instances of "program semantics ≠ constraint semantics".

**Artifacts**:

- ZK Circuit Bug Taxonomy: Under-Constrained / Over-Constrained /
  Public-Input Binding / Logic Mismatch.
- 3 Under-Constrained scenarios, 2 Over-Constrained scenarios.

---

## Day 2 — Fuzzing Basics

**Goal**: Understand why ZK circuit fuzzing is not a direct port of
traditional fuzzing.

**Key concepts**:

- Traditional fuzzing: Generator / Mutator / Oracle (crash detection).
- ZK fuzzing: Oracle must be **semantic consistency**, not crash.
- TCCT (Trace-Constraint Consistency Test) as the ZK oracle.
- Program mutation (not just input mutation) is the core of zkFuzz.

**Artifacts**:

- ZK Circuit Fuzzing framework diagram.
- 10 hand-designed circuit mutations (M1–M10).
- Fuzzing vs ZK Fuzzing comparison table.

---

## Day 3 — TCCT

**Goal**: Establish "execution result vs constraint result" as a unified view.

**Key concepts**:

- Execution trace: what the program actually computed.
- Constraint system: what the proof system requires.
- `T = S` → correct; `T ⊂ S` → under; `T ⊃ S` → over.
- Rewrite under-constrained bugs as "which trace value lost binding to
  which constraint".

**Artifacts**:

- Minimal TCCT pseudo-code.
- 2 circuit examples (under + over) with detection conditions.
- 300–500 word note on why unified oracle matters for automated ZKP analysis.

---

## Day 4 — Detection Baseline v0.2

**Goal**: Turn detection rules into a runnable tool.

**Key concepts**:

- Minimal JSON input format (inputs / public_inputs / outputs /
  internals / assignments / constraints).
- Rules R1–R5:
  - R1: selector missing boolean constraint
  - R2: assignment relation not bound by constraint
  - R3: output not depending on input
  - R4: public input not bound
  - R5: single-point binding (mutation sensitivity marker)
- Unified report fields: Circuit ID, Rule ID, Risk Variable, Evidence,
  Severity, Manual Verdict.

**Artifacts**:

- `baseline/rules_v0_2.py`
- 5 test circuits (safe / under / boundary).
- Auto-generated report.

**Bug found and fixed**:
R2 originally only checked "variable appears in any constraint", which
missed `tmp_unconstrained` (where `tmp` appears in `out === tmp + c`
but its assignment relation `tmp = a*b` is not bound). Fixed to check
"assignment relation is bound".

---

## Day 5 — Experiment Design and Evaluation

**Goal**: Learn to evaluate a detection method, not just demo it.

**Key concepts**:

- TP / FP / FN / TN; Precision / Recall / F1.
- Ground Truth must be manually labeled.
- Four categories: Safe / Under / Over / Ambiguous.
- Ablation thinking: Rule only / LLM only / Rule + LLM.

**Setup**:

- 11 test circuits: Safe(3) + Under(4) + Over(2) + Ambiguous(2).
- 6 vulnerable, 5 safe (ground truth).

**Results (Rule baseline)**:

| Metric | Value |
|--------|-------|
| TP | 3 |
| FP | 1 |
| FN | 3 |
| TN | 4 |
| Precision | 0.750 |
| Recall | 0.500 |
| F1 | 0.600 |

**Failure cases**:

- FP: `ambiguous_dead_var` — R2 cannot distinguish dead variable from
  security-relevant unbound variable.
- FN: `under_range` — no rule detects missing range constraint.
- FN: `over_range_check` / `over_equality` — static rules cannot detect
  over-constrained bugs.

**Artifacts**:

- `results/ground_truth.csv`
- `results/evaluation.csv`
- Failure case list (3 sources).

---

## Day 6 — AI + Static Analysis

**Goal**: Test whether structured analysis + LLM outperforms raw code + LLM.

**Setup**:

- 11 circuits, same ground truth as Day 5.
- Prompt v1: Circom code only.
- Prompt v2: Circom code + structured analysis summary.
- LLM: OpenAI API, temperature=0.

**Results**:

| Method | TP | FP | FN | TN | Precision | Recall | F1 |
|--------|----|----|----|----|-----------|--------|-----|
| Rule | 3 | 1 | 3 | 4 | 0.750 | 0.500 | 0.600 |
| LLM-v1 | 6 | 2 | 0 | 2 | 0.750 | **1.000** | 0.857 |
| LLM-v2 | 5 | 1 | 1 | 4 | **0.833** | 0.833 | 0.833 |

**Key finding**:
LLM-v1 and LLM-v2 have different bias directions. LLM-v1 favors recall
(catches everything, more FPs); LLM-v2 favors precision (fewer FPs, but
misses `under_range`). Not one dominating the other.

**Failure cases**:

| Case | Type | Method | Root Cause |
|------|------|--------|------------|
| `ambiguous_dead_var` | FP | LLM-v1 | Dead variable treated as under-constrained |
| `safe_range_check` | FP | LLM-v2 | Structured summary induced over-reasoning |
| `under_range` | FN | LLM-v2 | Summary lacked business semantics |
| `safe_range_check` | error | LLM-v1 | JSON output not properly escaped |

**Artifacts**:

- `llm/prompts/prompt_v1.txt`, `prompt_v2.txt`
- `llm/llm_experiment.py`
- `llm/raw_outputs/` (all cached responses)
- Comparison table + metrics

**Method**: `python llm/llm_experiment.py run` (calls API) or
`python llm/llm_experiment.py evaluate` (recompute metrics only).

---

## Day 7 — Research Summary

**Goal**: Consolidate code, data, and results into next-stage assets.

**Artifacts**:

- Repository reorganized into `zkp-security-lab/`.
- `notes/research_note_week3.md` — full experimental report.
- `mutations/mutation_catalog.md` — 10 mutations.
- `results/ground_truth.csv` and `results/evaluation.csv`.
- 3 next-stage research questions (RQ1–RQ3).

**Next research questions**:

- **RQ1**: Does structured dependency info reduce LLM false negatives?
- **RQ2**: Can TCCT-style oracle drive automatic counterexample generation?
- **RQ3**: How to generalize across ZK DSLs (Circom → Noir → Cairo)?

---

## Repository Layout
