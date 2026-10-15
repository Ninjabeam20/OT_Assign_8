# Submission status - 2026-10-15

Authoritative current ledger. Original supplied status is preserved at `prompts/second-tool/GEMINI_STATUS_ORIGINAL.md`.

| Track | Verified implementation | Evidence |
|---|---|---|
| A | Ten continuous optimizers; nonlinear Newton/Gauss-Newton, backprop, Fisher/HVP | [results](../results/A.json), [source](../optlab/track_a.py) |
| B | Knapsack greedy/DP/B&B/ILP; exact QUBO-to-Ising conversion | [results](../results/B.json), [source](../optlab/track_b.py) |
| C | QAOA/VQE/PQC; parameter-shift/SPSA/QNG; noise and finite-size gradient study | [results](../results/C.json), [source](../optlab/track_c.py) |
| D | Submodular coverage; actual process scheduling; FedAvg; MGDA/GradNorm | [results](../results/D.json), [source](../optlab/track_d.py) |
| E | Synthetic shuttle CVRP: fixed baseline, capacity-aware nearest neighbor, MTZ ILP | [results](../results/E.json), [source](../optlab/track_e.py) |
| F | Temporary IR, four passes, greedy lookahead ordering, native timings (three programs, five timing repeats) | [results](../results/F.json), [source](../optlab/track_f.py) |
| G | Actual xv6 COW fork and lottery scheduler; three repetitions; full usertests one/three harts | [results](../results/G.json), [source](../optlab/track_g.py) |
| H | SQLite greedy/ILP index selection under measured page budget; no join-order DP | [results](../results/H.json), [source](../optlab/track_h.py) |
| I | Quantum circuits, toy Shor order finding, annealing and QML/classical comparisons | [results](../results/I.json), [source](../optlab/track_i.py) |
| J | CPython JSON weighted test selection; deterministic suite with repeated timings, not five seeds | [results](../results/J.json), [source](../optlab/track_j.py) |

## Verification and packaging

- Local audit suite: **63 passed in 5.87s**, 2026-10-15, with local multiprocessing socket permission. Two extra runner-infrastructure tests remain local; the submission includes 61 algorithm/native correctness tests.
- All ten full result source hashes match their track modules. No track implementation was changed during continuation.
- Saved G full baseline/optimized/three-hart usertests verdicts are true; their referenced logs are retained. The expensive unchanged guest suite was not rerun.
- Original second-tool artifacts preserved; independent 100-instance protocol and adversarial failures are distinguished from supplied claims.
- README, demo guide, per-track evidence and sanitized visible conversation excerpts are included.
- Clean-environment reproduction and final PDF inspection: see [final verification](FINAL_VERIFICATION.md).
- Integration commit references: [commit map](../prompts/COMMITS.md).
- Public repository: **[Ninjabeam20/OT_Assign_8](https://github.com/Ninjabeam20/OT_Assign_8)**. GitHub confirms PUBLIC visibility and default branch `main`. The selected submission tree is verified against the remote after publication. No extra local history, scratch logs, ZIP or environments were pushed.
- Gemini proof includes the Antigravity usage statement and two original screenshots showing model selection, prompt execution and response. Both images are included in the documentation and report appendix.
- Only assignment source/tests/results/report/evidence are selected for publication; local progress and duplicate runs are excluded. No submission ZIP is included.


## Remaining human responsibilities

The student must understand the implementations and perform the live demo/viva. Gemini use in Antigravity is student-confirmed; exact latency and complete iteration history remain unverified. Some track records are retrospective indexes, not complete original/revised-prompt transcripts. The exact continuation model label is not recorded. These limits are disclosed rather than fabricated.
