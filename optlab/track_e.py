"""Track E: synthetic campus capacitated vehicle routing, unlimited shuttle trips."""
import itertools
import time
import numpy as np
from scipy.optimize import milp, Bounds, LinearConstraint
from scipy.sparse import lil_matrix


def distance_matrix(points):
    points=np.asarray(points,float)
    return np.linalg.norm(points[:,None,:]-points[None,:,:],axis=2)


def validate_routes(routes, demands, capacity):
    visits=[]
    for route in routes:
        if len(route)<3 or route[0]!=0 or route[-1]!=0: return False
        middle=route[1:-1]
        if any(i<=0 or i>=len(demands) for i in middle): return False
        if sum(demands[i] for i in middle)>capacity: return False
        visits.extend(middle)
    return sorted(visits)==list(range(1,len(demands)))


def route_cost(routes, distances):
    return float(sum(distances[a,b] for r in routes for a,b in zip(r,r[1:])))


def heuristic(distances, demands, capacity, nearest=False):
    if any(d<=0 or d>capacity for d in demands[1:]): raise ValueError('positive feasible stop demands required')
    pending=set(range(1,len(demands))); routes=[]
    while pending:
        route=[0]; remaining=capacity
        while True:
            feasible=[i for i in pending if demands[i]<=remaining]
            if not feasible: break
            i=min(feasible,key=lambda i:(distances[route[-1],i],i)) if nearest else min(feasible)
            route.append(i); pending.remove(i); remaining-=demands[i]
        routes.append(route+[0])
    return routes


def solve_ilp(distances, demands, capacity, time_limit=30):
    """Binary arcs plus load-based Miller-Tucker-Zemlin capacity/subtour constraints."""
    distances=np.asarray(distances,float); n=len(demands)
    if distances.shape!=(n,n) or n<2 or capacity<=0 or demands[0]!=0 or any(d<=0 or d>capacity for d in demands[1:]):
        raise ValueError('square distances, zero-demand depot and feasible positive demands required')
    arcs=[(i,j) for i in range(n) for j in range(n) if i!=j]
    ix={arc:k for k,arc in enumerate(arcs)}; m=len(arcs)
    rows=[]; lower=[]; upper=[]
    for k in range(1,n):
        rows.append({ix[i,k]:1 for i in range(n) if i!=k}); lower.append(1); upper.append(1)
        rows.append({ix[k,j]:1 for j in range(n) if j!=k}); lower.append(1); upper.append(1)
    rows.append({**{ix[0,j]:1 for j in range(1,n)}, **{ix[i,0]:-1 for i in range(1,n)}}); lower.append(0); upper.append(0)
    for i in range(1,n):
        for j in range(1,n):
            if i!=j:
                rows.append({m+i-1:1,m+j-1:-1,ix[i,j]:capacity})
                lower.append(-np.inf); upper.append(capacity-demands[j])
    a=lil_matrix((len(rows),m+n-1))
    for r,entries in enumerate(rows):
        for col,value in entries.items(): a[r,col]=value
    result=milp(np.r_[[distances[i,j] for i,j in arcs],np.zeros(n-1)],
                integrality=np.r_[np.ones(m),np.zeros(n-1)],
                bounds=Bounds(np.r_[np.zeros(m),demands[1:]],np.r_[np.ones(m),np.full(n-1,capacity)]),
                constraints=LinearConstraint(a.tocsr(),lower,upper),options={'time_limit':time_limit,'mip_rel_gap':0.0})
    if result.x is None: raise RuntimeError(f'No feasible incumbent: {result.message}')
    chosen=[(i,j) for k,(i,j) in enumerate(arcs) if result.x[k]>.5]
    routes=[]
    for _,start in sorted((i,j) for i,j in chosen if i==0):
        route=[0,start]
        while route[-1]!=0:
            nxt=[j for i,j in chosen if i==route[-1]]
            if len(nxt)!=1 or len(route)>n: raise RuntimeError('invalid solver path')
            route.append(nxt[0])
        routes.append(route)
    if not validate_routes(routes,demands,capacity): raise RuntimeError('invalid routing solution')
    return routes, {'optimal':bool(result.success),'status':int(result.status),'gap':float(result.mip_gap),'dual_bound':float(result.mip_dual_bound),'message':result.message}


def exact_enumeration(distances, demands, capacity):
    """Independent permutation/partition oracle for <=7 stops."""
    n=len(demands)-1
    if n>7: raise ValueError('oracle limited to seven stops')
    best=float('inf')
    for perm in itertools.permutations(range(1,n+1)):
        for mask in range(1<<max(0,n-1)):
            routes=[]; current=[0]
            for k,node in enumerate(perm):
                current.append(node)
                if k==n-1 or mask>>k&1:
                    routes.append(current+[0]); current=[0]
            if validate_routes(routes,demands,capacity): best=min(best,route_cost(routes,distances))
    return best


def run(quick=False):
    rows=[]; datasets=[]
    for seed in range(1 if quick else 5):
        for n in ([5] if quick else [5,9]):
            rng=np.random.default_rng(seed)
            points=np.vstack(([0.,0.],rng.uniform(-3,3,(n,2))))
            demands=[0]+rng.integers(1,4,n).tolist(); capacity=6
            d=distance_matrix(points)
            datasets.append({'seed':seed,'stops':n,'coordinates_km':points.tolist(),'demands':demands,'capacity':capacity})
            for name in ['fixed_order','nearest_neighbor','ILP']:
                t=time.perf_counter(); info={}
                if name=='ILP': routes,info=solve_ilp(d,demands,capacity,time_limit=10 if quick else 20)
                else: routes=heuristic(d,demands,capacity,name=='nearest_neighbor')
                seconds=time.perf_counter()-t
                assert validate_routes(routes,demands,capacity)
                rows.append({'seed':seed,'stops':n,'method':name,'distance_km':route_cost(routes,d), 'routes':routes,'seconds':seconds,**info})
    return {'description':'Minimize campus shuttle distance with indivisible stop demands and capacity six, unlimited depot-return trips.',
            'formulation':'min sum(d_ij*x_ij), binary x; one incoming/outgoing arc per stop; depot flow conserved; q_i<=u_i<=Q; u_i-u_j+Q*x_ij<=Q-q_j.',
            'measurements':rows,'datasets':datasets,'correctness':True,
            'strategy_selection':[{'method':'nearest neighbor','variables':'discrete','kind':'heuristic','hardware':'one CPU','scale':'large','parallelism':'independent instances'}, {'method':'ILP MTZ','variables':'binary arcs, continuous loads','kind':'exact if proven optimal','hardware':'CPU HiGHS','scale':'small','parallelism':'solver controlled'}],
            'limitations':['Synthetic Euclidean campus, not actual road data; no time windows, traffic or fleet limit. Runtime contains solver overhead; timeout incumbents are not called optimal.']}
