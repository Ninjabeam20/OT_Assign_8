import importlib
import pytest

def compiler():
    assert importlib.util.find_spec('optlab.track_f'), 'compiler not implemented'
    return importlib.import_module('optlab.track_f')

@pytest.mark.parametrize('source,x,expected', [
 ('let a = 2 + 3 * 4; return a + x;', 9, 23),
 ('let a = x + 1; let b = x + 1; return a * b;', 4, 25),
 ('let a = 100; let a = x - 2; return a;', 8, 6),
 ('return 0 - 1;', 0, 18446744073709551615),
])
def test_language_and_pass_equivalence(source,x,expected):
    f=compiler(); ir=f.parse(source)
    assert f.interpret(ir,x)==expected
    import itertools
    for order in itertools.permutations(f.PASSES):
        assert f.interpret(f.optimize(ir,order),x)==expected

def test_rejects_unknown_and_trailing_tokens():
    f=compiler()
    for source in ['return missing;', 'return 2; garbage', 'let x = @; return x;']:
        with pytest.raises(ValueError): f.parse(source)

def test_optimizer_reduces_work_and_native_matches(tmp_path):
    f=compiler(); ir=f.parse('let a = 2 + 3; let unused = x * 4; return a * x;')
    order, opt, history=f.greedy_order(ir)
    assert f.cost(opt)<f.cost(ir)
    assert f.native_measure(ir,tmp_path/'base',1000)['checksum']==f.native_measure(opt,tmp_path/'opt',1000)['checksum']

def test_greedy_crosses_constant_folding_plateau():
    f=compiler()
    assert f.cost(f.greedy_order(f.parse(f.CASES[0][1]))[1])==3

def test_xv6_ratios_reject_zero_duration():
    from optlab import track_g as g
    assert hasattr(g,'speedups'), 'missing validated timing ratio function'
    assert g.speedups({'fork':81},{'fork':8})=={'fork':10.125}
    with pytest.raises(ValueError,match='positive'):
        g.speedups({'cpu':0},{'cpu':0})

def test_xv6_full_plan_includes_smp_validation():
    from optlab import track_g as g
    assert hasattr(g,'experiment_plan'), 'missing explicit reproducible run plan'
    full=g.experiment_plan(False)
    assert [(x['variant'],x['cpus'],x['repetitions'],x['usertests']) for x in full]==[('baseline',1,3,True),('optimized',1,3,True),('optimized',3,0,True)]
    assert g.experiment_plan(True)==[dict(variant='baseline',cpus=1,repetitions=1,usertests=True),dict(variant='optimized',cpus=1,repetitions=1,usertests=True)]

def test_compiler_end_to_end_cost_includes_search():
    f=compiler();r=f.run(quick=True)
    for row in r['measurements']:
        assert 'search_seconds' in row, 'optimizer search time is missing'
        assert row['search_seconds']>=0 and row['frontend_seconds']>=0
        assert row['baseline']['end_to_end_compile_seconds']==pytest.approx(row['frontend_seconds']+row['baseline']['backend_compile_seconds'])
        assert row['optimized']['end_to_end_compile_seconds']==pytest.approx(row['frontend_seconds']+row['search_seconds']+row['optimized']['backend_compile_seconds'])
