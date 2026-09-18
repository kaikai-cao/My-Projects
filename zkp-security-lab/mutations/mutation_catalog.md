# Mutation Catalog

List of circuit mutations designed in Day 2, used to validate detection rules
and to guide fuzzing.

| ID  | Circuit            | Mutation                                        | Exposed By        | Detected By |
|-----|--------------------|-------------------------------------------------|-------------------|-------------|
| M1  | under_selector     | delete `sel*(sel-1)===0`                        | sel=2             | R1          |
| M2  | under_range        | delete range check on x                         | x=256             | (none)      |
| M3  | branch circuit     | delete else-branch constraint                   | flag=0            | R2          |
| M4  | over_equality      | `>=` replaced by `==`                           | a+b>c             | LLM only    |
| M5  | tmp_unconstrained  | `tmp <-- a*b` without constraint                | tmp=999           | R2          |
| M6  | unbound_public     | public input not in constraints                 | any               | R4          |
| M7  | safe_range_check   | remove `x === b0 + 2*b1`                        | x=4               | R2          |
| M8  | under_selector     | replace `a` with `b`                            | a≠b               | (none)      |
| M9  | over_range_check   | add `x0 === 1`                                  | x=0               | LLM only    |
| M10 | ambiguous_dead_var | dead variable left unconstrained                | — (not a bug)     | R2 (FP)     |

## Categories

- **Under-Constrained**: M1, M2, M3, M5, M6, M7
- **Over-Constrained**: M4, M9
- **Logic Mismatch**: M8
- **False Positive Trap**: M10

## Notes

- M2, M4, M8, M9 are not detected by any static rule — they require either
  business semantics (M4, M9) or cross-variable dependency analysis (M2, M8).
- M10 is a false-positive trap: R2 triggers but the variable is a dead variable,
  not a security-relevant unbound signal.