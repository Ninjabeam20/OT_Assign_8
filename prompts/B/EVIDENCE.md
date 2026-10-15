# Track B: evidence record

## Actual prompt and response evidence

The actual user instruction "Implement the plan." and the complete approved portfolio plan are in [visible conversation excerpts](../VISIBLE_CONVERSATION.md), timestamp 2026-10-15T03:58:46.109Z and preceding plan. Scope for this track: Knapsack greedy/DP/B&B/ILP; exact QUBO-to-Ising conversion.

This record is a retrospective index prepared on 2026-10-15, not a reconstructed verbatim conversation. Any pre-existing task/session notes in this directory remain labeled summaries. The actual generated response artifact is [the complete implementation](../../optlab/track_b.py). Its first 24 lines are retained below as an actual source excerpt, not a chat quote:

```python
"""Track B: exact/heuristic knapsack, Max-Cut QUBO and Ising equivalence."""
from fractions import Fraction
import itertools
import math
import time
import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp


def validate(weights, values, capacity):
    if len(weights) != len(values):
        raise ValueError('weights and values must have equal lengths')
    for x in [*weights, *values, capacity]:
        if isinstance(x, bool) or not isinstance(x, (int, np.integer)) or x < 0:
            raise ValueError('all inputs must be nonnegative integers, not booleans')
    return [int(w) for w in weights], [int(v) for v in values], int(capacity)


def greedy(weights, values, capacity):
    weights, values, capacity = validate(weights, values, capacity)
    ids = []
    remaining = capacity
    for i in sorted(range(len(weights)), key=lambda i: Fraction(int(values[i]),int(weights[i])) if weights[i] else math.inf, reverse=True):
        if weights[i] <= remaining:
```

## Revisions and verification

See [genuine failure/revision log](../../docs/AI_FAILURE_LOG.md), [coverage-to-test mapping](../../docs/COVERAGE.md), [full raw result](../../results/B.json), and [final verification](../../docs/FINAL_VERIFICATION.md). The saved full result's source hash matches the implementation. Local audit suite: 63 passing tests; the selected submission suite has 61 algorithm/native correctness tests. Two extra runner-infrastructure checks remain local. Track G additionally retains full upstream guest logs; unchanged expensive guest tests were not repeated during packaging. For B, the pre-review Codex output and original Gemini output are separately preserved in `../second-tool/`.

## Commit reference

See the Track B row of [the real integration commit map](../COMMITS.md). Commits integrate already-written and tested artifacts; they do not imply historical per-track commits existed during development.
