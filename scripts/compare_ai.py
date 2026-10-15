#!/usr/bin/env python3
"""Independent, reproducible comparison of inspected AI outputs; no network access."""
import importlib.util
import json
import random
import statistics
import sys
import time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from optlab import track_b


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def brute(w,v,c):
    return max(sum(v[i] for i in range(len(w)) if m>>i&1) for m in range(1<<len(w)) if sum(w[i] for i in range(len(w)) if m>>i&1)<=c)


def main():
    folder=ROOT/'prompts/second-tool'
    gemini=load('gemini',folder/'knapsack_second_tool.py')
    original=load('original_codex',folder/'codex_before_review.py')
    modules={'Codex original':original,'Gemini original':gemini,'Codex corrected':track_b}
    rng=random.Random(20261015); instances=[]
    for _ in range(100):
        n=rng.randrange(1,13); w=[rng.randrange(0,31) for _ in range(n)]; v=[rng.randrange(0,51) for _ in w]; c=rng.randrange(sum(w)+11)
        instances.append((w,v,c,brute(w,v,c)))
    checks={}; method_names=['greedy','dynamic_programming','branch_and_bound']
    for label,module in modules.items():
        exact=feasible=validation=0
        for w,v,c,opt in instances:
            for name in method_names:
                wc,vc=w[:],v[:]; value,ids=getattr(module,name)(w,v,c)
                assert w==wc and v==vc
                assert len(ids)==len(set(ids)) and sum(w[i] for i in ids)<=c and sum(v[i] for i in ids)==value
                feasible+=1
                if name!='greedy':
                    assert value==opt; exact+=1
        invalid=[([True],[1],1),([1],[False],1),([1],[1],True),([-1],[1],1),([1],[-1],1),([1],[1],-1),([1.5],[1],1),([1],[1.5],1),([1],[1],1.5),(['1'],[1],1),([1],[1,2],1)]
        for name in method_names:
            for w,v,c in invalid:
                try: getattr(module,name)(w,v,c)
                except ValueError: validation+=1
                else: raise AssertionError(f'{label} accepted invalid inputs')
        checks[label]={'exact_checks_passed':exact,'feasibility_checks_passed':feasible,'validation_checks_passed':validation}
    adversarial=[{'name':'Codex bound rounding','weights':[6,1,3,8,8,6],'values':[18014398509481997,18014398509481991,18014398509481988,18014398509482001,18014398509481989,18014398509482000],'capacity':12},
      {'name':'Gemini bound rounding','weights':[8,8,2,3,7,1],'values':[18014398509481985,18014398509481990,18014398509481990,18014398509481989,18014398509481993,18014398509481986],'capacity':12}]
    for case in adversarial:
        w,v,c=case['weights'],case['values'],case['capacity'];case['exact_optimum']=brute(w,v,c)
        case['outputs']={label:module.branch_and_bound(w,v,c)[0] for label,module in modules.items()}
    timings=[]; rng=random.Random(1337)
    workload=[([rng.randint(1,40) for _ in range(20)],[rng.randint(10,100) for _ in range(20)],300) for _ in range(50)]
    for label,module in modules.items():
        for method in method_names:
            fn=getattr(module,method)
            for w,v,c in workload: fn(w,v,c)
            samples=[]
            for _ in range(7):
                start=time.perf_counter()
                for w,v,c in workload: fn(w,v,c)
                samples.append((time.perf_counter()-start)/len(workload))
            timings.append({'implementation':label,'method':method,'median_seconds_per_solve':statistics.median(samples),'seconds_samples':samples})
    result={'tool_metadata':{'tool':'Gemini','model_label_user_reported':'Gemini 3.8 Flash (High)','date_user_reported':'2026-10-15','response_seconds_user_reported':2.5,'attempts_user_reported':1},
      'protocol':{'seed':20261015,'instances':100,'n_range':[1,12],'oracle':'exhaustive subset enumeration','benchmark_instances':50,'benchmark_n':20,'benchmark_capacity':300,'benchmark_repeats':7,'warmup':True,'python':sys.version},
      'checks':checks,'adversarial':adversarial,'timings':timings,
      'tie_example':{label:module.greedy([1,2],[1,2],2) for label,module in modules.items()},
      'limitations':['Original Codex module was made in broader assignment context and imports NumPy/SciPy, unlike Gemini standard-library-only prompt. This is an implementation comparison, not a controlled model ranking.',
      'External response latency/model/attempt metadata is user-provided, not independently timed by Codex.',
      'Corrected Codex implementation benefits from seeing counterexamples; distinguish it from original outputs.']}
    (ROOT/'results/AI_COMPARISON.json').write_text(json.dumps(result,indent=2)+'\n')
    lines=['# Independently verified AI comparison','',
      'User supplied Gemini 3.8 Flash (High), approximately 2.5 seconds and one attempt. Original response/code are preserved unchanged. Original Gemini analysis and status are preserved as GEMINI_COMPARISON_ORIGINAL.md and GEMINI_STATUS_ORIGINAL.md. These are supplied artifacts, not independently authenticated provider exports.','',
      '## Supplied chat screenshots','',
      'Two original user-supplied screenshots show the selected Gemini 3.8 Flash High label, prompt-file execution and response claims. See [screenshot evidence](SCREENSHOT_EVIDENCE.md). The UI displays Worked for 15m; this is distinct from the original response’s unverified approximately 2.5-second claim. Neither exact model response latency nor a complete prompt history is independently established.','',
      '## Verification','',
      'This reproducible check uses 100 instances with 1–12 items (seed 20261015), exhaustive enumeration, 300 feasibility checks and 200 exact-value checks per implementation. All pass on these small integers. All 33 invalid-input checks per implementation pass. Gemini’s six embedded tests also pass.','',
      'Two deliberately chosen large-integer instances expose floating-point branch-and-bound failures in the original implementations. These integers are allowed by the prompt. The corrected project code uses exact rational ordering and integer upper bounds. Original Gemini code remains untouched.','',
      '| Case | Exact optimum | Codex original | Gemini original | Codex corrected |','|---|---:|---:|---:|---:|']
    for a in adversarial: lines.append('| '+a['name']+' | '+str(a['exact_optimum'])+' | '+' | '.join(str(a['outputs'][l]) for l in modules)+' |')
    lines.extend(['','Greedy tie handling may legitimately differ: weights [1,2], values [1,2], capacity 2 gives original Codex value 1 and Gemini value 2. Equal outputs are not required for a heuristic with arbitrary tie-breaking. Very large values such as 10**400 overflow the original float-based ratio calculation; the corrected project handles them.','',
      '## Measured runtime','', 'Same 50 n=20, capacity=300 instances; one warm-up and seven repeated batches. Values below are median per-solve milliseconds. This is runtime, not model response latency.','', '| Implementation | Method | Median ms |','|---|---|---:|'])
    for r in timings:lines.append(f"| {r['implementation']} | {r['method']} | {1000*r['median_seconds_per_solve']:.6f} |")
    lines.extend(['','Exact arithmetic adds overhead but preserves the unrestricted integer contract. Small timing differences do not establish general superiority.','',
      '## Corrections to supplied analysis','',
      '- The original report’s blanket equivalence/full-compliance conclusion fails on the large-integer examples above.',
      '- Greedy can choose different tied-ratio items; identical indices/values are not guaranteed.',
      '- Immutable path tuples make DP reconstruction safe, but storing/copying paths can add O(n) per state: worst-case O(n²C) time and O(nC) live storage, not unconditional O(nC) time/O(C) space.',
      '- B&B path tuples can require O(n²) stack storage; conservative worst-case time including bound/path work is O(n2^n).',
      '- Replaying the supplied seed-1337 benchmark generation lets all items fit in 6/10 hard B&B cases; that label does not establish hard-case superiority.',
      '- 0.003-0.006 ms is 3-6 microseconds, not sub-microsecond.',
      '- The external portfolio status invented Clarke–Wright/2-opt routing and join-order DP. Actual E uses nearest neighbor/MTZ ILP; H uses greedy/ILP index selection. Those claims were corrected in the current ledger.',
      '- Codex original imports NumPy/SciPy and therefore does not satisfy the separate standard-library-only packaging constraint. Its assignment implementation predates this exact comparative prompt; this context difference is disclosed.',
      '- The supplied 100-instance benchmark was not used as independent evidence because no reproducible harness/raw samples accompanied it. The numbers here come from scripts/compare_ai.py and results/AI_COMPARISON.json.','',
      '## Prompt iterations and hallucinations','',
      'Gemini reports one attempt with no follow-up prompts. Codex used multiple task/review iterations in this session; timestamps are in the sanitized conversation export. Corrections were prompted by independent numerical counterexamples and review. Unsupported status and complexity claims were identified rather than accepted.','',
      'Regenerate: `.venv/bin/python scripts/compare_ai.py`. The full-suite regressions protect the corrected code.'])
    (folder/'COMPARISON.md').write_text('\n'.join(lines)+'\n')
    print('Verified 100 instances; saved raw timings and both original-code counterexamples.')

if __name__=='__main__': main()
