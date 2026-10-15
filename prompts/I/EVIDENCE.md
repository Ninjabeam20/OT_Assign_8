# Track I: evidence record

## Actual prompt and response evidence

The actual user instruction "Implement the plan." and the complete approved portfolio plan are in [visible conversation excerpts](../VISIBLE_CONVERSATION.md), timestamp 2026-10-15T03:58:46.109Z and preceding plan. Scope for this track: Quantum circuits, toy Shor order finding, annealing and QML/classical comparisons.

This record is a retrospective index prepared on 2026-10-15, not a reconstructed verbatim conversation. Any pre-existing task/session notes in this directory remain labeled summaries. The actual generated response artifact is [the complete implementation](../../optlab/track_i.py). Its first 24 lines are retained below as an actual source excerpt, not a chat quote:

```python
"""Track I: explicit small quantum circuits and honest classical comparisons.

Wire 0 is the most significant bit. All execution is classical simulation.
"""
from fractions import Fraction
from math import gcd
from time import perf_counter
import numpy as np
from scipy.optimize import minimize

H = np.array([[1, 1], [1, -1]], dtype=complex) / np.sqrt(2)
X = np.array([[0, 1], [1, 0]], dtype=complex)
Z = np.diag([1, -1]).astype(complex)
CNOT = np.array([[1,0,0,0],[0,1,0,0],[0,0,0,1],[0,0,1,0]], complex)


def apply(state, gate, wires):
    """Apply an ordered k-wire unitary without a full-system matrix."""
    n = int(np.log2(len(state)))
    wires = list(wires)
    axes = wires + [j for j in range(n) if j not in wires]
    tensor = state.reshape([2]*n).transpose(axes).reshape(2**len(wires), -1)
    return (gate @ tensor).reshape([2]*n).transpose(np.argsort(axes)).reshape(-1)

```

## Revisions and verification

See [genuine failure/revision log](../../docs/AI_FAILURE_LOG.md), [coverage-to-test mapping](../../docs/COVERAGE.md), [full raw result](../../results/I.json), and [final verification](../../docs/FINAL_VERIFICATION.md). The saved full result's source hash matches the implementation. Local audit suite: 63 passing tests; the selected submission suite has 61 algorithm/native correctness tests. Two extra runner-infrastructure checks remain local. Track G additionally retains full upstream guest logs; unchanged expensive guest tests were not repeated during packaging. For B, the pre-review Codex output and original Gemini output are separately preserved in `../second-tool/`.

## Commit reference

See the Track I row of [the real integration commit map](../COMMITS.md). Commits integrate already-written and tested artifacts; they do not imply historical per-track commits existed during development.
