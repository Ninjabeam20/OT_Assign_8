"""Track C: reproducible small variational quantum optimization benchmarks."""
from time import perf_counter
import numpy as np
from scipy.optimize import minimize
from .track_i import apply, zero, H, X, Z, CNOT, ry, rz

EDGES = [(0,1),(1,2),(2,3),(3,0)]


def cut_values(n=4):
    if n != 4: raise ValueError('This benchmark fixes the four-cycle MaxCut instance')
    return np.array([sum(((x>>(n-a-1))&1)!=((x>>(n-b-1))&1) for a,b in EDGES) for x in range(2**n)])


def rx(theta):
    return np.cos(theta/2)*np.eye(2)-1j*np.sin(theta/2)*X


def qaoa_probabilities(theta):
    state=np.ones(16,complex)/4; costs=cut_values()
    for gamma,beta in np.asarray(theta).reshape(-1,2):
        state*=np.exp(-1j*gamma*costs)
        for wire in range(4): state=apply(state,rx(2*beta),[wire])
    return abs(state)**2


def qaoa(seed=0, quick=False):
    rng=np.random.default_rng(seed); costs=cut_values(); calls=0
    def objective(theta):
        nonlocal calls
        calls+=1
        return -float(qaoa_probabilities(theta)@costs)
    started=perf_counter(); candidates=[]
    for _ in range(2 if quick else 5):
        result=minimize(objective,rng.uniform(-1,1,4),method='BFGS',options={'maxiter':100,'gtol':1e-7})
        candidates.append(result)
    result=min(candidates,key=lambda r:r.fun); probs=qaoa_probabilities(result.x)
    sample=rng.choice(16,size=1024,p=probs/probs.sum())
    return {'seed':seed,'depth':2,'angles':result.x.tolist(),'expected_cut':float(probs@costs),
            'approximation_ratio':float(probs@costs/4),'optimal_probability':float(probs[costs==4].sum()),
            'sample_mean_cut':float(costs[sample].mean()),'shots':1024,'exact_optimum':4,
            'exact_optimal_bitstrings':['0101','1010'],'classical_enumerated_states':16,
            'objective_circuit_evaluations':calls,'seconds':perf_counter()-started,
            'logical_gates':{'initial_h':4,'zz_rotations':8,'rx':8},
            'optimizer':'multi-start BFGS, finite-difference derivatives; shared-angle QAOA does not use naive two-shift gradients',
            'optimizer_success':bool(result.success)}


def parameter_shift(objective, theta):
    """Valid when each coordinate occurs once in an exp(-i theta P/2) gate."""
    gradient=np.empty(len(theta))
    for j in range(len(theta)):
        delta=np.zeros(len(theta)); delta[j]=np.pi/2
        gradient[j]=(objective(theta+delta)-objective(theta-delta))/2
    return gradient


def vqe_state(theta):
    state=apply(zero(2),ry(theta[0]),[0]); state=apply(state,ry(theta[1]),[1])
    state=apply(state,CNOT,[0,1]); state=apply(state,ry(theta[2]),[0]); state=apply(state,ry(theta[3]),[1])
    return state


def quantum_metric(state_function, theta, epsilon=1e-5):
    """Fubini–Study pullback metric from finite-difference state derivatives."""
    state=state_function(theta); derivatives=[]
    for j in range(len(theta)):
        delta=np.zeros(len(theta)); delta[j]=epsilon
        derivatives.append((state_function(theta+delta)-state_function(theta-delta))/(2*epsilon))
    derivatives=np.array(derivatives)
    overlap=derivatives.conj()@state
    return np.real(derivatives.conj()@derivatives.T-np.outer(overlap,overlap.conj()))


def vqe(seed=0, steps=100):
    hamiltonian=np.kron(Z,np.eye(2))+np.kron(np.eye(2),Z)+.5*np.kron(X,X)
    calls=0
    def objective(theta):
        nonlocal calls
        calls+=1; state=vqe_state(theta)
        return float(np.vdot(state,hamiltonian@state).real)
    started=perf_counter(); initial=np.random.default_rng(seed).normal(0,.5,4)
    initial_energy=objective(initial)
    result=minimize(objective,initial,jac=lambda x:parameter_shift(objective,x),method='BFGS',options={'maxiter':steps,'gtol':1e-8})
    return {'seed':seed,'energy':float(result.fun),'initial_energy':initial_energy,
            'exact_energy':float(np.linalg.eigvalsh(hamiltonian).min()), 'parameters':result.x.tolist(),
            'circuit_evaluations':calls,'seconds':perf_counter()-started,'optimizer_success':bool(result.success),
            'hamiltonian':'Z0 + Z1 + 0.5 X0 X1','measurement_groups_per_energy':2}


def optimizer_comparison(seed=0, quick=False):
    ham=np.kron(Z,np.eye(2))+np.kron(np.eye(2),Z)+.5*np.kron(X,X)
    rng=np.random.default_rng(seed); initial=rng.normal(0,.5,4); steps=30 if quick else 120
    records=[]
    for method in ['parameter_shift_gradient','SPSA','quantum_natural_gradient']:
        theta=initial.copy(); calls=0; state_calls=0; history=[]; started=perf_counter()
        def objective(x):
            nonlocal calls
            calls+=1; psi=vqe_state(x)
            return float(np.vdot(psi,ham@psi).real)
        for k in range(steps):
            if method=='SPSA':
                delta=rng.choice([-1.,1.],len(theta)); ck=.12/(k+1)**.101
                grad=(objective(theta+ck*delta)-objective(theta-ck*delta))/(2*ck)*delta
                update=.2/(k+1)**.602*grad
            else:
                grad=parameter_shift(objective,theta)
                if method=='quantum_natural_gradient':
                    metric=quantum_metric(vqe_state,theta); state_calls+=2*len(theta)+1
                    update=.08*np.linalg.solve(metric+1e-3*np.eye(len(theta)),grad)
                    update*=min(1.,.4/max(np.linalg.norm(update),1e-15))
                else: update=.12*grad
            theta-=update; history.append(objective(theta))
        records.append({'method':method,'seed':seed,'initial_parameters':initial.tolist(),
                        'final_energy':history[-1],'exact_energy':float(np.linalg.eigvalsh(ham).min()),
                        'energy_trace':history,'steps':steps,'expectation_circuit_evaluations':calls,
                        'metric_statevector_evaluations':state_calls,'seconds':perf_counter()-started,
                        'metric_note':'full simulator state derivatives; hardware metric estimation would add measurement costs' if state_calls else None})
    return records


def noisy_qaoa_probabilities(theta, probability):
    """Independent single-qubit depolarization after every mixer layer.

    E(rho)=(1-p)rho+p/3*(XrhoX+YrhoY+ZrhoZ), exactly on density matrices.
    """
    rho=np.ones((16,16),complex)/16; costs=cut_values(); paulis=[X,np.array([[0,-1j],[1j,0]]),Z]
    def full(gate,wire):
        return np.column_stack([apply(np.eye(16,dtype=complex)[:,j],gate,[wire]) for j in range(16)])
    for gamma,beta in np.asarray(theta).reshape(-1,2):
        diagonal=np.exp(-1j*gamma*costs); rho=diagonal[:,None]*rho*diagonal.conj()[None,:]
        for wire in range(4):
            unitary=full(rx(2*beta),wire); rho=unitary@rho@unitary.conj().T
        for wire in range(4):
            original=rho.copy(); rho=(1-probability)*original
            for pauli in paulis:
                p=full(pauli,wire); rho+=probability/3*(p@original@p.conj().T)
    probs=np.maximum(0,np.diag(rho).real); return probs/probs.sum()


def shot_noise_study(theta, seed=0, quick=False):
    rng=np.random.default_rng(seed); costs=cut_values(); records=[]
    for noise in [0.,.01,.05,.1]:
        probs=noisy_qaoa_probabilities(theta,noise); exact=float(probs@costs)
        for shots in [128,1024,8192]:
            repetitions=8 if quick else 40
            estimates=np.array([costs[rng.choice(16,size=shots,p=probs)].mean() for _ in range(repetitions)])
            records.append({'depolarizing_probability':noise,'shots':shots,'repetitions':repetitions,
                            'exact_noisy_expectation':exact,'sample_mean':float(estimates.mean()),
                            'empirical_std':float(estimates.std(ddof=1)),
                            'theoretical_standard_error':float(np.sqrt(probs@(costs-exact)**2/shots)),
                            'rmse':float(np.sqrt(np.mean((estimates-exact)**2)))})
    return {'seed':seed,'noise_placement':'one local depolarizing channel per qubit after each QAOA mixer layer', 'records':records}


def pqc_regression(seed=0, quick=False):
    rng=np.random.default_rng(seed); x=np.linspace(-np.pi,np.pi,48)
    y=np.sin(x); permutation=rng.permutation(len(x)); train=permutation[:36]; test=permutation[36:]
    def model(theta, inputs):
        result=[]
        for v in inputs:
            psi=ry(theta[2])@rz(theta[1])@ry(theta[0])@ry(v)@np.array([1.,0.])
            result.append(float(np.vdot(psi,Z@psi).real))
        return np.array(result)
    calls=0
    def objective(theta):
        nonlocal calls
        pred=model(theta,x[train]); calls+=len(train); residual=pred-y[train]; grad=[]
        for j in range(3):
            delta=np.zeros(3); delta[j]=np.pi/2
            derivative=(model(theta+delta,x[train])-model(theta-delta,x[train]))/2
            calls+=2*len(train); grad.append(2*np.mean(residual*derivative))
        return np.mean(residual**2),np.array(grad)
    started=perf_counter(); result=minimize(objective,rng.normal(size=3),jac=True,method='BFGS',options={'maxiter':20 if quick else 80})
    train_mse=float(np.mean((model(result.x,x[train])-y[train])**2)); test_mse=float(np.mean((model(result.x,x[test])-y[test])**2)); calls+=48
    # Same three coefficients, a basis baseline with matching periodic knowledge.
    design=np.column_stack([np.ones(48),np.sin(x),np.cos(x)])
    weights=np.linalg.lstsq(design[train],y[train],rcond=None)[0]
    return {'seed':seed,'qubits':1,'trainable_parameters':3,'train_mse':train_mse,'test_mse':test_mse,
            'classical_three_parameter_fourier_test_mse':float(np.mean((design[test]@weights-y[test])**2)),
            'circuit_evaluations':calls,'seconds':perf_counter()-started,'train_indices':train.tolist(),'test_indices':test.tolist(),
            'interpretation':'PQC/QNN regression on sin(x), a circuit-compatible function; Fourier regression is an equally informed baseline'}


def gradient_variance(seed=0, quick=False):
    rng=np.random.default_rng(seed); records=[]
    for n in [2,4,6,8]:
        depth=n; repetitions=8 if quick else 40; local=[]; global_cost=[]
        labels=np.arange(2**n); local_sign=1-2*((labels>>(n-1))&1)
        global_sign=np.array([(-1)**int(k).bit_count() for k in labels])
        def expectations(theta):
            state=zero(n)
            for layer in range(depth):
                for wire in range(n):
                    state=apply(state,ry(theta[layer,wire,0]),[wire]); state=apply(state,rz(theta[layer,wire,1]),[wire])
                for wire in range(n-1): state=apply(state,CNOT,[wire,wire+1])
            probs=abs(state)**2
            return np.array([probs@local_sign,probs@global_sign])
        started=perf_counter()
        for _ in range(repetitions):
            theta=rng.uniform(-np.pi,np.pi,size=(depth,n,2)); delta=np.zeros_like(theta); delta[0,0,0]=np.pi/2
            grad=(expectations(theta+delta)-expectations(theta-delta))/2
            local.append(float(grad[0])); global_cost.append(float(grad[1]))
        records.append({'qubits':n,'depth':depth,'parameters':2*n*depth,'random_initializations':repetitions,
                        'local_gradient_variance':float(np.var(local,ddof=1)), 'global_gradient_variance':float(np.var(global_cost,ddof=1)),
                        'local_gradients':local,'global_gradients':global_cost,'seconds':perf_counter()-started,
                        'statevector_complex128_bytes':16*2**n})
    return {'seed':seed,'records':records,'scope':'finite-size gradient concentration probe; growing both size and depth confounds causal attribution; not proof of a barren plateau'}


def run(quick=False):
    seeds=range(1 if quick else 5); started=perf_counter(); qaoa_results=[qaoa(s,quick) for s in seeds]
    vqe_results=[vqe(s,60 if quick else 100) for s in seeds]
    regressions=[pqc_regression(s,quick) for s in seeds]
    return {'track':'C','description':'QAOA MaxCut, VQE, PQC/QNN regression, three gradient optimizers, finite shots/noise and gradient concentration',
            'measurements':{'qaoa':qaoa_results,'vqe':vqe_results,'optimizers':[optimizer_comparison(s,quick) for s in seeds],
                            'pqc_qnn_regression':regressions,'shot_noise':[shot_noise_study(q['angles'],q['seed'],quick) for q in qaoa_results],
                            'gradient_variance':[gradient_variance(s,quick) for s in seeds], 'total_seconds':perf_counter()-started},
            'correctness':{'qaoa_within_exact_bound':all(q['expected_cut']<=4+1e-9 for q in qaoa_results),
                           'vqe_ground_state_errors':[abs(v['energy']-v['exact_energy']) for v in vqe_results],
                           'vqe_matches_exact':all(abs(v['energy']-v['exact_energy'])<1e-4 for v in vqe_results)},
            'limitations':['All timings are classical NumPy simulation; no quantum speed advantage or hardware run is claimed.',
                           'Exact enumeration of 16 states beats the purpose of QAOA here; this is a correctness benchmark.',
                           'QNG obtains the Fubini–Study metric from statevector derivatives, which are not directly available on hardware.',
                           'Depolarization is a simplified local layer noise model; calibration drift, readout error and device topology are excluded.',
                           'Noise studies evaluate clean-optimized angles rather than reoptimizing a noisy objective.',
                           'Two to eight qubits with increasing depth cannot prove asymptotic barren-plateau scaling.']}
