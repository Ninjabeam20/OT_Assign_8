# Track G: evidence record

## Actual prompt and response evidence

The actual user instruction "Implement the plan." and the complete approved portfolio plan are in [visible conversation excerpts](../VISIBLE_CONVERSATION.md), timestamp 2026-10-15T03:58:46.109Z and preceding plan. Scope for this track: Actual xv6 COW fork and lottery scheduler; three repetitions; full usertests one/three harts.

This record is a retrospective index prepared on 2026-10-15, not a reconstructed verbatim conversation. Any pre-existing task/session notes in this directory remain labeled summaries. The actual generated response artifact is [the complete implementation](../../optlab/track_g.py). Its first 24 lines are retained below as an actual source excerpt, not a chat quote:

```python
"""Boot and measure real MIT xv6-riscv kernels under QEMU."""
import json, os, re, selectors, shutil, subprocess, time, statistics, uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def guest(variant, repetitions=3, usertests=True, cpus=1):
    if variant not in ('baseline','optimized') or cpus < 1 or repetitions < 0:
        raise ValueError('invalid xv6 experiment configuration')
    if isinstance(usertests,str) and not re.fullmatch(r'[A-Za-z0-9_]+',usertests):
        raise ValueError('invalid usertest name')
    folder=ROOT/'vendor'/('xv6-'+variant)
    run_id=f'{variant}-cpu{cpus}-{time.time_ns()}-{uuid.uuid4().hex[:8]}'
    logdir=ROOT/'results'/'xv6'/run_id
    logdir.mkdir(parents=True,exist_ok=False)
    # This is a dedicated generated benchmark disk. Rebuild for every boot so
    # exhaustive usertests and interrupted runs cannot contaminate later runs.
    (folder/'fs.img').unlink(missing_ok=True)
    build=subprocess.run(['make','-j4','TOOLPREFIX=riscv64-elf-','kernel/kernel','fs.img'],cwd=folder,text=True,capture_output=True)
    (logdir/'build.log').write_text(build.stdout+build.stderr)
    build.check_returncode()
    cmd=['qemu-system-riscv64','-machine','virt','-bios','none','-kernel','kernel/kernel','-m','128M','-smp',str(cpus),'-nographic','-global','virtio-mmio.force-legacy=false','-drive','file=fs.img,if=none,format=raw,id=x0','-device','virtio-blk-device,drive=x0,bus=virtio-mmio-bus.0']
    proc=subprocess.Popen(cmd,cwd=folder,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    selector=selectors.DefaultSelector();selector.register(proc.stdout,selectors.EVENT_READ)
    transcript='';offset=0;verification_start=None
```

## Revisions and verification

See [genuine failure/revision log](../../docs/AI_FAILURE_LOG.md), [coverage-to-test mapping](../../docs/COVERAGE.md), [full raw result](../../results/G.json), and [final verification](../../docs/FINAL_VERIFICATION.md). The saved full result's source hash matches the implementation. Local audit suite: 63 passing tests; the selected submission suite has 61 algorithm/native correctness tests. Two extra runner-infrastructure checks remain local. Track G additionally retains full upstream guest logs; unchanged expensive guest tests were not repeated during packaging. For B, the pre-review Codex output and original Gemini output are separately preserved in `../second-tool/`.

## Commit reference

See the Track G row of [the real integration commit map](../COMMITS.md). Commits integrate already-written and tested artifacts; they do not imply historical per-track commits existed during development.
