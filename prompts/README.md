# AI evidence index

[Visible conversation excerpts](VISIBLE_CONVERSATION.md) retain actual visible user prompts, approved plan and assistant responses with original UTC timestamps. Private environment/tool messages are excluded. Existing track notes are preserved. Each track's `EVIDENCE.md` labels retrospective material and points to actual generated source, revisions, results and verification. These records do not invent verbatim track-specific prompts where no recoverable plain-text original exists. Some original inter-agent task payloads are not readable plain text in the retained session; existing faithful summaries are labeled as summaries.

[Second-tool originals and independent comparison](second-tool/COMPARISON.md) retain the supplied prompt, response, executable and original analysis/status separately from corrections. [Original artifact hash manifest](ORIGINAL_ARTIFACTS_SHA256.json) allows byte verification.

[Integration commits](COMMITS.md) map actual code/evidence snapshots to real commit hashes. These were made after implementation/review; they are not a historical per-edit timeline. Per-track source excerpts are generated-output evidence, not conversational quotations. The supplied [Gemini screenshots](second-tool/SCREENSHOT_EVIDENCE.md) retain its displayed model label and chat response. No provider-authenticated export or independently timed response is claimed.

- [A: Ten continuous optimizers; nonlinear Newton/Gauss-Newton, backprop, Fisher/HVP](A/EVIDENCE.md)
- [B: Knapsack greedy/DP/B&B/ILP; exact QUBO-to-Ising conversion](B/EVIDENCE.md)
- [C: QAOA/VQE/PQC; parameter-shift/SPSA/QNG; noise and finite-size gradient study](C/EVIDENCE.md)
- [D: Submodular coverage; actual process scheduling; FedAvg; MGDA/GradNorm](D/EVIDENCE.md)
- [E: Synthetic shuttle CVRP: fixed baseline, capacity-aware nearest neighbor, MTZ ILP](E/EVIDENCE.md)
- [F: Temporary IR, four passes, greedy lookahead ordering, native timings (three programs, five timing repeats)](F/EVIDENCE.md)
- [G: Actual xv6 COW fork and lottery scheduler; three repetitions; full usertests one/three harts](G/EVIDENCE.md)
- [H: SQLite greedy/ILP index selection under measured page budget; no join-order DP](H/EVIDENCE.md)
- [I: Quantum circuits, toy Shor order finding, annealing and QML/classical comparisons](I/EVIDENCE.md)
- [J: CPython JSON weighted test selection; deterministic suite with repeated timings, not five seeds](J/EVIDENCE.md)
