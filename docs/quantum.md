# Quantum experiments: Tracks C and I

These are executable small-instance simulations, not claims of quantum speedup. Run through the project runner or call `optlab.track_c.run()` / `optlab.track_i.run()` from Python. Full mode uses seeds 0–4; quick mode uses seed 0 and reduced optimization/sampling budgets. Functions have no import-time benchmarks or file writes. All random draws use explicit seeds.

## Track C design

**QAOA:** p=2 on the fixed four-cycle, unit edges (0,1), (1,2), (2,3), (3,0). Exhaustive enumeration yields maximum cut 4 at bitstrings 0101 and 1010. The cost phase applies exp(-i gamma C) and the mixer applies RX(2 beta). Multi-start BFGS optimizes the expected cut; a finite-shot estimate and exact optimum probability are also measured. Shared gamma parameters occur in multiple cost gates, so the naive two-term shift rule is deliberately not applied to the shared QAOA angle. BFGS uses numerical derivatives here.

**VQE:** the real two-qubit Hamiltonian Z0 + Z1 + 0.5 X0 X1 has exact ground energy -sqrt(4.25). Four independently parameterized RY gates surrounding a CNOT can represent its ground state. Parameter-shift derivatives are used for each single-occurrence Pauli rotation. Independent optimization runs compare standard parameter-shift gradient descent, SPSA with two perturbed expectations per update, and quantum natural gradient with a regularized Fubini–Study metric. Every method starts at the same parameters per seed. The QNG metric comes from finite differences of simulator states: this is a real metric calculation, but its hardware measurement overhead is not hidden inside the objective count. The separate statevector-evaluation count records it.

**PQC/QNN:** one-qubit, three-parameter regression of sin(x), with train/test rows randomized per seed. A three-coefficient classical Fourier regression is an intentionally strong baseline using the same periodic knowledge. A circuit that fits sin(x) does not establish a general learning advantage. Track I supplies the classification experiment.

**Shots/noise:** exact 16x16 density-matrix evolution implements E(rho)=(1-p)rho+p/3(XrhoX+YrhoY+ZrhoZ), independently on each qubit after each mixer layer. Noise probabilities 0, .01, .05, .1 and shot counts 128, 1024, 8192 are evaluated. Repeated sample estimates report empirical standard deviation, RMSE and analytical sampling standard error. These are evaluations of clean-optimized angles, not noisy retraining. At p=.75 this convention produces complete single-qubit depolarization; the tests verify that limit.

**Gradient concentration:** random RY/RZ circuits on 2, 4, 6 and 8 qubits have depth equal to qubit count. Parameter-shift derivatives of local Z0 and global Z-product costs are sampled at independent initializations. Variance, raw gradients, timing and statevector storage are retained. Size and depth change together, the sample is small, and the ansatz is structured; no asymptotic barren-plateau conclusion follows.

## Track I design

Wire 0 is the most significant bit. Gate application reshapes and permutes the tensor axes. Deutsch–Jozsa and Bernstein–Vazirani use explicit Hadamards, an auxiliary |-> qubit, and CNOT oracles. The QFT is built from Hadamards, controlled phases, and final swaps; tests independently compare its action on |1> with the positive-exponent Fourier vector. Inverse QFT reverses and adjoints this gate list. QPE simulates controlled powers on an eigenstate.

Shor's demonstration actually evolves an eight-qubit state: four control qubits and a four-qubit work register initialized to |1>. Controlled modular multiplication by powers of 2 modulo 15 acts on the work register, followed by inverse QFT on the control register. The order is recovered from sampled phase integers with continued fractions and verified candidate multiples; gcd postprocessing yields the factors. The circuit does not insert a known period as a substitute for order finding. Dense permutation unitaries make this a toy implementation, not a scalable arithmetic compiler or physical gate estimate.

Grover directly applies phase marking and diffusion. Results distinguish oracle calls, one-qubit gates, and multi-controlled-Z primitives. Theoretical classical query bounds are uniform-target linear search, with expected (N+1)/2 and worst-case N comparisons. A separately executable baseline scans an explicit permuted unique-value array and counts every equality comparison. Both methods use the same marked index and target predicate; the full benchmark places the target last, so measured linear-search counts equal N. Two warmups precede nine batches of 16 calls per method; results retain each per-call batch average and its median. Classical wall time and classical Grover-simulator wall time have distinct labels. Array construction and phase-oracle synthesis are outside both timers; Grover simulation includes state preparation, gate evolution, and exact probability readout. Its reported answer is the modal state, not a sampled measurement, and its single-shot success probability remains separately reported. MCZ decomposition, data loading, oracle synthesis and connectivity are excluded and can erase a small-instance query benefit. Simulator time is not quantum execution time.

The classification task uses 72 noisy two-moons observations, stratified 54/18 training/test rows, a scaler fit only on training rows, and fixed hyperparameters. Both quantum models and all classical baselines use identical rows. A two-qubit angle/product embedding feeds an eight-rotation circuit plus scalar bias (nine trained parameters); a nine-parameter MLP is included, along with logistic regression and an RBF SVM. Parameter-shift gradients include the classical loss chain rule. The fidelity kernel SVM uses |<phi(x)|phi(z)>|^2, tested for positive semidefiniteness. Simulation caches feature states; its state-preparation execution count and the much larger hardware pair-overlap circuit count are separately labeled. Kernel SVM parameters count fitted dual coefficients and intercept, not its fixed feature-map circuit. Raw embedding preparation time is separate from fit/predict time. No test-set tuning is performed.

Simulated quantum annealing uses a finite-temperature Suzuki–Trotter mapping of the transverse-field antiferromagnetic four-cycle to 16 classical imaginary-time replicas. Metropolis updates use the corresponding spatial and temporal couplings as the transverse field decreases geometrically. This is classical path-integral Monte Carlo, not a simulation of real-time coherent dynamics. Reported best/mean replica cuts and optimal-replica fraction must not be called QPU success probabilities. Fully connected logical problems may require costly minor embedding on sparse annealers; this cycle requires only degree-two logical connectivity. Gate-model encoding also scales poorly: exact statevectors use O(2^n) memory and density matrices O(4^n).

## Sources and implementation choices

The implementation uses NumPy/SciPy directly to make the gates, measurements, gradients and counters inspectable. PennyLane is available as a project dependency but is not needed by these tracks. Official reference checks during development: [PennyLane phase estimation documentation](https://docs.pennylane.ai/en/stable/code/api/pennylane.QuantumPhaseEstimation.html), [PennyLane QFT codebook](https://www.pennylane.ai/codebook/quantum-fourier-transform/quantum-fourier-transform/en), and [PennyLane mixed-state simulator documentation](https://docs.pennylane.ai/en/stable/code/api/pennylane.devices.DefaultMixed.html). No source code was copied from these pages.

## Actual development observations

- Initial test execution could not start because the shared project environment did not yet contain pytest. A separate import-availability assertion failed with `AssertionError: quantum track implementation is missing` before either production module was written. This was an expected missing-implementation check, not a numerical algorithm failure.
- A second test attempt after writing the modules still reported `No module named pytest`; a dependency probe also reported `No module named numpy`. These are environment/setup failures, not successful tests. Subsequent actual numerical outcomes are recorded below after verification.

## Measured full-run outcomes

Full runs completed with seeds 0–4. These are observed outcomes on this machine, not expected values copied into the results.

| Experiment | Observed result |
|---|---|
| QAOA expected cut | All five seeds reach 4 within floating-point rounding; exact optimum is 4. |
| VQE | Maximum absolute ground-energy error 1.33e-15. |
| parameter_shift_gradient, 120 updates | Mean energy error 1.55e-08; sample SD 3.443e-08. |
| SPSA, 120 updates | Mean energy error 0.01034; sample SD 0.006571. |
| quantum_natural_gradient, 120 updates | Mean energy error 1.776e-16; sample SD 3.972e-16. |
| variational_quantum_classifier | Mean held-out accuracy 0.7111; sample SD 0.1639 across five splits. |
| quantum_fidelity_kernel_svm | Mean held-out accuracy 0.8111; sample SD 0.0633 across five splits. |
| classical_rbf_svm | Mean held-out accuracy 0.9444; sample SD 0.0680 across five splits. |
| classical_logistic | Mean held-out accuracy 0.9333; sample SD 0.0913 across five splits. |
| classical_mlp_9_parameters | Mean held-out accuracy 0.9000; sample SD 0.0824 across five splits. |
| Shor | All five seeded runs recover order 4 and factors [3, 5]. |
| Simulated quantum / classical annealing | Both find cut 4 in all five runs; this tiny cycle offers no evidence of an advantage. |

Negative results are retained: the variational classifier reaches only 10/18 correct test predictions for seeds 0 and 2, while the classical models perform substantially better on those splits. SPSA remains farther from the exact VQE ground energy at the fixed update budget. Fourier regression has lower error than the PQC on the deliberately simple sine target. These are measured limitations, not coding failures.

Initial numerical verification: 10 tests passed; its only warning was inability to write pytest cache under the default sandbox. Re-running with `-p no:cacheprovider` avoided that filesystem warning. A new classical-annealing-baseline test first failed with `matching classical annealing baseline is missing`; implementation then yielded **11 passed in 0.51 seconds**. Full-suite collection initially failed because concurrently developed `track_b` was absent; a later attempt found `track_h` still absent. The parent agent owns final whole-project verification. No numerical test failure has been concealed or replaced with a predetermined result.

## Review follow-up: executable search comparison

The reviewer identified a real gap: the original Grover section recorded theoretical search counts but did not execute a classical search. Two regression tests first failed for missing `linear_search` and `search_comparison`; after implementation the quantum suite passed all 13 tests. The complete suite initially produced 55 passes and one sandbox socket-permission failure in `test_process_schedulers_do_not_drop_or_duplicate_work`. Re-running with the required local process permissions produced **56 passed in 4.25 seconds**. Track I was rerun through `python -m optlab run --track I`, which recorded environment and source-hash metadata in `results/I.json`.

| Items | Executed linear comparisons | Quantum oracle calls | Linear median (µs/call) | Grover simulator median (µs/call) |
|---:|---:|---:|---:|---:|
| 4 | 4 | 1 | 0.130 | 28.133 |
| 8 | 8 | 2 | 0.177 | 78.643 |
| 16 | 16 | 3 | 0.263 | 156.172 |
| 32 | 32 | 4 | 0.411 | 258.469 |

The measured tiny-array timings include Python overhead and are machine-specific. Logical oracle counts do not measure QPU latency, and the dense statevector simulator is much slower than linear search here. Compiling the known marked-index oracle does not implement a qRAM lookup; no data-access speedup is claimed.
