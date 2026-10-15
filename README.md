# Optimize Anything · Assignment 8

Ten optimization experiments, from numerical methods and routing to compilers, operating systems, databases and quantum computing.

**Main case study:** campus shuttle routing with capacity constraints. The study uses synthetic data, with five seeded instances at each of two sizes; it is not a campus survey.

## Start here

| Looking for… | Open |
|---|---|
| The complete report | **[Technical report (PDF)](output/pdf/Assignment_8_Technical_Report.pdf)** · [Markdown version](docs/REPORT.md) |
| Assignment coverage | [Chapter 6 coverage checklist](docs/COVERAGE.md) |
| Code and measured results | [Experiments A–J](#experiments-a-j) |
| Setup and commands | [Run the project](#run-the-project) |
| AI usage and proof | [AI assistance](#ai-assistance) |
| Verification details | [Final verification](docs/FINAL_VERIFICATION.md) · [Submission status](docs/SUBMISSION_STATUS.md) |

## Selected findings

- **xv6:** median fork-workload time falls from **81 to 8 guest ticks (10.125×)**. CPU and mixed workloads show no improvement. Two kernel features changed together, so their individual effects are not isolated.
- **Test selection:** greedy retains **14 of 53 cases**; ILP retains **13**. Both preserve observed line coverage but detect **3 of 4 injected faults**, compared with 4 for the full suite.
- **Quantum experiments:** circuits run in classical simulation. Query-count advantages are reported separately from wall-clock time; no real-QPU speedup is claimed.

The report includes baseline comparisons, correctness checks and limitations for every track. Saved timings describe the measured host and can vary on other machines.

## Experiments A-J

Each source link opens the implementation; each results link opens the saved full-run measurements.

| Track | Experiment | Code | Results |
|---|---|---|---|
| A | Continuous optimizers, backpropagation and curvature | [Source](optlab/track_a.py) | [A.json](results/A.json) |
| B | Knapsack: greedy, DP, branch-and-bound, ILP; QUBO/Ising | [Source](optlab/track_b.py) | [B.json](results/B.json) |
| C | QAOA, VQE, parameterized circuits and quantum optimizers | [Source](optlab/track_c.py) | [C.json](results/C.json) |
| D | Submodular coverage, parallel scheduling and distributed learning | [Source](optlab/track_d.py) | [D.json](results/D.json) |
| **E** | **Campus shuttle routing: baseline, nearest neighbor and ILP** | [Source](optlab/track_e.py) | [E.json](results/E.json) |
| F | Four compiler optimization passes and pass ordering | [Source](optlab/track_f.py) | [F.json](results/F.json) |
| G | xv6 copy-on-write fork and lottery scheduling | [Source](optlab/track_g.py) | [G.json](results/G.json) |
| H | SQLite index selection with greedy and ILP | [Source](optlab/track_h.py) | [H.json](results/H.json) |
| I | Quantum algorithms, annealing and QML comparisons | [Source](optlab/track_i.py) | [I.json](results/I.json) |
| J | CPython JSON test-suite reduction | [Source](optlab/track_j.py) | [J.json](results/J.json) |

## Run the project

### 1. Install and verify

Requires **Python 3.12** and [uv](https://docs.astral.sh/uv/).

```sh
git clone https://github.com/Ninjabeam20/OT_Assign_8.git
cd OT_Assign_8
uv sync --frozen
uv run python -m pytest -q
uv run python -m optlab status
```

Track D uses local multiprocessing sockets; the execution environment must allow them.

### 2. Run an experiment

Start with a quick version of the main case study:

```sh
uv run python -m optlab run --track E --quick
```

Run a full track, a group of tracks, or the complete portfolio:

```sh
uv run python -m optlab run --track E
uv run python -m optlab run --track BEHJ
uv run python -m optlab run --track all
```

**Quick runs** write to `results/quick/`. **Full runs** write to `results/` and replace the corresponding saved measurements. The committed full results include source hashes, timestamps and environment metadata.

The complete portfolio includes xv6 and requires the additional setup below.

### 3. Generate the report or repeat the AI comparison

```sh
uv run python -m optlab report
uv run python scripts/compare_ai.py
```

Report generation uses the saved full results and the locked ReportLab dependency. Visual PDF inspection uses Poppler (`brew install poppler` on macOS).

<details>
<summary><strong>Additional setup for Track G: xv6</strong></summary>

On macOS:

```sh
brew install qemu riscv64-elf-gcc make
uv run python scripts/xv6-setup.py
uv run python -m optlab run --track G
```

Setup downloads the pinned MIT xv6 archive, verifies its SHA-256 and applies the tracked kernel patch. It refuses to overwrite existing vendor trees.

The runner expects the `riscv64-elf-` executable prefix. Linux packages using `riscv64-unknown-elf-` need compatible wrappers or a prefix adaptation. Host-native compiler inspection was verified on macOS Apple Silicon; Linux reproduction is not claimed.

The saved full xv6 run took about **7.4 minutes**, including upstream usertests for the baseline on one hart and the optimized kernel on one and three harts. Vendor sources and compiled products are excluded from Git.

See [systems notes](docs/systems.md), [kernel patch](scripts/xv6-optimization.patch) and [source manifest](scripts/xv6-upstream.json).

</details>

## Repository guide

| Folder | Contents |
|---|---|
| [`optlab/`](optlab/) | Track implementations, shared runner and report generator |
| [`tests/`](tests/) | Algorithm and native-code correctness tests |
| [`results/`](results/) | Full measurements and final xv6 logs |
| [`output/`](output/) | Report PDF and measured charts |
| [`docs/`](docs/) | Formulations, coverage, methods and verification |
| [`prompts/`](prompts/) | AI records, original outputs, comparison and proof images |
| [`scripts/`](scripts/) | AI comparison and xv6 setup/verification tools |
| [`LICENSES/`](LICENSES/) | Third-party license notices |

Local environments, compiled vendor trees, private evidence, scratch logs, duplicate runs and extra development checks stay outside the submission.

## AI assistance

| Tool / model label | Date | Work |
|---|---|---|
| Codex / `gpt-6-astra` (original execution-record label) | 2026-10-15 | Planning, implementation, tests, debugging, review and documentation across A–J |
| Gemini 3.8 Flash (High), Google Antigravity IDE | 2026-10-15 | Track B comparison and draft documentation |
| Codex continuation (exact model label not recorded) | 2026-10-15 | Packaging, reproduction checks, report updates and publication |

**Evidence:** [Prompt index](prompts/README.md) · [Gemini screenshots](prompts/second-tool/SCREENSHOT_EVIDENCE.md) · [Antigravity usage statement](prompts/second-tool/ANTIGRAVITY_EVIDENCE.md) · [Original Gemini response](prompts/second-tool/RESPONSE.md)

**Review:** [Independent tool comparison](prompts/second-tool/COMPARISON.md) · [AI failure log](docs/AI_FAILURE_LOG.md) · [Commit traceability](prompts/COMMITS.md)

Both original knapsack implementations fail unrestricted large-integer examples. The corrected project uses exact bounds and integer normalization; original outputs remain preserved. The screenshots show the selected model, prompt execution and response, and also appear in the report appendix. Exact response latency is unverified, and the comparison does not rank foundation models.

<details>
<summary>Record provenance</summary>

Integration commits were created after implementation and review. The commit map connects the preserved evidence to real snapshots rather than inventing a per-edit development timeline. Some track records are retrospective indexes; unavailable original transcripts and the exact continuation model version are not fabricated.

</details>

## Methods and attribution

Detailed explanations: [Numerical methods](docs/numerical.md) · [Quantum methods](docs/quantum.md) · [Systems](docs/systems.md) · [Routing, databases and test selection](docs/COMBINATORIAL_DATABASE_SOFTWARE.md)

MIT xv6-riscv is pinned in the [upstream manifest](scripts/xv6-upstream.json) and attributed under its [MIT license](LICENSES/xv6-LICENSE). Track J runs the installed CPython JSON package (Python 3.12.13 in saved results), covered by the [PSF license](LICENSES/CPython-LICENSE.txt); no CPython source copy is vendored. Dependencies retain their authors' licenses.
