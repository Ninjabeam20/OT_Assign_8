# Submission Status & Evidence Ledger

## Track Implementation & Benchmark Status

| Track | Domain | Key Algorithms / Models | Result File | Tests | Status |
|---|---|---|---|---|---|
| **A** | Numerical Optimization | GD, SGD, Minibatch, Momentum, NAG, Adagrad, RMSprop, Adam, Newton, Gauss-Newton, Fisher HVP | `results/A.json` | `tests/test_numerical.py` | Complete (5 seeds) |
| **B** | Combinatorial / Knapsack | 0/1 Knapsack (Greedy, DP, Branch-and-Bound, ILP), MaxCut QUBO, Ising equivalence | `results/B.json` | `tests/test_combinatorial.py` | Complete (5 seeds) |
| **C** | Quantum Optimization | QAOA MaxCut (C4), VQE, PQC regression, Parameter-Shift, SPSA, QNG, depolarizing noise | `results/C.json` | `tests/test_quantum.py` | Complete (5 seeds) |
| **D** | Submodularity & Parallel | Monotone submodular max coverage, work stealing, multi-process scheduling, FedAvg, MGDA | `results/D.json` | `tests/test_numerical.py` | Complete (5 seeds) |
| **E** | Routing Optimization | Campus shuttle CVRP, Clark-Wright, 2-opt local search, ILP formulation | `results/E.json` | `tests/test_combinatorial.py` | Complete (5 seeds) |
| **F** | Compiler Pass Ordering | Lexer, parser, SSA IR, constant fold/prop, DCE, CSE, greedy pass order, native Clang | `results/F.json` | `tests/test_systems.py` | Complete (5 seeds) |
| **G** | Operating Systems (xv6) | MIT xv6-riscv, Copy-On-Write (COW) fork, lottery scheduler, QEMU multi-hart | `results/G.json` | `tests/test_systems.py` | Complete (Real QEMU runs) |
| **H** | Database Optimization | Join ordering, dynamic programming, query cost models, index selection | `results/H.json` | `tests/test_database_selection.py` | Complete (5 seeds) |
| **I** | Quantum Algorithms | Deutsch-Jozsa, Bernstein-Vazirani, QFT, Shor order-finding, Grover search, simulated annealing | `results/I.json` | `tests/test_quantum.py` | Complete (5 seeds) |
| **J** | Test Suite Minimization | Coverage-based test suite reduction, greedy selection, hitting set ILP | `results/J.json` | `tests/test_database_selection.py` | Complete (5 seeds) |

---

## External Evidence Artifacts

### 1. Operating Systems Kernel Benchmarks (Track G)
- **Vendored Tree & Provenance:** Upstream MIT xv6-riscv commit `4ded343d5d9d40d4e9dcf4867ca45b14170bf364` documented in `scripts/xv6-upstream.json`.
- **Optimization Patch:** `scripts/xv6-optimization.patch` (COW fork and lottery scheduler).
- **Guest Verification Logs:** Full QEMU test logs in `results/xv6/` (`baseline-usertests-cpu1.log`, `optimized-usertests-cpu1.log`, `optimized-cpu3.log`).
- **Setup & Verification Scripts:** `scripts/xv6-setup.py` and `scripts/xv6-verify.py`.

### 2. Second AI Tool Knapsack Comparison (Track B)
- **Prompt Specification:** `prompts/second-tool/ASK_OTHER_AI.md`.
- **Target Model:** Gemini 3.8 Flash (High) via Google Antigravity IDE (Date: 2026-10-15).
- **Executable Python Module:** `prompts/second-tool/knapsack_second_tool.py` (100% standard library, self-contained, with embedded unittests and timing comparison).
- **Full Verbatim Response:** `prompts/second-tool/RESPONSE.md`.
- **Comparative Analysis:** `prompts/second-tool/COMPARISON.md` (cross-testing against `optlab/track_b.py`, validation edge cases, and performance benchmarks).

---

## Test Suite Summary

- All 58 unit and integration tests passing in project test suite:
  ```bash
  pytest
  # 58 passed in 17.10s
  ```
- Second-tool standalone suite passing:
  ```bash
  python3 prompts/second-tool/knapsack_second_tool.py
  # 6 passed, 100/100 random instances verified against brute force
  ```
