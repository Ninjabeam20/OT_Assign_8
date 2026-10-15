"""Track D: submodularity, real process parallelism, federation and multitask training."""
import itertools
import math
import multiprocessing as mp
import os
from concurrent.futures import ProcessPoolExecutor
from time import perf_counter
import numpy as np


def greedy_coverage(sets,k):
    selected=[]; covered=set()
    for _ in range(min(k,len(sets))):
        remaining=[i for i in range(len(sets)) if i not in selected]
        best=max(remaining,key=lambda i:len(sets[i]-covered))
        selected.append(best); covered|=sets[best]
    return selected,len(covered)


def exact_coverage(sets,k):
    candidates=itertools.combinations(range(len(sets)),min(k,len(sets)))
    chosen=max(candidates,key=lambda c:len(set().union(*(sets[i] for i in c))))
    return list(chosen),len(set().union(*(sets[i] for i in chosen)))


def check_diminishing_returns(sets):
    """Exhaustively check A subset B and e outside B for small ground sets."""
    n=len(sets)
    for mask in range(1<<n):
        b={i for i in range(n) if mask>>i&1}; cb=set().union(*(sets[i] for i in b))
        sub=mask
        while True:
            a={i for i in range(n) if sub>>i&1}; ca=set().union(*(sets[i] for i in a))
            for e in set(range(n))-b:
                if len(sets[e]-ca)<len(sets[e]-cb): return False
            if sub==0: break
            sub=(sub-1)&mask
    return True


def coverage(seed):
    rng=np.random.default_rng(seed); sets=[set(np.flatnonzero(rng.random(24)<.25).tolist()) for _ in range(8)]
    rows=[]
    for k in (1,2,3,4):
        start=perf_counter(); chosen,greedy=greedy_coverage(sets,k); gt=perf_counter()-start
        start=perf_counter(); exact_set,exact=exact_coverage(sets,k); et=perf_counter()-start
        rows.append({'k':k,'greedy':greedy,'optimum':exact,'chosen':chosen,'optimal_chosen':exact_set,
                     'ratio':greedy/exact if exact else 1.,'bound':1-(1-1/k)**k,'greedy_seconds':gt,'exact_seconds':et,
                     'guarantee_satisfied':greedy+1e-10 >= (1-1/math.e)*exact})
    return {'seed':seed,'diminishing_returns_exhaustive':check_diminishing_returns(sets),'runs':rows,
            'adversarial_example':{'sets':[[0,1,2,3],[0,1,4],[2,3,5]],'k':2,
                'greedy':greedy_coverage([{0,1,2,3},{0,1,4},{2,3,5}],2)[1],
                'optimum':exact_coverage([{0,1,2,3},{0,1,4},{2,3,5}],2)[1],
                'explanation':'Greedy takes the four-element set first; the other two sets together cover all six.'}}


def _cpu_job(task):
    index,n=task; value=0
    for i in range(n): value=(value+(i*i+31*i)%100003)%1000000007
    return index,value


def _static_chunk(tasks): return [_cpu_job(t) for t in tasks]


def _steal_worker(worker,queues,lock):
    """Local LIFO pop; steal FIFO from peer. Manager calls make IPC explicit."""
    output=[]; steals=0; acquisitions=0
    while True:
        task=None
        with lock:
            acquisitions+=1
            if len(queues[worker]): task=queues[worker].pop()
            else:
                for peer in range(len(queues)):
                    if peer!=worker and len(queues[peer]):
                        task=queues[peer].pop(0); steals+=1; break
        if task is None: break
        output.append(_cpu_job(task))
    return output,steals,acquisitions


def scheduling(seed=0,quick=False):
    workers=min(2,os.cpu_count() or 1); base=6000 if quick else 45000
    # Cluster heavy jobs in the first static chunk to expose load imbalance.
    tasks=[(i,base*(8 if i<4 else 1)) for i in range(16)]
    start=perf_counter(); expected=[_cpu_job(t) for t in tasks]; serial=perf_counter()-start
    chunks=[tasks[i*8:(i+1)*8] for i in range(workers)] if workers==2 else [tasks]
    rows=[]; context=mp.get_context('spawn')
    for mode in ('static','dynamic','work_stealing'):
        start=perf_counter(); steals=0; locks=0
        if mode=='work_stealing':
            with context.Manager() as manager:
                queues=[manager.list(c) for c in chunks]; lock=manager.Lock()
                with ProcessPoolExecutor(workers,mp_context=context) as pool:
                    answers=[f.result() for f in [pool.submit(_steal_worker,i,queues,lock) for i in range(workers)]]
                result=[item for answer,_,_ in answers for item in answer]
                steals=sum(a[1] for a in answers); locks=sum(a[2] for a in answers)
        else:
            with ProcessPoolExecutor(workers,mp_context=context) as pool:
                if mode=='static': result=[r for chunk in pool.map(_static_chunk,chunks) for r in chunk]
                else: result=list(pool.map(_cpu_job,tasks,chunksize=1))
        elapsed=perf_counter()-start; speedup=serial/elapsed
        rows.append({'mode':mode,'seconds':elapsed,'speedup':speedup,'efficiency':speedup/workers,
                     'correct':sorted(result)==expected,'steals':steals,'lock_acquisitions':locks,
                     'task_payload_bytes_lower_bound':len(tasks)*16,
                     'amdahl_effective_serial_fraction':(1/speedup-1/workers)/(1-1/workers) if workers>1 else None})
    # Quantify locality with identical reductions over contiguous vs strided arrays.
    array=np.arange(512*512,dtype=np.float64).reshape(512,512); locality=[]
    for label,data in [('contiguous',array),('strided_transpose',array.T)]:
        start=perf_counter(); checksum=0.
        for _ in range(3):
            for row in data: checksum+=float(np.sum(row))
        locality.append({'layout':label,'seconds':perf_counter()-start,'checksum':checksum})
    return {'seed':seed,'workers':workers,'serial_seconds':serial,'schedulers':rows,'locality':locality,
            'scaling_predictions':[{'assumed_serial_fraction':s,'amdahl':1/(s+(1-s)/workers),
                                   'gustafson':workers-s*(workers-1)} for s in (.05,.2,.5)],
            'timing_scope':'End-to-end includes spawn, serialization, scheduler and shutdown. Effective serial fraction >1 means overhead violates ideal Amdahl model.'}


def _matmul(args):
    a,b=args
    return a@b


def _pipeline_stage(input_queue,output_queue,weight,nonlinear):
    while True:
        message=input_queue.get()
        if message is None: output_queue.put(None); return
        i,x=message; y=x@weight
        output_queue.put((i,np.tanh(y) if nonlinear else y))


def parallelism(seed=0,quick=False):
    rng=np.random.default_rng(seed); n=128 if quick else 512; d=32
    x=rng.normal(size=(n,d)); w=rng.normal(size=(d,d)); v=rng.normal(size=(d,8)); workers=2
    context=mp.get_context('spawn'); rows=[]
    start=perf_counter(); reference=x@w; serial=perf_counter()-start
    for mode in ('data','model'):
        start=perf_counter()
        with ProcessPoolExecutor(workers,mp_context=context) as pool:
            if mode=='data':
                results=list(pool.map(_matmul,[(part,w) for part in np.array_split(x,workers)])); answer=np.concatenate(results,axis=0)
            else:
                results=list(pool.map(_matmul,[(x,part) for part in np.array_split(w,workers,axis=1)])); answer=np.concatenate(results,axis=1)
        elapsed=perf_counter()-start
        rows.append({'mode':mode,'seconds':elapsed,'serial_seconds':serial,'speedup':serial/elapsed,'efficiency':serial/elapsed/workers,
                     'max_abs_error':float(np.max(np.abs(answer-reference))),
                     'input_communication_bytes':int(x.nbytes+w.nbytes*workers if mode=='data' else x.nbytes*workers+w.nbytes)})
    start=perf_counter(); reference=np.tanh(x@w)@v; serial_pipeline=perf_counter()-start
    start=perf_counter(); queues=[context.Queue() for _ in range(3)]
    processes=[context.Process(target=_pipeline_stage,args=(queues[0],queues[1],w,True)),
               context.Process(target=_pipeline_stage,args=(queues[1],queues[2],v,False))]
    for p in processes: p.start()
    batches=np.array_split(x,8)
    for i,batch in enumerate(batches): queues[0].put((i,batch))
    queues[0].put(None); outputs=[]
    while True:
        item=queues[2].get(timeout=60)
        if item is None: break
        outputs.append(item)
    for p in processes:
        p.join(timeout=60)
        if p.exitcode!=0: raise RuntimeError(f'pipeline worker exit {p.exitcode}')
    for q in queues: q.close(); q.join_thread()
    answer=np.concatenate([r for _,r in sorted(outputs)]); elapsed=perf_counter()-start
    rows.append({'mode':'pipeline','seconds':elapsed,'serial_seconds':serial_pipeline,'speedup':serial_pipeline/elapsed,
                 'efficiency':serial_pipeline/elapsed/workers,'max_abs_error':float(np.max(np.abs(answer-reference))),
                 'microbatches':len(batches),'interstage_activation_bytes':n*d*8})
    return {'seed':seed,'modes':rows,'scope':'Inference decomposition, not distributed backprop; CPU processes with explicit IPC, no GPU or network.'}


def federated(seed=0,rounds=20,local_steps=1):
    rng=np.random.default_rng(seed); clients=[]
    truth=rng.normal(size=6)
    for i,n in enumerate((32,48,64,80)):
        x=rng.normal(size=(n,6))+i*.3; y=x@truth+rng.normal(0,.15,n)+i*.15
        clients.append((x,y))
    allx=np.concatenate([x for x,y in clients]); ally=np.concatenate([y for x,y in clients]); total=len(ally)
    w=np.zeros(6); central=w.copy(); lr=.04; history=[]
    initial=float(.5*np.mean(ally**2)); one_step_error=0.
    for r in range(rounds):
        local=[]
        for x,y in clients:
            u=w.copy()
            for _ in range(local_steps): u-=lr*x.T@(x@u-y)/len(x)
            local.append(len(x)*u/total)
        nextw=sum(local)
        if r==0 and local_steps==1:
            one_step_error=float(np.max(np.abs(nextw-(w-lr*allx.T@(allx@w-ally)/total))))
        w=nextw
        # Same total gradient work: one centralized full pass per local step.
        for _ in range(local_steps): central-=lr*allx.T@(allx@central-ally)/total
        history.append({'round':r+1,'fedavg_loss':float(.5*np.mean((allx@w-ally)**2)),
                        'centralized_loss':float(.5*np.mean((allx@central-ally)**2))})
    return {'seed':seed,'rounds':rounds,'local_steps':local_steps,'initial_loss':initial,
            'fedavg_loss':history[-1]['fedavg_loss'],'centralized_loss':history[-1]['centralized_loss'],
            'one_step_equivalence_error':one_step_error if local_steps==1 else None,
            'model_transmitted_bytes':rounds*len(clients)*6*8*2,'sample_gradient_evaluations':rounds*local_steps*total,
            'trace':history,'non_iid':'Client feature mean and label offsets differ; sample-count weighted aggregation.'}


def mgda(g1,g2):
    """Exact minimum-norm convex combination for two task gradients."""
    delta=g1-g2; denom=delta@delta
    alpha=float(np.clip(-(g2@delta)/denom,0,1)) if denom>1e-20 else .5
    return alpha,alpha*g1+(1-alpha)*g2


def multitask(seed=0,quick=False):
    rng=np.random.default_rng(seed); x=rng.normal(size=(160,6)); true=rng.normal(size=6)
    # Shared representation plus task-specific biases; tasks intentionally conflict.
    y=np.stack([x@true+.5, -2*x@true-.3],axis=1)+rng.normal(0,.1,(160,2))
    rows=[]
    def task(w,t):
        residual=x[:120]@w[:6]+w[6+t]-y[:120,t]
        g=np.zeros(8); g[:6]=x[:120].T@residual/120; g[6+t]=residual.mean()
        return float(.5*np.mean(residual**2)),g
    for method in ('equal','mgda','gradnorm'):
        w=np.zeros(8); weights=np.ones(2); initial=np.array([task(w,t)[0] for t in (0,1)])
        start=perf_counter(); trace=[]
        for step in range(150 if quick else 500):
            pairs=[task(w,t) for t in (0,1)]; losses=np.array([p[0] for p in pairs]); grads=np.stack([p[1] for p in pairs])
            if method=='mgda':
                alpha,g=mgda(grads[0],grads[1]); weights=np.array([2*alpha,2*(1-alpha)])
            else:
                if method=='gradnorm':
                    # GradNorm alpha=1.5. Targets treated as constants in weight-gradient update.
                    norms=np.linalg.norm(grads[:,:6],axis=1); weighted=weights*norms
                    rates=losses/initial; rates/=rates.mean()
                    targets=weighted.mean()*rates**1.5
                    weights-=.01*np.sign(weighted-targets)*norms
                    weights=np.maximum(weights,1e-4); weights*=2/weights.sum()
                g=(weights[:,None]*grads).mean(0)
            w-=.03*g
            if step%25==0: trace.append({'step':step,'losses':losses.tolist(),'weights':weights.tolist()})
        tests=[float(.5*np.mean((x[120:]@w[:6]+w[6+t]-y[120:,t])**2)) for t in (0,1)]
        rows.append({'method':method,'train_losses':[task(w,t)[0] for t in (0,1)],'test_losses':tests,
                     'weights':weights.tolist(),'seconds':perf_counter()-start,'trace':trace})
    return {'seed':seed,'runs':rows,'gradnorm':'Positive weights normalized to sum two; task-gradient norms from shared parameters, alpha=1.5; target detached.'}


def run(quick=False):
    seeds=range(1 if quick else 5); cov=[]; sched=[]; parallel=[]; fed=[]; multi=[]
    for seed in seeds:
        cov.append(coverage(seed)); sched.append(scheduling(seed,quick)); parallel.append(parallelism(seed,quick))
        for rounds in (5,20):
            for steps in (1,5,20): fed.append(federated(seed,rounds,steps))
        multi.append(multitask(seed,quick))
    return {'track':'D','description':'Submodular maximum coverage; real multiprocessing scheduling and decomposition; non-IID FedAvg; equal/MGDA/GradNorm.',
            'measurements':{'coverage':cov,'scheduling':sched,'parallelism':parallel,'federated':fed,'multitask':multi},
            'correctness':{'coverage_guarantees':all(r['guarantee_satisfied'] for c in cov for r in c['runs']),
                           'diminishing_returns':all(c['diminishing_returns_exhaustive'] for c in cov),
                           'scheduling_results_equal':all(r['correct'] for s in sched for r in s['schedulers']),
                           'parallel_max_error':max(r['max_abs_error'] for s in parallel for r in s['modes']),
                           'fedavg_one_step_max_error':max(r['one_step_equivalence_error'] for r in fed if r['local_steps']==1)},
            'limitations':['Tiny CPU workloads include process startup and IPC; do not expect speedup.',
                           'Explicit work stealing uses a global lock and manager proxies, limiting scalability.',
                           'Amdahl/Gustafson curves are analytical predictions, not measured large-cluster scaling.',
                           'Data/model/pipeline examples perform inference only; federation is sequentially simulated clients, not networked hardware.',
                           'FedAvg communication counts payload only, excluding protocol overhead; clients are non-IID synthetic data.',
                           'Two-task linear shared model illustrates conflict; no claim of state-of-the-art multitask performance.']}
