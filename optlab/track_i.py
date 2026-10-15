"""Track I: explicit small quantum circuits and honest classical comparisons.

Wire 0 is the most significant bit. All execution is classical simulation.
"""
from fractions import Fraction
from math import gcd
from time import perf_counter
import numpy as np
from scipy.optimize import minimize

H = np.array([[1, 1], [1, -1]], dtype=complex) / np.sqrt(2)
X = np.array([[0, 1], [1, 0]], dtype=complex)
Z = np.diag([1, -1]).astype(complex)
CNOT = np.array([[1,0,0,0],[0,1,0,0],[0,0,0,1],[0,0,1,0]], complex)


def apply(state, gate, wires):
    """Apply an ordered k-wire unitary without a full-system matrix."""
    n = int(np.log2(len(state)))
    wires = list(wires)
    axes = wires + [j for j in range(n) if j not in wires]
    tensor = state.reshape([2]*n).transpose(axes).reshape(2**len(wires), -1)
    return (gate @ tensor).reshape([2]*n).transpose(np.argsort(axes)).reshape(-1)


def zero(n):
    state = np.zeros(2**n, complex); state[0] = 1
    return state


def ry(theta):
    return np.array([[np.cos(theta/2), -np.sin(theta/2)],
                     [np.sin(theta/2), np.cos(theta/2)]], complex)


def rz(theta):
    return np.diag(np.exp(np.array([-1j, 1j])*theta/2))


def qft_state(state, inverse=False):
    """Gate-by-gate H, controlled-phase and SWAP QFT, positive exponent."""
    n = int(np.log2(len(state)))
    operations = []
    for j in range(n):
        operations.append((H, [j]))
        for k in range(j+1, n):
            operations.append((np.diag([1,1,1,np.exp(1j*np.pi/2**(k-j))]), [k,j]))
    swap = np.array([[1,0,0,0],[0,0,1,0],[0,1,0,0],[0,0,0,1]], complex)
    operations.extend((swap, [j,n-j-1]) for j in range(n//2))
    for gate, wires in ([(g.conj().T,w) for g,w in operations[::-1]] if inverse else operations):
        state = apply(state, gate, wires)
    return state


def deutsch_jozsa(balanced=True, n=3):
    state = apply(zero(n+1), X, [n])
    for wire in range(n+1): state = apply(state, H, [wire])
    # f(x)=xor(x) is balanced; f(x)=0 is constant.
    if balanced:
        for wire in range(n): state = apply(state, CNOT, [wire,n])
    for wire in range(n): state = apply(state, H, [wire])
    probs = (abs(state)**2).reshape(-1,2).sum(axis=1)
    return {'balanced': balanced, 'zero_probability': float(probs[0]),
            'oracle_queries': 1, 'classical_deterministic_worst_queries': 2**(n-1)+1,
            'one_qubit_gates': 2*n+2, 'oracle_cnot_gates': n if balanced else 0}


def bernstein_vazirani(secret='101'):
    n = len(secret); state = apply(zero(n+1), X, [n])
    for wire in range(n+1): state = apply(state, H, [wire])
    for wire, bit in enumerate(secret):
        if bit == '1': state = apply(state, CNOT, [wire,n])
    for wire in range(n): state = apply(state, H, [wire])
    probs = (abs(state)**2).reshape(-1,2).sum(axis=1)
    return {'secret': secret, 'answer': format(int(probs.argmax()), f'0{n}b'),
            'success_probability': float(probs[int(secret,2)]), 'oracle_queries': 1,
            'classical_queries': n, 'oracle_cnot_gates': secret.count('1')}


def grover(n=3, marked=5):
    if not 0 <= marked < 2**n: raise ValueError('marked state outside register')
    state = zero(n)
    for j in range(n): state = apply(state, H, [j])
    iterations = max(1, int(np.floor(np.pi/4*np.sqrt(2**n))))
    zeros = n - marked.bit_count()
    for _ in range(iterations):
        # Exact marked-state phase oracle; equivalent X/MCZ/X gate circuit.
        state[marked] *= -1
        for j in range(n): state = apply(state,H,[j]); state = apply(state,X,[j])
        state[-1] *= -1
        for j in range(n): state = apply(state,X,[j]); state = apply(state,H,[j])
    probs = abs(state)**2
    return {'n':n,'marked':marked,'answer':int(probs.argmax()),
            'success_probability':float(probs[marked]), 'oracle_queries':iterations,
            'classical_expected_queries':(2**n+1)/2, 'classical_worst_queries':2**n,
            'one_qubit_gates':n+iterations*(2*zeros+4*n),
            'multi_controlled_z_gates':2*iterations,
            'gate_count_note':'MCZ treated as primitive; hardware decomposition/connectivity cost excluded'}



def linear_search(values, target):
    """Execute sequential equality comparisons; return the first matching index."""
    comparisons=0
    for index,value in enumerate(values):
        comparisons+=1
        if value==target:
            return {'index':index,'comparisons':comparisons}
    return {'index':None,'comparisons':comparisons}


def search_comparison(n=3, marked=5, repeats=9, batch_size=16):
    """Warm, batched wall-clock measurements of simulation and actual linear search."""
    if repeats<1 or batch_size<1: raise ValueError('positive timing budgets required')
    if not 0<=marked<2**n: raise ValueError('marked state outside register')
    # Multiplication by odd 5 permutes every power-of-two range: one unique target.
    values=[(5*index+3)%(2**n) for index in range(2**n)]
    target=values[marked]
    classical=lambda:linear_search(values,target)
    quantum=lambda:grover(n,marked)
    measured={}
    for name,operation in [('classical',classical),('quantum',quantum)]:
        operation(); operation()  # Warm interpreter/NumPy paths; exclude imports.
        samples=[]
        for _ in range(repeats):
            start=perf_counter()
            for _ in range(batch_size): result=operation()
            samples.append((perf_counter()-start)/batch_size)
        if name=='classical':
            result.update(timing_seconds=samples,median_seconds=float(np.median(samples)))
        else:
            result.update(simulator_timing_seconds=samples,simulator_median_seconds=float(np.median(samples)))
        measured[name]=result
    return {'n':n,'array':values,'target':target,'marked_index':marked,**measured,
            'timing_protocol':{'repeats':repeats,'calls_per_repeat':batch_size,'warmup_calls_per_method':2,
                               'statistic':'median of per-call batch averages; perf_counter wall time'},
            'query_count_scope':'quantum oracle_queries and logical gates are circuit counts; classical comparisons are executed and counted',
            'comparison_limits':'quantum wall time is classical statevector simulation including state preparation and exact probability readout; array/oracle construction excluded for both; oracle synthesis and qRAM excluded; quantum answer is modal state, with single-shot success probability reported separately'}


def phase_estimation(phase=3/8, bits=3):
    # Target |1> of diag(1, exp(2 pi i phase)); kickback explicitly simulated.
    state = apply(zero(bits+1), X, [bits])
    for j in range(bits):
        state = apply(state,H,[j])
        gate = np.diag([1,1,1,np.exp(2j*np.pi*phase*2**(bits-j-1))])
        state = apply(state,gate,[j,bits])
    tensor = state.reshape(2**bits,2)
    tensor = np.stack([qft_state(tensor[:,k], inverse=True) for k in range(2)],axis=1)
    probs = (abs(tensor)**2).sum(axis=1)
    return {'phase':float(probs.argmax()/2**bits),'target_phase':phase,
            'probabilities':probs.tolist(),'controlled_power_gates':bits}


def shor15(seed=0):
    """QPE of modular multiplication by 2 mod 15; no hardcoded order."""
    bits, work = 4, 4
    state = zero(bits+work); state[0]=0; state[1]=1
    for j in range(bits):
        state = apply(state,H,[j])
        multiplier = pow(2, 2**(bits-j-1), 15)
        permutation = np.zeros((16,16),complex)
        for x in range(16): permutation[(multiplier*x)%15 if x<15 else x,x]=1
        controlled = np.zeros((32,32),complex)
        controlled[:16,:16]=np.eye(16); controlled[16:,16:]=permutation
        state = apply(state,controlled,[j]+list(range(bits,bits+work)))
    tensor = state.reshape(16,16)
    tensor = np.stack([qft_state(tensor[:,x],inverse=True) for x in range(16)],axis=1)
    probs = (abs(tensor)**2).sum(axis=1); probs /= probs.sum()
    samples = np.random.default_rng(seed).choice(16, size=32, p=probs)
    order = None; used = []
    for sample in samples:
        used.append(int(sample))
        if sample == 0: continue
        denominator = Fraction(int(sample),16).limit_denominator(15).denominator
        # A measured phase may yield a divisor; verify small multiples classically.
        for candidate in range(denominator, 16, denominator):
            if pow(2,candidate,15)==1:
                order=candidate; break
        if order is not None: break
    factors = []
    if order is not None and order%2==0:
        factors=sorted(set(d for d in [gcd(pow(2,order//2)-1,15),gcd(pow(2,order//2)+1,15)] if 1<d<15))
    return {'number':15,'base':2,'order':order,'factors':factors,
            'phase_probabilities':probs.tolist(),'measured_integers':used,
            'qubits':8,'controlled_modular_multiplications':4,
            'implementation':'actual controlled modular permutation unitaries plus inverse QFT; dense toy gates, not scalable arithmetic compilation'}


def feature_states(x):
    states=[]
    for a,b in x:
        state=apply(zero(2),ry(a),[0]); state=apply(state,ry(b),[1])
        state=apply(state,CNOT,[0,1]); state=apply(state,rz(a*b),[1])
        states.append(state)
    return np.asarray(states)


def predictions(states, theta):
    # Batch simulation evaluates the same circuit for each input, not one QPU shot.
    out=states.copy()
    for layer in range(2):
        for wire in range(2):
            for gate in (ry(theta[4*layer+2*wire]),rz(theta[4*layer+2*wire+1])):
                matrix=np.kron(gate,np.eye(2)) if wire==0 else np.kron(np.eye(2),gate)
                out=out@matrix.T
        out=out@CNOT.T
    return (abs(out)**2)@np.array([1,1,-1,-1]) + theta[8]


def classification(seed=0, quick=False):
    from sklearn.datasets import make_moons
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import StandardScaler
    from sklearn.svm import SVC
    from sklearn.neural_network import MLPClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import accuracy_score
    x,y=make_moons(n_samples=72,noise=.16,random_state=seed)
    train,test=train_test_split(np.arange(len(y)),test_size=.25,stratify=y,random_state=seed)
    scaler=StandardScaler().fit(x[train]); x=scaler.transform(x)
    # Fixed pi/2 scale, fit only training standardization; no test-label tuning.
    x=x*np.pi/2
    started=perf_counter(); states=feature_states(x); embedding_time=perf_counter()-started
    target=2*y[train]-1; calls=0
    def objective(theta):
        nonlocal calls
        pred=predictions(states[train],theta); residual=pred-target
        calls+=len(train)
        gradient=np.zeros(9)
        for k in range(8):
            delta=np.zeros(9); delta[k]=np.pi/2
            derivative=(predictions(states[train],theta+delta)-predictions(states[train],theta-delta))/2
            calls+=2*len(train)
            gradient[k]=2*np.mean(residual*derivative)
        gradient[8]=2*residual.mean()
        return np.mean(residual**2),gradient
    initial=np.r_[np.random.default_rng(seed).normal(0,.4,8),0.]
    started=perf_counter()
    result=minimize(objective,initial,jac=True,method='L-BFGS-B',options={'maxiter':12 if quick else 60})
    prediction=predictions(states[test],result.x)>0; calls+=len(test)
    train_prediction=predictions(states[train],result.x)>0; calls+=len(train)
    models=[{'model':'variational_quantum_classifier','test_accuracy':float(accuracy_score(y[test],prediction)),
             'train_accuracy':float(accuracy_score(y[train],train_prediction)),
             'fit_predict_seconds':perf_counter()-started,'trainable_parameters':9,'circuit_executions':calls,
             'converged':bool(result.success),'iterations':int(result.nit),
             'gates_per_circuit':{'one_qubit':11,'cnot':3}}]
    started=perf_counter()
    kernel=abs(states[train].conj()@states[train].T)**2
    test_kernel=abs(states[test].conj()@states[train].T)**2
    svc=SVC(kernel='precomputed',C=1).fit(kernel,y[train]); prediction=svc.predict(test_kernel)
    models.append({'model':'quantum_fidelity_kernel_svm','test_accuracy':float(accuracy_score(y[test],prediction)),
                   'train_accuracy':float(svc.score(kernel,y[train])), 'fit_predict_seconds':perf_counter()-started,
                   'trainable_parameters':int(svc.dual_coef_.size+svc.intercept_.size),
                   'circuit_executions':len(x),'hardware_overlap_circuits':len(train)*(len(train)+1)//2+len(test)*len(train),
                   'circuit_count_note':'simulator caches feature states; hardware overlap circuit count reported separately'})
    for name,model in [('classical_rbf_svm',SVC(C=1)),('classical_logistic',LogisticRegression()),
                       ('classical_mlp_9_parameters',MLPClassifier(hidden_layer_sizes=(2,),solver='lbfgs',max_iter=1000,random_state=seed))]:
        started=perf_counter(); model.fit(x[train],y[train]); prediction=model.predict(x[test])
        parameters=(sum(a.size for a in model.coefs_)+sum(a.size for a in model.intercepts_)) if hasattr(model,'coefs_') else (model.dual_coef_.size+model.intercept_.size if hasattr(model,'dual_coef_') else model.coef_.size+model.intercept_.size)
        models.append({'model':name,'test_accuracy':float(accuracy_score(y[test],prediction)),
                       'train_accuracy':float(model.score(x[train],y[train])), 'fit_predict_seconds':perf_counter()-started,
                       'trainable_parameters':int(parameters),'circuit_executions':0})
    return {'seed':seed,'train_indices':train.tolist(),'test_indices':test.tolist(),'models':models,
            'embedding_seconds':embedding_time,'embedding':'two angle-encoded features, CNOT, feature-product RZ; no amplitude-loading oracle',
            'kernel_min_eigenvalue':float(np.linalg.eigvalsh(kernel).min()),
            'fairness':'same train/test rows and train-fitted scaler; fixed hyperparameters, no test selection; 9-parameter MLP matches VQC parameter count, function classes differ'}


def simulated_quantum_annealing(seed=0, quick=False):
    """Finite-temperature Suzuki-Trotter path-integral Monte Carlo (not QPU dynamics)."""
    rng=np.random.default_rng(seed); slices=16; beta=4.; n=4
    spins=rng.choice([-1,1],size=(slices,n)); sweeps=40 if quick else 200
    accepted=0; proposed=0
    started=perf_counter()
    for gamma in np.geomspace(3.,.02,sweeps):
        temporal=.5*np.log(1/np.tanh(beta*gamma/slices))
        for _ in range(slices*n):
            t=rng.integers(slices); j=rng.integers(n); s=spins[t,j]
            # H_problem=sum Z_i Z_j, antiferromagnetic cycle.
            delta=-2*beta/slices*s*(spins[t,(j-1)%n]+spins[t,(j+1)%n])+2*temporal*s*(spins[(t-1)%slices,j]+spins[(t+1)%slices,j])
            proposed+=1
            if delta<=0 or rng.random()<np.exp(-delta): spins[t,j]*=-1; accepted+=1
    cuts=np.sum(spins!=np.roll(spins,-1,axis=1),axis=1)
    return {'seed':seed,'best_cut':int(cuts.max()),'mean_slice_cut':float(cuts.mean()),
            'optimal_slice_fraction':float(np.mean(cuts==4)), 'slices':slices,'beta':beta,
            'sweeps':sweeps,'proposals':proposed,'accepted':accepted,'seconds':perf_counter()-started,
            'algorithm':'Suzuki-Trotter transverse-field Ising path-integral Metropolis; finite slices and sweeps'}



def classical_annealing(seed=0, proposals=12800):
    """Classical Ising Metropolis annealing with the same flip-proposal budget."""
    rng=np.random.default_rng(seed); spins=rng.choice([-1,1],size=4)
    best=int(np.sum(spins!=np.roll(spins,-1))); accepted=0; started=perf_counter()
    for temperature in np.geomspace(3.,.02,proposals):
        wire=rng.integers(4)
        delta=-2*spins[wire]*(spins[(wire-1)%4]+spins[(wire+1)%4])
        if delta<=0 or rng.random()<np.exp(-delta/temperature):
            spins[wire]*=-1; accepted+=1
        best=max(best,int(np.sum(spins!=np.roll(spins,-1))))
    return {'seed':seed,'cut':int(np.sum(spins!=np.roll(spins,-1))),'best_cut':best,
            'proposals':proposals,'accepted':accepted,'seconds':perf_counter()-started,
            'comparison':'same number of single-spin proposals; one classical replica versus 16 Trotter replicas, not equal mixing difficulty'}


def run(quick=False):
    seeds=range(1 if quick else 5); started=perf_counter()
    algorithms={'deutsch_jozsa':[deutsch_jozsa(False),deutsch_jozsa(True)],
                'bernstein_vazirani':bernstein_vazirani(), 'grover':[grover(n,2**n-1) for n in [2,3,4,5]],
                'search_comparison':[search_comparison(n,2**n-1,repeats=3 if quick else 9) for n in [2,3,4,5]],
                'qpe':phase_estimation(),'shor':[shor15(s) for s in seeds]}
    rng=np.random.default_rng(0); state=rng.normal(size=8)+1j*rng.normal(size=8); state/=np.linalg.norm(state)
    algorithms['qft']={'roundtrip_error':float(np.linalg.norm(qft_state(qft_state(state),True)-state)),
                       'qubits':3,'h_gates':3,'controlled_phase_gates':3,'swap_gates':1}
    classification_results=[classification(s,quick) for s in seeds]
    annealing=[simulated_quantum_annealing(s,quick) for s in seeds]
    return {'track':'I','description':'Executable quantum algorithms, variational/kernel classification and simulated quantum annealing',
            'measurements':{'algorithms':algorithms,'classification':classification_results,'annealing':annealing,'classical_annealing':[classical_annealing(s,2560 if quick else 12800) for s in seeds],'total_seconds':perf_counter()-started},
            'correctness':{'shor_factors_all_correct':all(x['factors']==[3,5] for x in algorithms['shor']),
                           'qft_roundtrip_pass':algorithms['qft']['roundtrip_error']<1e-10,
                           'search_indices_match':all(r['classical']['index']==r['quantum']['answer']==r['marked_index'] for r in algorithms['search_comparison']),
                           'bernstein_vazirani_pass':algorithms['bernstein_vazirani']['answer']=='101'},
            'limitations':['All algorithms use classical statevector simulation; no wall-clock quantum speedup is claimed.',
                           'Dense toy modular permutation gates do not establish scalable Shor arithmetic resources.',
                           'Oracle query comparisons exclude loading/oracle synthesis; MCZ gates are not decomposed into hardware primitives.',
                           'Classification uses a tiny synthetic dataset and exact expectations, with no hyperparameter search.',
                           'Annealing is classical path-integral Monte Carlo, not real-time coherent quantum annealing or hardware execution.',
                           'Only two real-valued features are encoded; larger data requires additional qubits, layers or costly state preparation.']}
