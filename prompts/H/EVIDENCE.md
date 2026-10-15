# Track H: evidence record

## Actual prompt and response evidence

The actual user instruction "Implement the plan." and the complete approved portfolio plan are in [visible conversation excerpts](../VISIBLE_CONVERSATION.md), timestamp 2026-10-15T03:58:46.109Z and preceding plan. Scope for this track: SQLite greedy/ILP index selection under measured page budget; no join-order DP.

This record is a retrospective index prepared on 2026-10-15, not a reconstructed verbatim conversation. Any pre-existing task/session notes in this directory remain labeled summaries. The actual generated response artifact is [the complete implementation](../../optlab/track_h.py). Its first 24 lines are retained below as an actual source excerpt, not a chat quote:

```python
"""Track H: budgeted index selection on an actual SQLite sales workload."""
import hashlib
import json
import sqlite3
import tempfile
import time
from pathlib import Path
import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp

CANDIDATES=[('ix_customer','customer'),('ix_region','region'),('ix_day','day'),
            ('ix_customer_day','customer, day'),('ix_region_amount','region, amount')]
QUERIES=[('customer_total','SELECT sum(amount), count(*) FROM sales WHERE customer=?',(42,)),
         ('regional_total','SELECT sum(amount), count(*) FROM sales WHERE region=?',(3,)),
         ('date_total','SELECT sum(amount), count(*) FROM sales WHERE day BETWEEN ? AND ?',(50,60)),
         ('customer_dates','SELECT sum(amount), count(*) FROM sales WHERE customer=? AND day BETWEEN ? AND ?',(42,20,100)),
         ('region_group','SELECT region, sum(amount), count(*) FROM sales GROUP BY region',())]

def create_database(path, n, seed):
    conn=sqlite3.connect(path)
    conn.execute('CREATE TABLE sales(id INTEGER PRIMARY KEY, customer INTEGER, region INTEGER, day INTEGER, amount INTEGER)')
    rng=np.random.default_rng(seed)
    data=np.column_stack((rng.integers(1,1001,n),rng.integers(0,10,n),rng.integers(0,365,n),rng.integers(1,10000,n)))
    conn.executemany('INSERT INTO sales(customer,region,day,amount) VALUES(?,?,?,?)', [tuple(map(int,row)) for row in data])
```

## Revisions and verification

See [genuine failure/revision log](../../docs/AI_FAILURE_LOG.md), [coverage-to-test mapping](../../docs/COVERAGE.md), [full raw result](../../results/H.json), and [final verification](../../docs/FINAL_VERIFICATION.md). The saved full result's source hash matches the implementation. Local audit suite: 63 passing tests; the selected submission suite has 61 algorithm/native correctness tests. Two extra runner-infrastructure checks remain local. Track G additionally retains full upstream guest logs; unchanged expensive guest tests were not repeated during packaging. For B, the pre-review Codex output and original Gemini output are separately preserved in `../second-tool/`.

## Commit reference

See the Track H row of [the real integration commit map](../COMMITS.md). Commits integrate already-written and tested artifacts; they do not imply historical per-track commits existed during development.
