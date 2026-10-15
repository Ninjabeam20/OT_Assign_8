import itertools
import pytest
from optlab import track_h as h
from optlab import track_j as j

def test_index_selection_budget_and_optimality():
    sizes=[4,5,3]; gains=[6.,8.,5.]; budget=8
    for method in ['greedy','ILP']:
        ids=h.select_indexes(sizes,gains,budget,method)
        assert sum(sizes[i] for i in ids)<=budget
    ids=h.select_indexes(sizes,gains,budget,'ILP')
    assert sum(gains[i] for i in ids)==13

def test_database_results_equal_with_indexes(tmp_path):
    conn=h.create_database(tmp_path/'db.sqlite',500,3)
    expected=h.query_results(conn)
    for name,columns in h.CANDIDATES:
        conn.execute(f'CREATE INDEX {name} ON sales({columns})')
    assert h.query_results(conn)==expected
    conn.close()

def test_set_cover_exact_and_feasible():
    coverage=[{1,2},{2,3},{3},{1,2,3}]; costs=[2.,2.,1.,4.]
    for method in ['greedy','ILP','naive']:
        ids=j.select_tests(coverage,costs,method)
        assert set.union(*(coverage[i] for i in ids))=={1,2,3}
    ids=j.select_tests(coverage,costs,'ILP')
    assert sum(costs[i] for i in ids)==3
    assert j.select_tests([],[],'ILP')==[]

def test_json_cases_and_real_codebase():
    for name,case in j.cases(): case()
    assert j.codebase_info()['python_lines']>=1000

def test_index_ilp_is_invariant_to_objective_units():
    sizes=[4,5,3]; gains=[6e-8,8e-8,5e-8]
    ids=h.select_indexes(sizes,gains,8,'ILP')
    assert sum(gains[i] for i in ids)==pytest.approx(1.3e-7,abs=1e-14)
