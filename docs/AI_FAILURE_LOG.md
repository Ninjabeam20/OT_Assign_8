# Genuine AI implementation/review failures

These are actual observed development issues. Missing dependencies and intentional test mutations are not counted as AI algorithm failures. Fixes were made during this session; integration commits are linked from per-track prompt records. We do not claim a pre-existing granular history that was not recorded.

## 1. Database objective scale changed the solution (Track H)
The generated ILP passed ordinary tests but raw seconds as coefficients could fall below solver tolerances. Independent review reproduced `sizes=[4,5,3], gains=[6e-8,8e-8,5e-8], budget=8`: it returned gain 5e-8 rather than optimal 1.3e-7. Regression `test_index_ilp_is_invariant_to_objective_units` was observed failing with exactly those values. Fixed by normalizing positive gains before MILP. The regression then passed. Lesson: mathematical unit invariance can be broken by numerical tolerances.

## 2. Compiler timing excluded optimizer work (Track F)
Independent review found generated `compile_seconds` measured only the C backend, excluding the greedy optimization search. This would understate total compilation cost. Fix: record frontend, optimization search and backend times separately and compute end-to-end compilation time. Evidence and regression are in tests/test_systems.py and prompts/F. Lesson: measure the entire operation claimed by a benchmark label.

## 3. Quantum comparison omitted real classical execution (Track I)
The initial generated Grover demonstration reported theoretical classical query counts but omitted the required executed wall-clock comparison. Independent review caught the coverage gap. Fix: implement actual linear search on the same unique-target input, retain measured comparisons, and time both warmed search and Grover simulation with repetitions. Quantum tests were extended and passed. Lesson: complexity counts do not substitute for an implemented baseline or measured runtime.

## Additional observed limitations corrected
Compiler greedy pass search initially stalled on a constant chain with insufficient lookahead; a regression led to three-pass lookahead. The original numerical experiments only compared Newton/Gauss-Newton on linear residuals, where they coincide; a nonlinear exponential fit now demonstrates their difference. Random maximum-coverage fixtures all let greedy reach the optimum; an explicit 5/6 fixture prevents that misleading impression. These supplemental observations are documented in the corresponding track notes.


## 4. Floating-point knapsack pruning and accepted integer types (Track B)
Independent exhaustive counterexamples expose wrong optima in both preserved originals. Codex original gives 54043195528445979 instead of 54043195528445980; Gemini original gives 54043195528445969 instead of 54043195528445972. Float ratio calculation also overflows for 10**400. The corrected project uses Fraction ordering and integer-floor upper bounds. A separate regression exposed NumPy scalar overflow; validated integral inputs are now converted to Python int. Exact fixtures, original outputs and corrected outputs are in `results/AI_COMPARISON.json`; regressions are in `tests/test_combinatorial.py`. Originals are untouched.

## 5. Unsupported second-tool analysis and portfolio claims
The supplied status claimed Clarke-Wright/2-opt, join-order DP and five-seed F/J runs without implementations. The supplied comparison overstated compliance, complexity and benchmark hardness. Current analysis separately corrects these claims: tuple DP has O(n²C) worst-case time/O(nC) live storage, B&B path/bound work can require O(n2^n) time/O(n²) stack storage, and 0.003-0.006 ms is 3-6 microseconds. Six of ten supplied "hard" B&B instances let every item fit. A heuristic tie need not yield identical answers. Preserved originals remain available for inspection.
