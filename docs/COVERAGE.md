# Chapter 6 and assignment coverage checklist

Scope is the entire explicit list in Assignment 8, confirmed by the user. The syllabus photograph names broad headings only; no undocumented additional taught method is assumed. Every entry below has executable evidence, not just a description. Results paths are relative to the repository root.

| Requirement | Experiment/code | Result evidence |
|---|---|---|
| ML parameters/loss/regularization; continuous vs discrete | A `neural_network`, B knapsack | A neural_network; B measurements |
| Convex and strongly convex convergence | A `optimize_least_squares` | A optimizers, traces and reference gaps |
| Nonconvex, local/global minima, saddle points | A `nonconvex` | A nonconvex; exact Hessian signs and escape trials |
| GD, SGD, mini-batch SGD | A optimizer methods | A optimizers/noise |
| Momentum, NAG | A optimizer methods | A optimizers |
| AdaGrad, RMSProp, Adam | A optimizer methods | A optimizers |
| Newton, Gauss-Newton, nonlinear difference | A `nonlinear_least_squares` | A nonlinear_least_squares |
| Backpropagation distinct from optimizer | A `nn_loss_grad` | A neural_network, finite-difference checks |
| Fisher/empirical Fisher, diagonal/low-rank, HVP | A `curvature` | A curvature, storage/errors |
| Step-size tuning, noisy objectives | A `run` | A step_size_tuning, noise |
| Greedy, ILP, branch-and-bound, DP | B knapsack | B measurements vs exact DP; independent enumeration tests |
| Combinatorial applications | E shuttle routing, H index choice, J test selection | E/H/J measurements |
| QUBO, Ising, binary-to-spin | B `maxcut_qubo`, `qubo_to_ising` | B maxcut, all 16 assignments |
| Penalty constraints | B cardinality-two selection | B penalty_example, exact enumeration |
| Basic quantum states/gates/measurement | I direct statevector/gate routines | I algorithms; quantum tests |
| QAOA and classical baseline | C `qaoa`; B same four-cycle | C qaoa; B maxcut |
| VQE, hybrid optimization | C `vqe` | C vqe vs diagonalization |
| PQC/QNN | C `pqc_regression`; I classifier | C pqc_qnn_regression, I classification |
| Parameter-shift, SPSA, quantum natural gradient | C `optimizer_comparison` | C optimizers, circuit/state counts |
| Barren plateaus/gradient concentration | C `gradient_variance` | C gradient_variance; size/depth caveat |
| Finite-shot costs, hardware noise model | C `shot_noise_study` | C shot_noise, density-matrix depolarizing channel |
| Deutsch-Jozsa, Bernstein-Vazirani | I direct H/CNOT circuits | I algorithms |
| Grover and classical algorithmic comparison | I `search_comparison` | I algorithms, actual queries and timings |
| QFT, QPE | I direct circuits | I algorithms; independent Fourier fixture |
| Shor | I `shor15` controlled modular multiplication | I algorithms: sampled order finding and gcd factors |
| Quantum annealing and embedding limits | I `simulated_quantum_annealing` | I annealing vs classical_annealing; docs/quantum.md |
| Variational classifier, quantum kernels | I `classification` | I classification vs matched classical models |
| Submodular diminishing returns/assumptions/guarantee | D `coverage` | D coverage; exhaustive checks and 5/6 counterexample |
| Load balancing, makespan, work stealing | D `scheduling` | D scheduling, exact task result matching |
| Locality, synchronization, communication | D `parallelism` and scheduling lock counts | D parallelism/scheduling |
| Data/model/pipeline parallelism | D process decomposition | D parallelism; checksums/errors |
| Speedup, efficiency, Amdahl, Gustafson | D timing and explicit theoretical predictions | D scheduling; docs/numerical.md |
| Method selection variables/constraints/hardware/cost | E strategy_selection, report sections | E strategy_selection and docs/REPORT.md |
| FedAvg | D `federated` | D federated vs centralized; varying steps/rounds |
| MGDA, GradNorm | D `multitask` | D multitask vs equal weighting |
| Compiler 4 passes and formulated decision | F lexer/parser/IR/C + greedy pass ordering | F measurements, native equivalence tests |
| xv6 2 features, 3 workloads, usertests | G actual lottery + COW kernel patch | G measurements; results/xv6 logs |
| DBMS 2 methods/default, storage/query plans | H SQLite greedy/ILP | H measurements, plans and result hashes |
| Software engineering on realistic public code | J CPython json weighted set cover | J codebase, profile, coverage, timings and mutations |

## External evidence and human work

- Supplied second-tool response is present at `prompts/second-tool/RESPONSE.md`; preserved code is independently checked by `scripts/compare_ai.py`. The student confirms Gemini use in Google Antigravity IDE; see `prompts/second-tool/ANTIGRAVITY_EVIDENCE.md`. Metadata and latency claims are distinguished from independent measurements.
- Current publication and verification: `docs/SUBMISSION_STATUS.md` and `docs/FINAL_VERIFICATION.md`.
- Actual visible conversation excerpts and labeled per-track retrospective records: `prompts/README.md`. Commit map: `prompts/COMMITS.md`.
- Live viva/demonstration must be performed by the student. `docs/DEMO_AND_VIVA.md` is preparation, not proof of performance.
