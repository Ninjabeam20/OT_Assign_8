"""Independent fixtures catch update, curvature, aggregation and scheduling bugs."""
import importlib
import numpy as np
import pytest


def module(name):
    spec = importlib.util.find_spec('optlab.' + name)
    assert spec is not None, f'{name} implementation missing'
    return importlib.import_module('optlab.' + name)


@pytest.mark.parametrize('method', ['gd','sgd','minibatch','momentum','nag','adagrad','rmsprop','adam','newton','gauss_newton'])
def test_optimizer_converges_on_known_quadratic(method):
    a = module('track_a')
    x = np.array([[1.,0.],[0.,2.],[1.,1.],[-1.,2.]])
    truth = np.array([1.5,-.5])
    result = a.optimize_least_squares(x,x@truth,method,seed=2,steps=2000,lr=.05)
    assert np.linalg.norm(result['parameters']-truth) < .08


def test_manual_backprop_and_hessian_vector_against_finite_difference():
    a=module('track_a'); rng=np.random.default_rng(3)
    x=rng.normal(size=(6,2)); y=rng.normal(size=6); w=rng.normal(size=13)*.1
    loss, grad=a.nn_loss_grad(w,x,y,hidden=3,l2=.2)
    eps=1e-6
    numerical=np.array([(a.nn_loss_grad(w+np.eye(13)[i]*eps,x,y,3,.2)[0]-a.nn_loss_grad(w-np.eye(13)[i]*eps,x,y,3,.2)[0])/(2*eps) for i in range(13)])
    np.testing.assert_allclose(grad,numerical,atol=1e-7)
    c=a.curvature(seed=3)
    assert c['hvp_dense_max_error'] < 1e-10
    assert c['fisher_min_eigenvalue'] > -1e-10


def test_greedy_exact_and_diminishing_returns():
    d=module('track_d'); sets=[{0,1,2},{2,3},{3,4}]
    chosen,score=d.greedy_coverage(sets,2)
    assert score==5 and len(chosen)==2
    assert d.exact_coverage(sets,2)[1]==5
    assert d.check_diminishing_returns(sets)
    assert d.greedy_coverage(sets,0)==([],0)


def test_mgda_projects_conflicting_gradients():
    d=module('track_d')
    alpha,g=d.mgda(np.array([1.,0.]),np.array([-1.,0.]))
    assert alpha==pytest.approx(.5)
    np.testing.assert_allclose(g,[0.,0.],atol=1e-12)
    alpha,g=d.mgda(np.array([2.,0.]),np.array([1.,0.]))
    np.testing.assert_allclose(g,[1.,0.])


def test_one_local_step_fedavg_equals_centralized():
    d=module('track_d'); out=d.federated(seed=0,rounds=5,local_steps=1)
    assert out['one_step_equivalence_error'] < 1e-12
    assert out['fedavg_loss'] < out['initial_loss']


def test_process_schedulers_do_not_drop_or_duplicate_work():
    d=module('track_d'); out=d.scheduling(seed=0,quick=True)
    assert all(r['correct'] for r in out['schedulers'])
    assert all(r['seconds']>0 for r in out['schedulers'])


def test_parallel_decompositions_match_serial():
    d=module('track_d'); out=d.parallelism(seed=0,quick=True)
    assert all(r['max_abs_error'] < 1e-10 for r in out['modes'])


def test_nonlinear_gauss_newton_recovers_exponential_parameters():
    a=module('track_a')
    assert hasattr(a,'nonlinear_least_squares'), 'nonlinear curvature comparison missing'
    x=np.linspace(0,1,30); y=1.7*np.exp(-.8*x)
    for method in ('newton','gauss_newton'):
        out=a.nonlinear_least_squares(x,y,method)
        np.testing.assert_allclose(out['parameters'],[1.7,-.8],atol=1e-5)


def test_coverage_benchmark_retains_nonoptimal_greedy_example():
    d=module('track_d'); result=d.coverage(0)
    assert 'adversarial_example' in result
    assert result['adversarial_example']['greedy']==5
    assert result['adversarial_example']['optimum']==6
