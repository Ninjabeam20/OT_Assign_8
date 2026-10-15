# Independently verified AI comparison

User supplied Gemini 3.8 Flash (High), approximately 2.5 seconds and one attempt. Original response/code are preserved unchanged. Original Gemini analysis and status are preserved as GEMINI_COMPARISON_ORIGINAL.md and GEMINI_STATUS_ORIGINAL.md. These are supplied artifacts, not independently authenticated provider exports.

## Antigravity usage statement

The student confirms that Gemini 3.8 Flash (High) was used in Google Antigravity IDE. See [usage statement](ANTIGRAVITY_EVIDENCE.md). Original response latency and complete prompt history are not independently verified.

## Verification

This reproducible check uses 100 instances with 1–12 items (seed 20261015), exhaustive enumeration, 300 feasibility checks and 200 exact-value checks per implementation. All pass on these small integers. All 33 invalid-input checks per implementation pass. Gemini’s six embedded tests also pass.

Two deliberately chosen large-integer instances expose floating-point branch-and-bound failures in the original implementations. These integers are allowed by the prompt. The corrected project code uses exact rational ordering and integer upper bounds. Original Gemini code remains untouched.

| Case | Exact optimum | Codex original | Gemini original | Codex corrected |
|---|---:|---:|---:|---:|
| Codex bound rounding | 54043195528445980 | 54043195528445979 | 54043195528445979 | 54043195528445980 |
| Gemini bound rounding | 54043195528445972 | 54043195528445972 | 54043195528445969 | 54043195528445972 |

Greedy tie handling may legitimately differ: weights [1,2], values [1,2], capacity 2 gives original Codex value 1 and Gemini value 2. Equal outputs are not required for a heuristic with arbitrary tie-breaking. Very large values such as 10**400 overflow the original float-based ratio calculation; the corrected project handles them.

## Measured runtime

Same 50 n=20, capacity=300 instances; one warm-up and seven repeated batches. Values below are median per-solve milliseconds. This is runtime, not model response latency.

| Implementation | Method | Median ms |
|---|---|---:|
| Codex original | greedy | 0.003564 |
| Codex original | dynamic_programming | 0.301198 |
| Codex original | branch_and_bound | 0.023009 |
| Gemini original | greedy | 0.003556 |
| Gemini original | dynamic_programming | 0.294942 |
| Gemini original | branch_and_bound | 0.024352 |
| Codex corrected | greedy | 0.016767 |
| Codex corrected | dynamic_programming | 0.302637 |
| Codex corrected | branch_and_bound | 0.050222 |

Exact arithmetic adds overhead but preserves the unrestricted integer contract. Small timing differences do not establish general superiority.

## Corrections to supplied analysis

- The original report’s blanket equivalence/full-compliance conclusion fails on the large-integer examples above.
- Greedy can choose different tied-ratio items; identical indices/values are not guaranteed.
- Immutable path tuples make DP reconstruction safe, but storing/copying paths can add O(n) per state: worst-case O(n²C) time and O(nC) live storage, not unconditional O(nC) time/O(C) space.
- B&B path tuples can require O(n²) stack storage; conservative worst-case time including bound/path work is O(n2^n).
- Replaying the supplied seed-1337 benchmark generation lets all items fit in 6/10 hard B&B cases; that label does not establish hard-case superiority.
- 0.003-0.006 ms is 3-6 microseconds, not sub-microsecond.
- The external portfolio status invented Clarke–Wright/2-opt routing and join-order DP. Actual E uses nearest neighbor/MTZ ILP; H uses greedy/ILP index selection. Those claims were corrected in the current ledger.
- Codex original imports NumPy/SciPy and therefore does not satisfy the separate standard-library-only packaging constraint. Its assignment implementation predates this exact comparative prompt; this context difference is disclosed.
- The supplied 100-instance benchmark was not used as independent evidence because no reproducible harness/raw samples accompanied it. The numbers here come from scripts/compare_ai.py and results/AI_COMPARISON.json.

## Prompt iterations and hallucinations

Gemini reports one attempt with no follow-up prompts. Codex used multiple task/review iterations in this session; timestamps are in the sanitized conversation export. Corrections were prompted by independent numerical counterexamples and review. Unsupported status and complexity claims were identified rather than accepted.

Regenerate: `.venv/bin/python scripts/compare_ai.py`. The full-suite regressions protect the corrected code.
