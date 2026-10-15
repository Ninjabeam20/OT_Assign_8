# OT_Assign_8 - Optimize Anything

Public submission: [Ninjabeam20/OT_Assign_8](https://github.com/Ninjabeam20/OT_Assign_8).

Ten implemented optimization experiments. Main study: **synthetic campus shuttle capacitated vehicle routing**, using five seeded instances at each of two sizes. This is simulated data, not a campus survey.

## Run

Python 3.12 is required. Install [uv](https://docs.astral.sh/uv/), then:

```sh
uv sync --frozen
.venv/bin/python -m pytest -q
.venv/bin/python -m optlab status
.venv/bin/python -m optlab run --track E --quick
.venv/bin/python -m optlab run --track BEHJ
.venv/bin/python scripts/compare_ai.py
.venv/bin/python -m optlab report
```

Quick runs write `results/quick/`; full runs write `results/`. The committed full measurements are retained as evidence, with source hashes, timestamps and environment metadata. Timings vary by machine. `--track all` runs all ten tracks, including real xv6 guest tests. Use `python -m optlab`, not `python -m optlab.runner`. Track D needs permission to create local multiprocessing sockets.

For Track G on macOS, install `brew install qemu riscv64-elf-gcc make`. The runner requires the exact executable prefix `riscv64-elf-` (including `riscv64-elf-gcc`); common Linux `riscv64-unknown-elf-` packages need a compatible toolchain wrapper/prefix adaptation. Host-native compiler inspection was verified on macOS Apple Silicon; Linux reproduction is not claimed. Then run:

```sh
.venv/bin/python scripts/xv6-setup.py
.venv/bin/python -m optlab run --track G
```

Setup fetches the pinned MIT archive, checks its SHA-256 and applies the tracked patch. It refuses to overwrite existing vendor trees. Full G includes upstream usertests on baseline one hart and optimized one/three harts; the saved run took about 7.4 minutes. Vendor trees and compiled products are excluded from Git. Report generation additionally needs ReportLab (locked dependency); visual PDF review uses Poppler (`brew install poppler`).

## Portfolio

| Track | Implementation | Full evidence |
|---|---|---|
| A | [Continuous optimizers, neural backprop, Fisher/HVP](optlab/track_a.py) | [A.json](results/A.json) |
| B | [Knapsack greedy/DP/B&B/ILP, QUBO/Ising](optlab/track_b.py) | [B.json](results/B.json) |
| C | [QAOA, VQE, PQC, quantum optimizers/noise](optlab/track_c.py) | [C.json](results/C.json) |
| D | [Submodular coverage, multiprocessing, FedAvg, MGDA/GradNorm](optlab/track_d.py) | [D.json](results/D.json) |
| E | [Fixed baseline, nearest neighbor, MTZ CVRP ILP](optlab/track_e.py) | [E.json](results/E.json) |
| F | [Four compiler passes and greedy ordering](optlab/track_f.py) | [F.json](results/F.json) |
| G | [Actual xv6 COW fork and lottery scheduler](optlab/track_g.py) | [G.json](results/G.json) |
| H | [SQLite greedy/ILP index selection](optlab/track_h.py) | [H.json](results/H.json) |
| I | [Quantum algorithms, annealing, QML comparisons](optlab/track_i.py) | [I.json](results/I.json) |
| J | [CPython JSON coverage-based test reduction](optlab/track_j.py) | [J.json](results/J.json) |

[Technical PDF](output/pdf/Assignment_8_Technical_Report.pdf) · [Report text](docs/REPORT.md) · [Coverage mapping](docs/COVERAGE.md) · [Demo/viva preparation](docs/DEMO_AND_VIVA.md) · [Submission status](docs/SUBMISSION_STATUS.md)

The saved xv6 fork median improves 81 to 8 ticks (10.125x); CPU/mixed medians do not improve. Both kernel features changed together, so there is no causal ablation. Quantum work uses classical statevector/density-matrix simulation, not real quantum hardware; query complexity does not imply simulator speedup. Track J reduces 53 tests to 14 greedy/13 ILP while retaining observed Python line coverage, but detects only three of four injected faults versus four for the full suite. Coverage retention does not preserve all behavior.

## AI tools register

| Tool/model label | Date | Scope and evidence |
|---|---|---|
| Codex / `gpt-6-astra` (original local execution record label) | 2026-10-15 | Planning, code, tests, debugging, review and documentation, A-J; [prompt index](prompts/README.md) |
| Gemini 3.8 Flash (High), Antigravity IDE (user-reported) | 2026-10-15 | Track B comparison and draft documentation; [original response](prompts/second-tool/RESPONSE.md), [independent comparison](prompts/second-tool/COMPARISON.md) |
| Codex continuation (this packaging session; exact model label not recorded here) | 2026-10-15 | Documentation/evidence reconciliation, clean reproduction, report verification and publication; no algorithm changes |

Original outputs are preserved. Both original knapsack implementations fail unrestricted large-integer examples; the corrected project uses exact bounds and integer normalization. [Original chat screenshots](prompts/second-tool/SCREENSHOT_EVIDENCE.md) show the selected model label and response. The UI displays 15 minutes of work; the original response claims approximately 2.5 seconds. Exact response latency is unverified. This comparison does not rank foundation models. [Actual failure log](docs/AI_FAILURE_LOG.md).

Integration commits were created after implementation and review, rather than during each historical edit. [Commit traceability](prompts/COMMITS.md) maps evidence to real commits without inventing a development timeline. The student must understand the code and perform the live demonstration/viva.

## Attribution

MIT xv6-riscv source pin and archive hash: [upstream manifest](scripts/xv6-upstream.json); [MIT license](LICENSES/xv6-LICENSE). Track J executes the installed CPython JSON package (Python 3.12.13 in saved results), attributed under the [PSF license](LICENSES/CPython-LICENSE.txt). No CPython source copy is vendored. Method references are in [numerical](docs/numerical.md), [quantum](docs/quantum.md), [systems](docs/systems.md), and [combinatorial/database/software](docs/COMBINATORIAL_DATABASE_SOFTWARE.md) notes. Dependency licenses remain their authors'.

## Faculty submission contents

This repository contains the Section 9 deliverables: A-J source and required correctness tests; full measured results and plots; the main study/formulations; Chapter 6 mapping; AI register, prompt/response evidence, screenshots, failure log and comparison; report PDF/source; xv6 patch and final guest logs; setup and demo instructions. Duplicate experiments, progress/smoke logs, local handoff, raw private evidence, environments and compiled vendor trees remain local. No ZIP is required by the assignment or included here.

The screenshots satisfy the supplied Gemini interface-evidence gap. Some per-track records are honest retrospective indexes rather than complete original revised-prompt transcripts; missing originals are not fabricated. The exact continuation model version is not recoverable from these records. The student must still understand the code and perform the demonstration/live viva.
