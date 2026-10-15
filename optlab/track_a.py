"""Track A: transparent first/second-order optimization and curvature experiments."""
from time import perf_counter
import numpy as np

METHODS = ('gd','sgd','minibatch','momentum','nag','adagrad','rmsprop','adam','newton','gauss_newton')


def optimize_least_squares(x, y, method='gd', seed=0, steps=300, lr=.05, l2=0.):
    """Minimize mean squared residual / 2 + l2 * ||w||² / 2.

    SGD draws one observation, minibatch draws eight; other methods use the
    full deterministic gradient. NAG evaluates at the momentum lookahead.
    Gauss-Newton equals Newton for this linear residual model (documented).
    """
    rng=np.random.default_rng(seed); w=np.zeros(x.shape[1]); velocity=w.copy()
    first=w.copy(); second=w.copy(); history=[]; samples=0
    start=perf_counter()
    for t in range(1,steps+1):
        n=1 if method=='sgd' else min(8,len(x)) if method=='minibatch' else len(x)
        indices=rng.choice(len(x),n,replace=False) if n<len(x) else np.arange(len(x))
        xb,yb=x[indices],y[indices]; samples+=n
        point=w+.9*velocity if method=='nag' else w
        g=xb.T@(xb@point-yb)/n+l2*point
        if method in ('gd','sgd','minibatch'): w-=lr*g
        elif method in ('momentum','nag'):
            velocity=.9*velocity-lr*g; w+=velocity
        elif method=='adagrad':
            second+=g*g; w-=lr*g/(np.sqrt(second)+1e-8)
        elif method=='rmsprop':
            second=.9*second+.1*g*g; w-=lr*g/(np.sqrt(second)+1e-8)
        elif method=='adam':
            first=.9*first+.1*g; second=.999*second+.001*g*g
            w-=lr*(first/(1-.9**t))/(np.sqrt(second/(1-.999**t))+1e-8)
        elif method in ('newton','gauss_newton'):
            h=xb.T@xb/n+l2*np.eye(len(w)); w-=np.linalg.solve(h+1e-9*np.eye(len(w)),g)
        else: raise ValueError(method)
        if t==1 or t%max(1,steps//20)==0:
            history.append({'step':t,'objective':float(.5*np.mean((x@w-y)**2)+.5*l2*(w@w))})
    return {'parameters':w,'objective':float(.5*np.mean((x@w-y)**2)+.5*l2*(w@w)),
            'seconds':perf_counter()-start,'sample_gradient_evaluations':samples,'trace':history}


def nonlinear_least_squares(x,y,method='gauss_newton',steps=50):
    """Fit a*exp(b*x); true Hessian includes residual second derivatives."""
    w=np.array([1.,-.2]); history=[]; start=perf_counter()
    for _ in range(steps):
        a,b=w; e=np.exp(b*x); residual=a*e-y
        jac=np.column_stack([e,a*x*e]); g=jac.T@residual/len(x)
        h=jac.T@jac/len(x)
        if method=='newton':
            h+=np.array([[0.,np.mean(residual*x*e)],
                         [np.mean(residual*x*e),np.mean(residual*a*x*x*e)]])
        elif method!='gauss_newton': raise ValueError(method)
        # Modified Newton makes indefinite Hessians positive definite.
        damping=max(1e-9,1e-6-float(np.linalg.eigvalsh(h).min()))
        direction=np.linalg.solve(h+damping*np.eye(2),g)
        old=.5*np.mean(residual**2); scale=1.
        for _ in range(40):
            trial=w-scale*direction
            with np.errstate(over='ignore',invalid='ignore'):
                new=.5*np.mean((trial[0]*np.exp(trial[1]*x)-y)**2)
            if np.isfinite(new) and new<=old-1e-4*scale*(g@direction): break
            scale*=.5
        w=trial; history.append(float(new))
        if np.linalg.norm(g)<1e-10: break
    return {'parameters':w.tolist(),'objective':history[-1],'trace':history,'seconds':perf_counter()-start}


def nn_loss_grad(w,x,y,hidden=8,l2=0.):
    """One tanh hidden layer; manually derived backprop, independent of optimizer."""
    d=x.shape[1]; cut=d*hidden
    w1=w[:cut].reshape(d,hidden); b1=w[cut:cut+hidden]
    w2=w[cut+hidden:cut+2*hidden]; b2=w[-1]
    h=np.tanh(x@w1+b1); prediction=h@w2+b2; residual=prediction-y
    loss=.5*np.mean(residual**2)+.5*l2*(w@w)
    dy=residual/len(x); dh=dy[:,None]*w2[None,:]*(1-h*h)
    grad=np.concatenate([(x.T@dh).ravel(),dh.sum(0),h.T@dy,[dy.sum()]])+l2*w
    return float(loss),grad


def neural_network(seed=0,quick=False):
    rng=np.random.default_rng(seed); x=rng.uniform(-2,2,(200,2))
    y=np.sin(x[:,0])+x[:,1]**2*.2+rng.normal(0,.15,len(x))
    split=120; initial=rng.normal(0,.2,33); rows=[]
    for optimizer in ('gd','adam'):
        for l2 in (0.,.01):
            w=initial.copy(); m=np.zeros_like(w); v=m.copy(); start=perf_counter()
            for t in range(1,(150 if quick else 600)+1):
                _,g=nn_loss_grad(w,x[:split],y[:split],8,l2)
                if optimizer=='gd': w-=.05*g
                else:
                    m=.9*m+.1*g; v=.999*v+.001*g*g
                    w-=.015*(m/(1-.9**t))/(np.sqrt(v/(1-.999**t))+1e-8)
            rows.append({'optimizer':optimizer,'l2':l2,'train_mse':2*nn_loss_grad(w,x[:split],y[:split])[0],
                         'test_mse':2*nn_loss_grad(w,x[split:],y[split:])[0],
                         'weight_norm':float(np.linalg.norm(w)),'seconds':perf_counter()-start})
    # Independent central finite-difference check of the manually implemented backprop.
    w=initial; _,g=nn_loss_grad(w,x[:7],y[:7],8,.01); eps=1e-6
    numeric=np.array([(nn_loss_grad(w+eps*e,x[:7],y[:7],8,.01)[0]-nn_loss_grad(w-eps*e,x[:7],y[:7],8,.01)[0])/(2*eps) for e in np.eye(len(w))])
    return {'runs':rows,'backprop_max_error':float(np.max(np.abs(g-numeric))),
            'distinction':'Backprop computes derivatives; GD/Adam consume those derivatives to update parameters.'}


def curvature(seed=0):
    rng=np.random.default_rng(seed); x=rng.normal(size=(160,12)); w=rng.normal(size=12)*.2
    p=1/(1+np.exp(-x@w)); q=p*(1-p)
    h=x.T@(q[:,None]*x)/len(x); v=rng.normal(size=12)
    hv=x.T@(q*(x@v))/len(x); eigen,u=np.linalg.eigh(h); rank=3
    low=(u[:,-rank:]*eigen[-rank:])@u[:,-rank:].T
    # Expected Fisher for Bernoulli logistic regression equals its loss Hessian.
    # Empirical Fisher uses sampled labels and generally does not equal Hessian.
    y=rng.binomial(1,p); per_example=(p-y)[:,None]*x
    empirical=per_example.T@per_example/len(x)
    diag=np.diag(np.diag(h)); damping=.01; g=x.T@(p-y)/len(x)
    direction=np.linalg.solve(h+damping*np.eye(12),g)
    return {'hvp_dense_max_error':float(np.max(np.abs(hv-h@v))),
            'fisher_min_eigenvalue':float(eigen.min()),'condition_number':float(eigen.max()/eigen.min()),
            'diagonal_relative_frobenius_error':float(np.linalg.norm(h-diag)/np.linalg.norm(h)),
            'rank3_relative_frobenius_error':float(np.linalg.norm(h-low)/np.linalg.norm(h)),
            'empirical_fisher_hessian_relative_difference':float(np.linalg.norm(empirical-h)/np.linalg.norm(h)),
            'natural_gradient_norm':float(np.linalg.norm(direction)),
            'dense_storage_scalars':144,'diagonal_storage_scalars':12,'rank3_storage_scalars':39,
            'hvp_operator':'v -> X.T @ (p*(1-p)*(X@v)) / n; no Hessian allocated by this operator'}


def nonconvex(seed=0,quick=False):
    """Tilted double well has two local minima; 2-D origin is an exact saddle at zero tilt."""
    rng=np.random.default_rng(seed); rows=[]
    for tilt in (0.,.15):
        for start_x in (-1.5,0.,1.5):
            for noise in (0.,.03):
                w=np.array([start_x,0.]); start=w.copy()
                for _ in range(300 if quick else 1000):
                    g=np.array([4*w[0]*(w[0]**2-1)+tilt,2*w[1]])
                    w-=.03*(g+rng.normal(0,noise,2))
                eig=[12*w[0]**2-4,2.]
                rows.append({'tilt':tilt,'initial':start.tolist(),'gradient_noise_std':noise,
                    'parameters':w.tolist(),'objective':float((w[0]**2-1)**2+w[1]**2+tilt*w[0]),
                    'gradient_norm':float(np.linalg.norm([4*w[0]*(w[0]**2-1)+tilt,2*w[1]])),
                    'min_hessian_eigenvalue':float(min(eig)),
                    'classification':'saddle' if min(eig)<0 else 'local minimum neighborhood'})
    return rows


def run(quick=False):
    rows=[]; tuning=[]; noise_rows=[]; nns=[]; curves=[]; wells=[]; nonlinear=[]
    seeds=range(1 if quick else 5)
    for seed in seeds:
        rng=np.random.default_rng(seed); x=rng.normal(size=(160,8)); truth=rng.normal(size=8)
        y=x@truth+rng.normal(0,.1,len(x)); rank_def=x.copy(); rank_def[:,-1]=rank_def[:,0]
        for landscape,xx in [('strongly_convex',x),('convex_rank_deficient',rank_def)]:
            yy=xx@truth+(y-x@truth); reference=np.linalg.lstsq(xx,yy,rcond=None)[0]
            optimum=.5*np.mean((xx@reference-yy)**2)
            for method in METHODS:
                out=optimize_least_squares(xx,yy,method,seed,150 if quick else 600,.05)
                out.pop('parameters'); rows.append({'seed':seed,'landscape':landscape,'optimizer':method,
                    'reference_objective':float(optimum),'optimality_gap':out['objective']-float(optimum),**out})
        # Tune on a held-out validation set, then evaluate once on separate test data.
        xv=rng.normal(size=(80,8)); yv=xv@truth+rng.normal(0,.1,80)
        xt=rng.normal(size=(80,8)); yt=xt@truth+rng.normal(0,.1,80)
        candidates=[]
        for lr in (.001,.01,.05,.2,.8,2.):
            with np.errstate(over='ignore',invalid='ignore'):
                out=optimize_least_squares(x,y,'gd',seed,150,lr)
                val=float(np.mean((xv@out['parameters']-yv)**2))
            candidates.append((val if np.isfinite(val) else float('inf'),lr,out['parameters']))
        best=min(candidates,key=lambda z:z[0])
        tuning.append({'seed':seed,'candidates':[{'lr':lr,'validation_mse':v if np.isfinite(v) else None} for v,lr,_ in candidates],
                       'chosen_lr':best[1],'test_mse':float(np.mean((xt@best[2]-yt)**2))})
        for noise in (0.,.5,2.):
            yn=x@truth+rng.normal(0,noise,len(x))
            for method in ('gd','sgd','minibatch'):
                out=optimize_least_squares(x,yn,method,seed,300,.03)
                noise_rows.append({'seed':seed,'label_noise_std':noise,'method':method,'parameter_error':float(np.linalg.norm(out['parameters']-truth)),'objective':out['objective']})
        xx=np.linspace(0,1,60); yy=1.7*np.exp(-.8*xx)+rng.normal(0,.01,60)
        for method in ('newton','gauss_newton'):
            nonlinear.append({'seed':seed,'method':method,**nonlinear_least_squares(xx,yy,method)})
        nns.append({'seed':seed,**neural_network(seed,quick)}); curves.append({'seed':seed,**curvature(seed)})
        wells.append({'seed':seed,'experiments':nonconvex(seed,quick)})
    return {'track':'A','description':'First-order, Newton/Gauss-Newton, nonconvex geometry, manual neural-network backprop and curvature.',
            'measurements':{'optimizers':rows,'step_size_tuning':tuning,'noise':noise_rows,'neural_network':nns,'curvature':curves,'nonconvex':wells,'nonlinear_least_squares':nonlinear},
            'correctness':{'backprop_max_error':max(x['backprop_max_error'] for x in nns),'hvp_max_error':max(x['hvp_dense_max_error'] for x in curves),
                           'least_squares_reference':'numpy.linalg.lstsq; objective gaps tolerate roundoff'},
            'limitations':['Synthetic small problems; no universal optimizer ranking.','Gauss-Newton and Newton coincide on linear least squares; separate nonlinear exponential fits use distinct Hessians and safeguarded line search.',
                           'Full-batch adaptive methods use fixed step sizes and may plateau; traces retain that behavior.',
                           'Fisher equality is for expected Bernoulli logistic Fisher; empirical Fisher is separately reported.',
                           'Noise and regularization demonstrations do not establish generalization guarantees.']}
