# Track D: evidence record

## Actual prompt and response evidence

The actual user instruction "Implement the plan." and the complete approved portfolio plan are in [visible conversation excerpts](../VISIBLE_CONVERSATION.md), timestamp 2026-10-15T03:58:46.109Z and preceding plan. Scope for this track: Submodular coverage; actual process scheduling; FedAvg; MGDA/GradNorm.

This record is a retrospective index prepared on 2026-10-15, not a reconstructed verbatim conversation. Any pre-existing task/session notes in this directory remain labeled summaries. The actual generated response artifact is [the complete implementation](../../optlab/track_d.py). Its first 24 lines are retained below as an actual source excerpt, not a chat quote:

```python
"""Track D: submodularity, real process parallelism, federation and multitask training."""
import itertools
import math
import multiprocessing as mp
import os
from concurrent.futures import ProcessPoolExecutor
from time import perf_counter
import numpy as np


def greedy_coverage(sets,k):
    selected=[]; covered=set()
    for _ in range(min(k,len(sets))):
        remaining=[i for i in range(len(sets)) if i not in selected]
        best=max(remaining,key=lambda i:len(sets[i]-covered))
        selected.append(best); covered|=sets[best]
    return selected,len(covered)


def exact_coverage(sets,k):
    candidates=itertools.combinations(range(len(sets)),min(k,len(sets)))
    chosen=max(candidates,key=lambda c:len(set().union(*(sets[i] for i in c))))
    return list(chosen),len(set().union(*(sets[i] for i in chosen)))

```

## Revisions and verification

See [genuine failure/revision log](../../docs/AI_FAILURE_LOG.md), [coverage-to-test mapping](../../docs/COVERAGE.md), [full raw result](../../results/D.json), and [final verification](../../docs/FINAL_VERIFICATION.md). The saved full result's source hash matches the implementation. Local audit suite: 63 passing tests; the selected submission suite has 61 algorithm/native correctness tests. Two extra runner-infrastructure checks remain local. Track G additionally retains full upstream guest logs; unchanged expensive guest tests were not repeated during packaging. For B, the pre-review Codex output and original Gemini output are separately preserved in `../second-tool/`.

## Commit reference

See the Track D row of [the real integration commit map](../COMMITS.md). Commits integrate already-written and tested artifacts; they do not imply historical per-track commits existed during development.
