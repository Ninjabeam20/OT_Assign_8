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
            ids.append(i)
            remaining -= weights[i]
    return sum(values[i] for i in ids), ids


def dynamic_programming(weights, values, capacity):
    weights, values, capacity = validate(weights, values, capacity)
    # Immutable predecessor tuples avoid reconstruction through an overwritten DP cell.
    dp = [(0, ()) for _ in range(capacity+1)]
    for i, (w, v) in enumerate(zip(weights, values)):
        previous = dp[:]
        for c in range(w, capacity+1):
            candidate = previous[c-w][0]+v
            if candidate > previous[c][0]:
                dp[c] = (candidate, previous[c-w][1]+(i,))
    value, ids = dp[capacity]
    return value, list(ids)


def branch_and_bound(weights, values, capacity):
    weights, values, capacity = validate(weights, values, capacity)
    order = sorted(range(len(weights)), key=lambda i: Fraction(int(values[i]),int(weights[i])) if weights[i] else math.inf, reverse=True)
    best, selected = greedy(weights, values, capacity)
    nodes = [(0, capacity, 0, ())]
    while nodes:
        pos, remaining, value, ids = nodes.pop()
        if value > best:
            best, selected = value, list(ids)
        upper, room = value, remaining
        for i in order[pos:]:
            if weights[i] == 0:
                upper += values[i]
            elif weights[i] <= room:
                upper += values[i]; room -= weights[i]
            else:
                upper += (int(values[i])*int(room))//int(weights[i]); break
        if pos == len(order) or upper <= best:
            continue
        i = order[pos]
        nodes.append((pos+1, remaining, value, ids))
        if weights[i] <= remaining:
            nodes.append((pos+1, remaining-weights[i], value+values[i], ids+(i,)))
    return best, selected


def integer_programming(weights, values, capacity):
    weights, values, capacity = validate(weights, values, capacity)
    if not weights:
        return 0, []
    result = milp(-np.array(values, dtype=float), integrality=np.ones(len(weights)),
                  bounds=Bounds(0, 1), constraints=LinearConstraint([weights], -np.inf, capacity),
                  options={'time_limit': 20})
    if not result.success:
        raise RuntimeError(f'ILP did not prove optimality: {result.message}')
    ids = np.flatnonzero(result.x > .5).tolist()
    return sum(values[i] for i in ids), ids


def maxcut_qubo(n, edges):
    q = np.zeros((n,n))
    for u,v in edges:
        q[u,u] -= 1; q[v,v] -= 1
        q[u,v] += 1; q[v,u] += 1
    return q


def qubo_to_ising(q):
    """x=(1-s)/2; return c,h,J such that x'Qx=c+h's+s'Js."""
    q = (np.array(q, dtype=float)+np.array(q, dtype=float).T)/2
    j = q/4
    constant = float(q.sum()/4+np.trace(j))
    np.fill_diagonal(j, 0)
    return constant, -q.sum(axis=1)/2, j


def run(quick=False):
    rows=[]
    methods=[greedy,dynamic_programming,branch_and_bound,integer_programming]
    for seed in range(1 if quick else 5):
        rng=np.random.default_rng(seed)
        weights=rng.integers(1,30,24).tolist(); values=rng.integers(1,80,24).tolist(); cap=100
        optimum=dynamic_programming(weights,values,cap)[0]
        for method in methods:
            method(weights,values,cap)
            times=[]
            for _ in range(2 if quick else 5):
                t=time.perf_counter(); value,ids=method(weights,values,cap); times.append(time.perf_counter()-t)
            assert sum(weights[i] for i in ids)<=cap and len(ids)==len(set(ids))
            rows.append({'seed':seed,'method':method.__name__,'value':value,'optimal_value':optimum,
                         'gap':optimum-value,'seconds_median':float(np.median(times)), 'seconds_samples':times})
    edges=[(0,1),(1,2),(2,3),(3,0)]; q=maxcut_qubo(4,edges); c,h,j=qubo_to_ising(q)
    energies=[]
    for bits in itertools.product([0,1],repeat=4):
        x=np.array(bits); s=1-2*x
        assert np.isclose(x@q@x,c+h@s+s@j@s)
        energies.append({'bits':bits,'qubo_energy':float(x@q@x),'cut':sum(bits[u]!=bits[v] for u,v in edges)})
    # Equality-cardinality constraint: choose exactly two items; penalty larger than sum(values).
    vals=np.array([7,4,5,3]); penalty=float(vals.sum()+1)
    candidates=[(float(-vals@np.array(x)+penalty*(sum(x)-2)**2), x) for x in itertools.product([0,1],repeat=4)]
    best=min(candidates)
    assert sum(best[1])==2
    return {'description':'0/1 knapsack and binary-to-spin reformulation', 'measurements':rows,
            'maxcut':{'edges':edges,'qubo':q.tolist(),'constant':c,'h':h.tolist(),'J':j.tolist(),'enumeration':energies},
            'penalty_example':{'objective':'-v.x + P(sum(x)-2)^2','values':vals.tolist(),'P':penalty,'solution':best[1]},
            'correctness':True,'limitations':['Ratio greedy has no exactness guarantee; DP is pseudo-polynomial; branch-and-bound is exponential in the worst case.']}
