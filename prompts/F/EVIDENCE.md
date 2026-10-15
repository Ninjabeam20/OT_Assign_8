# Track F: evidence record

## Actual prompt and response evidence

The actual user instruction "Implement the plan." and the complete approved portfolio plan are in [visible conversation excerpts](../VISIBLE_CONVERSATION.md), timestamp 2026-10-15T03:58:46.109Z and preceding plan. Scope for this track: Temporary IR, four passes, greedy lookahead ordering, native timings (three programs, five timing repeats).

This record is a retrospective index prepared on 2026-10-15, not a reconstructed verbatim conversation. Any pre-existing task/session notes in this directory remain labeled summaries. The actual generated response artifact is [the complete implementation](../../optlab/track_f.py). Its first 24 lines are retained below as an actual source excerpt, not a chat quote:

```python
"""Unsigned 64-bit straight-line compiler; no effects at import time."""
from dataclasses import dataclass
import re, subprocess, time, statistics, tempfile
from pathlib import Path
MASK=(1<<64)-1
PASSES=('fold','propagate','dead','cse')
@dataclass(frozen=True)
class Instruction:
    dest:str
    op:str
    args:tuple
@dataclass(frozen=True)
class IR:
    instructions:tuple
    result:object

def parse(source):
    tokens=re.findall(r'\d+|[A-Za-z_]\w*|[+*();=\-]|\S',source)
    pos=0; code=[]; names={'x':'x'}
    def take(w=None):
        nonlocal pos
        if pos>=len(tokens): raise ValueError('unexpected end')
        t=tokens[pos];pos+=1
        if w is not None and t!=w: raise ValueError(f'expected {w}, got {t}')
```

## Revisions and verification

See [genuine failure/revision log](../../docs/AI_FAILURE_LOG.md), [coverage-to-test mapping](../../docs/COVERAGE.md), [full raw result](../../results/F.json), and [final verification](../../docs/FINAL_VERIFICATION.md). The saved full result's source hash matches the implementation. Local audit suite: 63 passing tests; the selected submission suite has 61 algorithm/native correctness tests. Two extra runner-infrastructure checks remain local. Track G additionally retains full upstream guest logs; unchanged expensive guest tests were not repeated during packaging. For B, the pre-review Codex output and original Gemini output are separately preserved in `../second-tool/`.

## Commit reference

See the Track F row of [the real integration commit map](../COMMITS.md). Commits integrate already-written and tested artifacts; they do not imply historical per-track commits existed during development.
