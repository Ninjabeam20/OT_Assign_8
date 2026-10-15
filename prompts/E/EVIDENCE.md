# Track E: evidence record

## Actual prompt and response evidence

The actual user instruction "Implement the plan." and the complete approved portfolio plan are in [visible conversation excerpts](../VISIBLE_CONVERSATION.md), timestamp 2026-10-15T03:58:46.109Z and preceding plan. Scope for this track: Synthetic shuttle CVRP: fixed baseline, capacity-aware nearest neighbor, MTZ ILP.

This record is a retrospective index prepared on 2026-10-15, not a reconstructed verbatim conversation. Any pre-existing task/session notes in this directory remain labeled summaries. The actual generated response artifact is [the complete implementation](../../optlab/track_e.py). Its first 24 lines are retained below as an actual source excerpt, not a chat quote:

```python
"""Track E: synthetic campus capacitated vehicle routing, unlimited shuttle trips."""
import itertools
import time
import numpy as np
from scipy.optimize import milp, Bounds, LinearConstraint
from scipy.sparse import lil_matrix


def distance_matrix(points):
    points=np.asarray(points,float)
    return np.linalg.norm(points[:,None,:]-points[None,:,:],axis=2)


def validate_routes(routes, demands, capacity):
    visits=[]
    for route in routes:
        if len(route)<3 or route[0]!=0 or route[-1]!=0: return False
        middle=route[1:-1]
        if any(i<=0 or i>=len(demands) for i in middle): return False
        if sum(demands[i] for i in middle)>capacity: return False
        visits.extend(middle)
    return sorted(visits)==list(range(1,len(demands)))


```

## Revisions and verification

See [genuine failure/revision log](../../docs/AI_FAILURE_LOG.md), [coverage-to-test mapping](../../docs/COVERAGE.md), [full raw result](../../results/E.json), and [final verification](../../docs/FINAL_VERIFICATION.md). The saved full result's source hash matches the implementation. Local audit suite: 63 passing tests; the selected submission suite has 61 algorithm/native correctness tests. Two extra runner-infrastructure checks remain local. Track G additionally retains full upstream guest logs; unchanged expensive guest tests were not repeated during packaging. For B, the pre-review Codex output and original Gemini output are separately preserved in `../second-tool/`.

## Commit reference

See the Track E row of [the real integration commit map](../COMMITS.md). Commits integrate already-written and tested artifacts; they do not imply historical per-track commits existed during development.
