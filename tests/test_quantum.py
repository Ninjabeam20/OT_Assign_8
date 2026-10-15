"""Independent fixtures catch wire-order, phase, optimizer and leakage errors."""
import importlib
import numpy as np
import pytest


def module(name):
    spec = importlib.util.find_spec('optlab.' + name)
    assert spec is not None, 'quantum track implementation is missing'
    return importlib.import_module('optlab.' + name)


def test_oracles_recover_hand_checked_answers():
    i = module('track_i')
    assert i.deutsch_jozsa(False)['zero_probability'] == pytest.approx(1)
    assert i.deutsch_jozsa(True)['zero_probability'] == pytest.approx(0, abs=1e-12)
    assert i.bernstein_vazirani('101')['answer'] == '101'
    assert i.bernstein_vazirani('010')['answer'] == '010'


def test_qft_matches_positive_fourier_and_inverse():
    i = module('track_i')
    x = np.zeros(8, dtype=complex); x[1] = 1
    transformed = i.qft_state(x)
    assert np.allclose(transformed, np.exp(2j*np.pi*np.arange(8)/8)/np.sqrt(8))
    assert np.allclose(i.qft_state(transformed, inverse=True), x)


def test_phase_estimation_and_actual_modular_order_finding():
    i = module('track_i')
    assert i.phase_estimation(3/8, 3)['phase'] == pytest.approx(3/8)
    result = i.shor15(0)
    assert result['factors'] == [3, 5]
    assert result['order'] == 4
    assert np.allclose(result['phase_probabilities'], [.25,0,0,0,.25,0,0,0,.25,0,0,0,.25,0,0,0], atol=1e-10)


def test_grover_amplifies_marked_state_and_counts_queries():
    result = module('track_i').grover(3, 5)
    assert result['success_probability'] > .94
    assert result['oracle_queries'] == 2
    assert result['answer'] == 5


def test_maxcut_and_gradients_have_independent_references():
    c = module('track_c')
    assert c.cut_values(4).tolist() == [0,2,2,2,2,4,2,2,2,2,4,2,2,2,2,0]
    objective = lambda x: np.cos(x[0]) + .5*np.sin(x[1])
    x = np.array([.3, -.7])
    assert np.allclose(c.parameter_shift(objective, x), [-np.sin(.3), .5*np.cos(-.7)])
    assert np.allclose(c.qaoa_probabilities(np.zeros(4)), np.ones(16)/16)


def test_vqe_reaches_exact_ground_state_and_metric_psd():
    c = module('track_c')
    result = c.vqe(0, steps=100)
    assert abs(result['energy'] - result['exact_energy']) < 1e-4
    metric = c.quantum_metric(c.vqe_state, np.array([.2,.3,.4,.5]))
    assert np.allclose(metric, metric.T)
    assert np.linalg.eigvalsh(metric).min() > -1e-8


def test_classifier_split_and_kernel_psd():
    i = module('track_i')
    result = i.classification(0, quick=True)
    assert not set(result['train_indices']) & set(result['test_indices'])
    assert result['kernel_min_eigenvalue'] > -1e-8
    assert all(0 <= model['test_accuracy'] <= 1 for model in result['models'])
    assert result['models'][0]['circuit_executions'] > 0


def test_noise_channel_preserves_distribution_and_zero_noise_limit():
    c=module('track_c')
    theta=np.array([.31,.62,-.23,.87])
    clean=c.qaoa_probabilities(theta)
    assert np.allclose(c.noisy_qaoa_probabilities(theta,0),clean,atol=1e-12)
    depolarized=c.noisy_qaoa_probabilities(theta,.75)
    assert np.allclose(depolarized,np.ones(16)/16,atol=1e-12)


def test_annealing_returns_feasible_cut_and_resource_counts():
    result=module('track_i').simulated_quantum_annealing(0,quick=True)
    assert result['best_cut'] in [0,2,4]
    assert 0 <= result['optimal_slice_fraction'] <= 1
    assert result['proposals'] == result['slices']*4*result['sweeps']


def test_qaoa_optimization_reaches_cycle_optimum():
    result=module('track_c').qaoa(0,quick=True)
    assert result['expected_cut'] > 3.99
    assert result['optimal_probability'] > .99


def test_classical_annealing_produces_valid_solution_under_same_proposal_budget():
    i=module('track_i')
    assert hasattr(i,'classical_annealing'), 'matching classical annealing baseline is missing'
    result=i.classical_annealing(0,proposals=2560)
    assert result['cut'] in [0,2,4]
    assert result['best_cut'] == 4
    assert result['proposals'] == 2560


def test_linear_search_executes_comparisons_for_actual_target_position():
    i=module('track_i')
    assert hasattr(i,'linear_search'), 'executable classical search baseline is missing'
    assert i.linear_search([11,4,9,2],9) == {'index':2,'comparisons':3}
    assert i.linear_search([11,4,9,2],11) == {'index':0,'comparisons':1}
    assert i.linear_search([11,4,9,2],7) == {'index':None,'comparisons':4}


def test_grover_search_comparison_uses_same_target_and_records_wall_time():
    i=module('track_i')
    assert hasattr(i,'search_comparison'), 'measured search comparison is missing'
    result=i.search_comparison(3,5,repeats=3)
    assert result['classical']['index'] == result['quantum']['answer'] == 5
    assert result['classical']['comparisons'] == 6
    assert result['quantum']['oracle_queries'] == 2
    assert len(result['classical']['timing_seconds']) == len(result['quantum']['simulator_timing_seconds']) == 3
    assert result['classical']['median_seconds'] > 0
    assert result['quantum']['simulator_median_seconds'] > 0
