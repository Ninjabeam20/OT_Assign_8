# Demo and viva preparation

This is a preparation guide, not evidence that the student performed a live demo.

## Short demonstration

1. Open README and the technical PDF. Explain the ten tracks and the synthetic shuttle study.
2. Run `.venv/bin/python -m pytest -q` (61 submission tests; the full local audit has 63). A restricted sandbox may need local socket permission for D.
3. Run `.venv/bin/python -m optlab run --track E --quick`; inspect `results/quick/E.json`: coordinates, demands, capacity, routes, feasibility and ILP status/gap. Full evidence stays in `results/E.json`.
4. Run `.venv/bin/python scripts/compare_ai.py`; show both preserved originals, the exhaustive oracle and a large-integer failure. Explain the exact-bound fix and its cost.
5. Open `results/F.json`: show all four passes, native equivalence, timing repetitions and total compilation cost. Open `results/G.json` and its referenced verification logs: explain actual QEMU execution and COW.
6. Open `results/J.json`: compare 53/14/13 tests and four versus three detected faults. Show quantum classical comparisons in `results/I.json`.
7. Regenerate with `.venv/bin/python -m optlab report`. Explain what changes with new measurements and what is retained as historical evidence.

Fresh xv6 setup/full tests need the toolchain and several minutes; use saved logs in a short demo unless explicitly asked to rerun. Understand every command before presenting it.

## Questions to prepare

- **Routing formulation?** Binary vehicle arcs with depot returns; load-based MTZ constraints enforce capacity and prevent nondepot subtours. Unlimited trips, no time windows or finite fleet; distances are Euclidean simulated kilometers.
- **Why ILP and nearest neighbor?** Exact proof/gap on small instances versus a cheap feasible heuristic. Scaling limits and wall time matter alongside route distance.
- **How is correctness checked?** Independent enumeration for tiny routing/knapsack; QUBO all assignments; finite differences/known optima for derivatives; native compiler equivalence; upstream guest usertests; exact SQL result hashes.
- **Why did float B&B fail?** Rounded ratio/bound can prune a branch containing the optimum. Use exact integer/rational arithmetic; acknowledge overhead.
- **Why normalize H gains?** A solver's absolute tolerances can erase tiny coefficients; positive scaling preserves the mathematical optimum and improves numerical behavior.
- **Quantum advantage?** None established by these simulators. Query counts and host wall time are different resources; the saved classical RBF classifier wins this toy task.
- **xv6 causality?** COW and lottery changed together. Fork speed improves, CPU/mixed medians do not; no isolated scheduler or fairness advantage is proved.
- **Coverage vs quality?** Preserving observed Python lines misses one of four mutations; C accelerator coverage is excluded.
- **Compiler economics?** Include frontend/search/backend time; a faster executable may need enough invocations to repay extra compile time.
- **Five seeds everywhere?** Stochastic experiments use seeded instances; F/J use repeated deterministic timings and G uses repeated guest runs.
- **AI reliability?** Both originals had precision errors. Generated status invented methods. Tests and direct source/result inspection led to corrections; original evidence remains unchanged.

Practice an instructor-selected small code modification and explain its expected effect without AI. Do not treat memorizing these answers as understanding the code.
