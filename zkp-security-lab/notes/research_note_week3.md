# Research Note — Week 3
## ZK Circuit Security: From Taxonomy to LLM-Assisted Detection

---

## 1. Problem

ZK circuit correctness bugs are currently detected in a fragmented way:
under-constrained, over-constrained, and public-input binding each have
their own detection rules. There is no unified oracle.

Meanwhile, LLMs are increasingly used for ZK circuit auditing, but their
role is unclear: independent auditor, or assistive tool?

This week investigates both questions under a unified framework.

---

## 2. Method

### 2.1 Unified View: TCCT

We adopt **Trace-Constraint Consistency Test (TCCT)** as the unified oracle:

> Circuit Correctness = trace set T == constraint solution set S

- `T ⊂ S` → Under-Constrained
- `T ⊃ S` → Over-Constrained
- `T = S` → Correct

This unifies under- and over-constrained bugs as instances of
"program semantics ≠ constraint semantics".

### 2.2 Static Baseline v0.2

Five rules implemented in `baseline/rules_v0_2.py`:

| Rule | Detects |
|------|---------|
| R1   | selector missing boolean constraint |
| R2   | assignment relation not bound by constraint |
| R3   | output not depending on input |
| R4   | public input not bound |
| R5   | single-point binding (mutation sensitivity marker) |

Input format: structured JSON with `inputs`, `public_inputs`, `outputs`,
`assignments`, `constraints`.

### 2.3 LLM Comparison

Two prompt variants:

- **v1**: Circom code only
- **v2**: Circom code + structured analysis summary (variable lists,
  constraint lists, dependency info, selector patterns)

LLM output constrained to JSON with fields: `vulnerability_type`,
`variable`, `evidence`, `attack_input`, `fix_suggestion`, `confidence`.

---

## 3. Setup

| Item          | Value |
|---------------|-------|
| Test circuits | 11 (Safe 3, Under 4, Over 2, Edge 2) |
| Ground truth  | Manual, 6 vulnerable / 5 safe |
| Static rules  | R1–R5, Python |
| LLM           | OpenAI API, temperature=0 |
| Metrics       | Precision, Recall, F1 |

---

## 4. Results

### 4.1 Confusion Matrix and Metrics

| Method  | TP | FP | FN | TN | Precision | Recall  | F1    |
|---------|----|----|----|----|-----------|---------|-------|
| Rule    | 3  | 1  | 3  | 4  | 0.750     | 0.500   | 0.600 |
| LLM-v1  | 6  | 2  | 0  | 2  | 0.750     | **1.000** | 0.857 |
| LLM-v2  | 5  | 1  | 1  | 4  | **0.833** | 0.833   | 0.833 |

### 4.2 Key Observations

1. **LLM-v1 achieves Recall = 1.000** but pays with 2 FPs.
2. **LLM-v2 improves Precision to 0.833** but introduces 1 FN (`under_range`).
3. LLM-v1 and LLM-v2 have **different bias directions**, not one dominating.

### 4.3 On the 4-Circuit vs 11-Circuit Gap

With only 4 circuits, LLM-v2 looked perfect (F1 = 1.000).
Expanding to 11 circuits revealed that structured summaries can both
help (remove dead-variable FP) and hurt (suppress legitimate suspicion).

---

## 5. Failure Cases

| Case                | Type  | Method  | Root Cause |
|---------------------|-------|---------|------------|
| `ambiguous_dead_var`| FP    | LLM-v1  | Dead variable treated as under-constrained; no business impact analysis |
| `safe_range_check`  | FP    | LLM-v2  | Structured summary induced over-reasoning about weak assignments |
| `under_range`       | FN    | LLM-v2  | Summary lacked business semantics, suppressed active suspicion |
| `safe_range_check`  | error | LLM-v1  | JSON output not properly escaped |

### 5.1 Detailed Analysis

**`ambiguous_dead_var` (LLM-v1 FP)**:
The LLM correctly noted `dead` was "unused" but still classified it as
under-constrained. The missing step: "unconstrained **AND** affects
verifier-visible statement" → vulnerability.

**`safe_range_check` (LLM-v2 FP)**:
The structured summary listed `b0 <-- x & 1` and `b1 <-- x >> 1` as
weak assignments. LLM-v2 interpreted this as "b0/b1 unconstrained",
missing that `x === b0 + 2*b1` plus boolean constraints already fully
bind `x`'s range.

**`under_range` (LLM-v2 FN)**:
The summary had no suspicious entries, so LLM-v2 relaxed. But business
semantics required `x ∈ {0,1,2,3}`, which was not in the constraints
and not in the summary. Structured summary suppressed active suspicion.

---

## 6. Limitations

1. Static rules only cover a subset of Under-Constrained bugs.
2. Over-Constrained detection requires business semantics, not yet formalized.
3. Dead variable vs. unbound critical variable cannot be distinguished statically.
4. Test set only 11 circuits — metrics not statistically significant.
5. No trace execution; attack inputs not verified for executability.

---

## 7. Next Steps

### RQ1: Structured dependency info to reduce LLM false negatives?

**Origin**: `under_range` FN (LLM-v2).
**Hypothesis**: Adding business specification to the structured summary
will restore LLM's ability to detect missing constraints.
**Experiment**: Prompt v3 with business spec + impact analysis requirement.

### RQ2: TCCT-style oracle for automatic counterexample generation?

**Origin**: Day 2–3 TCCT framework.
**Hypothesis**: A TCCT-based fitness function (trace vs. constraint
difference) can guide a genetic algorithm to generate counterexamples
like `sel=2` automatically.
**Experiment**: Minimal fuzzer with TCCT fitness, 100 rounds on `under_selector`.

### RQ3: Cross-DSL generalization?

**Origin**: All current rules and prompts are Circom-specific.
**Hypothesis**: TCCT is language-agnostic; rules R1–R5 and prompt v2
can be partially reused for Noir/Cairo.
**Experiment**: Translate `under_selector` to Noir, test R1 and v2 prompt.

---

## 8. Capability Summary

### What we can detect

- Missing boolean constraint on selectors (R1)
- Assignment relations not bound (R2, after fix)
- Public inputs not bound (R4)
- Over-constrained (LLM only)
- Dead variable vs. vulnerability (LLM-v2)

### What we cannot detect

- Missing range constraints (needs business semantics)
- Incomplete branches (needs path analysis)
- Modular overflow (needs field semantics)
- Cross-signal over-constrained (needs business spec)

### What requires human semantic understanding

- Formalizing business specifications
- Distinguishing dead variables from unbound critical variables
- Over-constrained judgment
- Attack input executability verification

---

## 9. Knowledge Path
Circuit → Constraints → Trace → Detection (TCCT)
→ Fuzzing → Verification → AI-assisted Analysis


---

## 10. One-Sentence Summary

> The most valuable outcome of this week is not "how many bugs the
> detector finds", but **knowing under what conditions it fails**.
> Rule's blind spot is Over-Constrained; LLM-v1's blind spot is dead
> variables; LLM-v2's blind spot is missing business semantics.
> All three failure cases point in one direction: **detecting ZK
> circuit security ultimately requires formalizing business semantics
> and making it part of the oracle.**