# Track A: evidence record

## Actual prompt and response evidence

The actual user instruction "Implement the plan." and the complete approved portfolio plan are in [visible conversation excerpts](../VISIBLE_CONVERSATION.md), timestamp 2026-10-15T03:58:46.109Z and preceding plan. Scope for this track: Ten continuous optimizers; nonlinear Newton/Gauss-Newton, backprop, Fisher/HVP.

This record is a retrospective index prepared on 2026-10-15, not a reconstructed verbatim conversation. Any pre-existing task/session notes in this directory remain labeled summaries. The actual generated response artifact is [the complete implementation](../../optlab/track_a.py). Its first 24 lines are retained below as an actual source excerpt, not a chat quote:

```python
"""Track A: transparent first/second-order optimization and curvature experiments."""
from time import perf_counter
import numpy as np

METHODS = ('gd','sgd','minibatch','momentum','nag','adagrad','rmsprop','adam','newton','gauss_newton')


def optimize_least_squares(x, y, method='gd', seed=0, steps=300, lr=.05, l2=0.):
    """Minimize mean squared residual / 2 + l2 * ||w||² / 2.

    SGD draws one observation, minibatch draws eight; other methods use the
    full deterministic gradient. NAG evaluates at the momentum lookahead.
    Gauss-Newton equals Newton for this linear residual model (documented).
    """
    rng=np.random.default_rng(seed); w=np.zeros(x.shape[1]); velocity=w.copy()
    first=w.copy(); second=w.copy(); history=[]; samples=0
    start=perf_counter()
    for t in range(1,steps+1):
        n=1 if method=='sgd' else min(8,len(x)) if method=='minibatch' else len(x)
        indices=rng.choice(len(x),n,replace=False) if n<len(x) else np.arange(len(x))
        xb,yb=x[indices],y[indices]; samples+=n
        point=w+.9*velocity if method=='nag' else w
        g=xb.T@(xb@point-yb)/n+l2*point
        if method in ('gd','sgd','minibatch'): w-=lr*g
```

## Revisions and verification

See [genuine failure/revision log](../../docs/AI_FAILURE_LOG.md), [coverage-to-test mapping](../../docs/COVERAGE.md), [full raw result](../../results/A.json), and [final verification](../../docs/FINAL_VERIFICATION.md). The saved full result's source hash matches the implementation. Local audit suite: 63 passing tests; the selected submission suite has 61 algorithm/native correctness tests. Two extra runner-infrastructure checks remain local. Track G additionally retains full upstream guest logs; unchanged expensive guest tests were not repeated during packaging. For B, the pre-review Codex output and original Gemini output are separately preserved in `../second-tool/`.

## Commit reference

See the Track A row of [the real integration commit map](../COMMITS.md). Commits integrate already-written and tested artifacts; they do not imply historical per-track commits existed during development.
