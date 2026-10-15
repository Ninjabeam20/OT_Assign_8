# Track C: evidence record

## Actual prompt and response evidence

The actual user instruction "Implement the plan." and the complete approved portfolio plan are in [visible conversation excerpts](../VISIBLE_CONVERSATION.md), timestamp 2026-10-15T03:58:46.109Z and preceding plan. Scope for this track: QAOA/VQE/PQC; parameter-shift/SPSA/QNG; noise and finite-size gradient study.

This record is a retrospective index prepared on 2026-10-15, not a reconstructed verbatim conversation. Any pre-existing task/session notes in this directory remain labeled summaries. The actual generated response artifact is [the complete implementation](../../optlab/track_c.py). Its first 24 lines are retained below as an actual source excerpt, not a chat quote:

```python
"""Track C: reproducible small variational quantum optimization benchmarks."""
from time import perf_counter
import numpy as np
from scipy.optimize import minimize
from .track_i import apply, zero, H, X, Z, CNOT, ry, rz

EDGES = [(0,1),(1,2),(2,3),(3,0)]


def cut_values(n=4):
    if n != 4: raise ValueError('This benchmark fixes the four-cycle MaxCut instance')
    return np.array([sum(((x>>(n-a-1))&1)!=((x>>(n-b-1))&1) for a,b in EDGES) for x in range(2**n)])


def rx(theta):
    return np.cos(theta/2)*np.eye(2)-1j*np.sin(theta/2)*X


def qaoa_probabilities(theta):
    state=np.ones(16,complex)/4; costs=cut_values()
    for gamma,beta in np.asarray(theta).reshape(-1,2):
        state*=np.exp(-1j*gamma*costs)
        for wire in range(4): state=apply(state,rx(2*beta),[wire])
    return abs(state)**2
```

## Revisions and verification

See [genuine failure/revision log](../../docs/AI_FAILURE_LOG.md), [coverage-to-test mapping](../../docs/COVERAGE.md), [full raw result](../../results/C.json), and [final verification](../../docs/FINAL_VERIFICATION.md). The saved full result's source hash matches the implementation. Local audit suite: 63 passing tests; the selected submission suite has 61 algorithm/native correctness tests. Two extra runner-infrastructure checks remain local. Track G additionally retains full upstream guest logs; unchanged expensive guest tests were not repeated during packaging. For B, the pre-review Codex output and original Gemini output are separately preserved in `../second-tool/`.

## Commit reference

See the Track C row of [the real integration commit map](../COMMITS.md). Commits integrate already-written and tested artifacts; they do not imply historical per-track commits existed during development.
