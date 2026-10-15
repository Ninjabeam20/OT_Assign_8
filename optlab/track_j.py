"""Track J: weighted coverage-preserving test selection for CPython's JSON package."""
import contextlib
import cProfile
import io
import json
import math
import pstats
import sys
import time
from pathlib import Path
from unittest.mock import patch
import numpy as np
from scipy.optimize import milp, Bounds, LinearConstraint


def codebase_info():
    root=Path(json.__file__).parent
    sources=list(root.glob('*.py'))
    return {'project':'CPython standard-library json (public open-source project)', 'version':sys.version,
            'source':'https://github.com/python/cpython/tree/v3.12.13/Lib/json',
            'license':'Python Software Foundation License',
            'python_lines':sum(len(p.read_text().splitlines()) for p in sources),
            'files':[p.name for p in sources]}


def cases():
    items=[]
    fixtures=[None,True,False,0,-32,1.25,'hello','é🙂','quote"\\\n',[],{},[1,True,None],{'a':[1,2],'b':{'c':'hi'}},list(range(50))]
    for i,value in enumerate(fixtures):
        def case(value=value):
            assert json.loads(json.dumps(value,ensure_ascii=False))==value
            assert json.loads(json.dumps(value,ensure_ascii=True,indent=2,sort_keys=True))==value
        items.append((f'roundtrip_{i}',case))
    for i,value in enumerate(fixtures*2):
        def case(value=value): assert json.loads(json.dumps(value))==value
        items.append((f'redundant_{i}',case))
    for i,text in enumerate(['{','[1,]','{"x":}','NaNx','"unterminated','{"a":1} trailing','01']):
        def case(text=text):
            try: json.loads(text)
            except json.JSONDecodeError: return
            raise AssertionError('accepted invalid JSON')
        items.append((f'invalid_{i}',case))
    def nan_policy():
        assert math.isnan(json.loads('NaN'))
        try: json.dumps(float('nan'),allow_nan=False)
        except ValueError: return
        raise AssertionError('allow_nan=False ignored')
    def custom():
        assert json.loads('{"x":1.25}',parse_float=str)=={'x':'1.25'}
        assert json.loads('{"x":1,"x":2}',object_pairs_hook=list)==[('x',1),('x',2)]
        assert json.dumps(complex(1,2),default=lambda z:[z.real,z.imag])=='[1.0, 2.0]'
    def unicode_policy():
        assert json.dumps('é',ensure_ascii=True)=='"\\u00e9"'
        assert json.dumps('é',ensure_ascii=False)=='"é"'
    def circular():
        v=[]; v.append(v)
        try: json.dumps(v)
        except ValueError: return
        raise AssertionError('circular list accepted')
    items.extend([('nan_policy',nan_policy),('custom_options',custom),('unicode_policy',unicode_policy),('circular',circular)])
    return items


def select_tests(coverages,costs,method):
    if len(coverages)!=len(costs) or any(c<=0 for c in costs): raise ValueError('positive test costs required')
    universe=set().union(*coverages)
    if not universe: return []
    if method in ['greedy','naive']:
        remaining=set(universe); ids=[]
        available=list(range(len(costs)))
        while remaining:
            if method=='greedy': i=max(available,key=lambda k:len(coverages[k]&remaining)/costs[k])
            else: i=available[0]
            available.remove(i); ids.append(i); remaining-=coverages[i]
        return ids
    if method!='ILP': raise ValueError(method)
    elements=sorted(universe)
    a=np.array([[int(e in coverages[i]) for i in range(len(costs))] for e in elements])
    # Normalize microsecond costs to avoid absolute solver feasibility/objective tolerances dominating.
    scaled=np.array(costs)/min(costs)
    result=milp(scaled,integrality=np.ones(len(costs)),bounds=Bounds(0,1),constraints=LinearConstraint(a,1,np.inf))
    if not result.success: raise RuntimeError(result.message)
    return np.flatnonzero(result.x>.5).tolist()


def measure_cases(selected,repeats):
    times=[]
    for _ in range(repeats):
        start=time.perf_counter()
        for _,case in selected: case()
        times.append(time.perf_counter()-start)
    return float(np.median(times)),times


def collect_coverage(case):
    root=str(Path(json.__file__).parent)+ '/'; visited=set()
    previous=sys.gettrace()
    def trace(frame,event,arg):
        if event=='line' and frame.f_code.co_filename.startswith(root):
            visited.add((Path(frame.f_code.co_filename).name,frame.f_lineno))
        return trace
    try:
        sys.settrace(trace); case()
    finally: sys.settrace(previous)
    return visited


def fault_detection(selected):
    """Deliberately injected API faults, not claimed to be historical AI mistakes."""
    original_dumps=json.dumps; original_loads=json.loads
    def wrong_ascii(value,**kwargs): kwargs['ensure_ascii']=False; return original_dumps(value,**kwargs)
    def wrong_nan(value,**kwargs): kwargs['allow_nan']=True; return original_dumps(value,**kwargs)
    def wrong_float(value,**kwargs): kwargs.pop('parse_float',None); return original_loads(value,**kwargs)
    def wrong_pairs(value,**kwargs): kwargs.pop('object_pairs_hook',None); return original_loads(value,**kwargs)
    found={}
    for name,target,replacement in [('ignore_ascii','dumps',wrong_ascii),('ignore_nan','dumps',wrong_nan),('ignore_parse_float','loads',wrong_float),('ignore_pairs','loads',wrong_pairs)]:
        caught=[]
        with patch.object(json,target,replacement):
            for case_name,case in selected:
                try: case()
                except (AssertionError,ValueError,TypeError,RecursionError): caught.append(case_name)
        found[name]=caught
    return found


def run(quick=False):
    suite=cases(); coverages=[collect_coverage(case) for _,case in suite]
    costs=[measure_cases([item],10 if quick else 40)[0] for item in suite]
    universe=set().union(*coverages)
    profile=cProfile.Profile(); profile.enable()
    for _ in range(20):
        for _,case in suite: case()
    profile.disable(); buffer=io.StringIO(); pstats.Stats(profile,stream=buffer).sort_stats('cumulative').print_stats(15)
    rows=[]
    base,base_samples=measure_cases(suite,10 if quick else 50)
    for method in ['full','naive','greedy','ILP']:
        start=time.perf_counter(); ids=list(range(len(suite))) if method=='full' else select_tests(coverages,costs,method)
        selection_seconds=time.perf_counter()-start
        covered=set().union(*(coverages[i] for i in ids)); assert covered==universe
        selected=[suite[i] for i in ids]; runtime,samples=measure_cases(selected,10 if quick else 50)
        faults=fault_detection(selected)
        rows.append({'method':method,'selected_count':len(ids),'selected_names':[suite[i][0] for i in ids],
                     'seconds_median':runtime,'seconds_samples':samples,'selection_seconds':selection_seconds,
                     'speedup':base/runtime,'retained_observed_line_coverage':len(covered)/len(universe),
                     'faults_detected':sum(bool(v) for v in faults.values()),'fault_detection':faults})
    return {'description':'Minimize measured test execution cost while preserving every Python JSON line hit by the full candidate suite.',
            'formulation':'min sum(t_i*x_i), sum_{i covering line l} x_i >= 1 for each observed line, x_i binary.',
            'measurements':rows,'codebase':codebase_info(),'profile':buffer.getvalue(),
            'coverage':{'observed_lines':len(universe),'full_suite_count':len(suite),'per_test':[{'name':suite[i][0],'lines':sorted(coverages[i]),'cost_seconds':costs[i]} for i in range(len(suite))]},
            'correctness':True,'limitations':['Line coverage is not behavioral equivalence; losing fault detection is reported.',
            'CPython C accelerator coverage excluded; Python line coverage only. Submillisecond timings are noisy.',
            'Compiler is under 1000 lines, so the public CPython JSON codebase is used instead as permitted by Track J.']}
