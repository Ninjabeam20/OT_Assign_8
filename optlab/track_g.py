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
    def save_logs():
        end=verification_start if verification_start is not None else len(transcript)
        (logdir/'timing.log').write_text(transcript[:end])
        if verification_start is not None:
            (logdir/'verification.log').write_text(transcript[verification_start:])
    def expect(marker,timeout=600):
        nonlocal transcript,offset
        start=time.monotonic()
        while marker not in transcript[offset:]:
            if time.monotonic()-start>timeout:raise TimeoutError(f'{variant}: waiting for {marker}: {transcript[-1000:]}')
            for key,_ in selector.select(1):
                block=os.read(key.fd,65536)
                if not block:raise RuntimeError('QEMU exited: '+transcript[-1000:])
                transcript+=block.decode(errors='replace')
                save_logs()
                if 'panic:' in transcript[offset:] or 'BENCH FAIL' in transcript[offset:]:raise RuntimeError(transcript[-1500:])
        out=transcript[offset:];offset=len(transcript);return out
    def send(s):proc.stdin.write((s+'\n').encode());proc.stdin.flush()
    rows=[];passed=False
    try:
        expect('$ ',60)
        for _ in range(repetitions):
            send('optbench');out=expect('BENCH correctness PASS');expect('$ ') if '$ ' not in out else None
            values={name:int(value) for name,value in re.findall(r'BENCH (fork|cpu|mixed) (\d+)',out)}
            if len(values)!=3:raise RuntimeError('missing benchmark metrics')
            rows.append(values)
        if usertests:
            verification_start=len(transcript)
            send('usertests '+usertests if isinstance(usertests,str) else 'usertests');expect('ALL TESTS PASSED',1800);passed=True
    finally:
        save_logs()
        proc.terminate()
        try:proc.wait(5)
        except subprocess.TimeoutExpired:proc.kill();proc.wait()
        selector.close()
    return {'samples_ticks':rows,
            'median_ticks':{k:statistics.median(r[k] for r in rows) for k in ('fork','cpu','mixed')} if rows else {},
            'usertests_passed':passed,'usertests_scope':usertests if isinstance(usertests,str) else ('all' if usertests else None),'cpus':cpus,'repetitions':repetitions,
            'fresh_filesystem':True,
            'log':str((logdir/'timing.log').relative_to(ROOT)),
            'usertests_log':str((logdir/'verification.log').relative_to(ROOT)) if usertests else None,
            'build_log':str((logdir/'build.log').relative_to(ROOT))}

def speedups(baseline, optimized):
    if baseline.keys()!=optimized.keys():
        raise ValueError('mismatched workload metrics')
    if any(v<=0 for v in [*baseline.values(),*optimized.values()]):
        raise ValueError('timing samples must be positive; increase the workload duration')
    return {k:baseline[k]/optimized[k] for k in baseline}

def experiment_plan(quick=False):
    plan=[dict(variant=v,cpus=1,repetitions=1 if quick else 3,usertests=True)
          for v in ('baseline','optimized')]
    if not quick:
        plan.append(dict(variant='optimized',cpus=3,repetitions=0,usertests=True))
    return plan

def run(quick=False):
    for tool in ['make','riscv64-elf-gcc','qemu-system-riscv64']:
        if not shutil.which(tool):raise RuntimeError(f'Required real-xv6 tool missing: {tool}')
    plan=experiment_plan(quick)
    outcomes=[guest(**config) for config in plan]
    baseline,optimized=outcomes[:2]
    return {'track':'G','description':'Real xv6-riscv: round-robin/eager fork baseline versus equal-ticket lottery/COW fork',
            'upstream':json.loads((ROOT/'scripts/xv6-upstream.json').read_text()),
            'benchmark_mode':'quick' if quick else 'full','experiment_plan':plan,
            'measurements':{'baseline':baseline,'optimized':optimized,'speedup':speedups(baseline['median_ticks'],optimized['median_ticks'])},
            'correctness':{'baseline_usertests':baseline['usertests_passed'],
                           'optimized_usertests':optimized['usertests_passed'],
                           'guest_cow_isolation_and_copyout':True,
                           'optimized_usertests_three_harts':outcomes[2]['usertests_passed'] if len(outcomes)>2 else None,
                           'multicore_log':outcomes[2]['usertests_log'] if len(outcomes)>2 else None},
            'limitations':['QEMU emulation on host; not physical RISC-V hardware.',
                           'Guest timer ticks; coarse timing for short workloads.',
                           'Equal-ticket lottery; no configurable ticket syscall or measured fairness claim.',
                           'Combined COW/scheduler change; cannot attribute gains separately without ablation.',
                           'Performance measured on one hart for reproducibility.'],
            'toolchain':{tool:subprocess.check_output([tool,'--version'],text=True).splitlines()[0] for tool in ['qemu-system-riscv64','riscv64-elf-gcc']}}
