import itertools
import pytest
from optlab import track_b as b
from optlab import track_e as e

@pytest.mark.parametrize('method',['greedy','dynamic_programming','branch_and_bound','integer_programming'])
def test_knapsack_edges(method):
    f=getattr(b,method)
    assert f([],[],0)==(0,[])
    v,ids=f([0,2,3],[7,4,5],0)
    assert v==7 and ids==[0]
    with pytest.raises(ValueError): f([True],[1],2)
    with pytest.raises(ValueError): f([1],[2,3],2)
    with pytest.raises(ValueError): f([-1],[2],2)

@pytest.mark.parametrize('method',['dynamic_programming','branch_and_bound','integer_programming'])
def test_knapsack_exact_against_enumeration(method):
    import random
    rng=random.Random(4)
    for _ in range(15):
        w=[rng.randrange(0,9) for _ in range(7)]
        v=[rng.randrange(0,20) for _ in w]; cap=12
        best=max(sum(v[i] for i in range(7) if m>>i&1) for m in range(128) if sum(w[i] for i in range(7) if m>>i&1)<=cap)
        got,ids=getattr(b,method)(w,v,cap)
        assert got==best
        assert len(ids)==len(set(ids)) and sum(w[i] for i in ids)<=cap
        assert sum(v[i] for i in ids)==got

def test_qubo_ising_all_assignments():
    import numpy as np
    q=b.maxcut_qubo(4,[(0,1),(1,2),(2,3),(3,0)])
    constant,h,j=b.qubo_to_ising(q)
    for bits in itertools.product([0,1],repeat=4):
        x=np.array(bits); spin=1-2*x
        assert x@q@x==pytest.approx(constant+h@spin+spin@j@spin)
        assert -(x@q@x)==sum(bits[u]!=bits[v] for u,v in [(0,1),(1,2),(2,3),(3,0)])

def test_route_ilp_matches_enumerated_small():
    import numpy as np
    xy=np.array([[0,0],[1,0],[2,0],[0,2],[1,2]],float)
    demand=[0,1,2,1,2]; capacity=3
    distances=e.distance_matrix(xy)
    routes,info=e.solve_ilp(distances,demand,capacity)
    assert e.validate_routes(routes,demand,capacity)
    assert e.route_cost(routes,distances)==pytest.approx(e.exact_enumeration(distances,demand,capacity))
    assert info['optimal']

def test_routes_reject_infeasible_demands():
    import numpy as np
    with pytest.raises(ValueError): e.solve_ilp(np.zeros((2,2)),[0,5],4)
    assert not e.validate_routes([[0,1,1,0]],[0,1],4)

def test_branch_and_bound_large_integer_precision():
    w=[6,1,3,8,8,6]
    v=[18014398509481997,18014398509481991,18014398509481988,18014398509482001,18014398509481989,18014398509482000]
    assert b.branch_and_bound(w,v,12)[0]==54043195528445980

def test_greedy_arbitrary_precision_integer_ratio():
    value,ids=b.greedy([1,2],[10**400,10**399],2)
    assert value==10**400 and ids==[0]

@pytest.mark.parametrize('method',['greedy','dynamic_programming','branch_and_bound'])
def test_accepted_numpy_integers_do_not_overflow(method):
    import numpy as np
    value,ids=getattr(b,method)([1,1],[np.int64(2**62),np.int64(2**62)],2)
    assert value==2**63 and sorted(ids)==[0,1]
