# Actual task prompt and implementation evidence
Parent task requested a toy integer-language lexer, parser, IR, C generation, constant folding/propagation, dead-code elimination, CSE, and greedy pass-order optimization; measure native equivalence, static instruction count, code size, runtime, compilation time.

Implementation decision: unsigned modulo 2^64, immutable temporary SSA, + - *, let/reassignment, return. Three-pass greedy lookahead crosses enabling-pass plateaus. Native clang -O0 avoids hiding the toy optimizer behind LLVM optimization. Test cases exercise all 24 pass permutations and overflow.

Observed initial failure: assertion `compiler not implemented` before module existed. Pytest was initially absent while parent installed dependencies; independently exercised permutation checks before pytest availability.

Observed greedy-search failure: two-pass lookahead stopped at cost 7 for a constant chain. Added a regression test requiring one multiply (cost 3), then expanded lookahead to three passes.

Review found clang-only compilation measurements omitted optimization search cost. Added a failing end-to-end cost regression, then measured parser, full greedy search, C emission/write and clang separately; explicit end-to-end totals include search for optimized compilation. Reran F through the unified runner for timestamp/source provenance.
