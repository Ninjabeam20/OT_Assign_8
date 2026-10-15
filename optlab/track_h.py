"""Track H: budgeted index selection on an actual SQLite sales workload."""
import hashlib
import json
import sqlite3
import tempfile
import time
from pathlib import Path
import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp

CANDIDATES=[('ix_customer','customer'),('ix_region','region'),('ix_day','day'),
            ('ix_customer_day','customer, day'),('ix_region_amount','region, amount')]
QUERIES=[('customer_total','SELECT sum(amount), count(*) FROM sales WHERE customer=?',(42,)),
         ('regional_total','SELECT sum(amount), count(*) FROM sales WHERE region=?',(3,)),
         ('date_total','SELECT sum(amount), count(*) FROM sales WHERE day BETWEEN ? AND ?',(50,60)),
         ('customer_dates','SELECT sum(amount), count(*) FROM sales WHERE customer=? AND day BETWEEN ? AND ?',(42,20,100)),
         ('region_group','SELECT region, sum(amount), count(*) FROM sales GROUP BY region',())]

def create_database(path, n, seed):
    conn=sqlite3.connect(path)
    conn.execute('CREATE TABLE sales(id INTEGER PRIMARY KEY, customer INTEGER, region INTEGER, day INTEGER, amount INTEGER)')
    rng=np.random.default_rng(seed)
    data=np.column_stack((rng.integers(1,1001,n),rng.integers(0,10,n),rng.integers(0,365,n),rng.integers(1,10000,n)))
    conn.executemany('INSERT INTO sales(customer,region,day,amount) VALUES(?,?,?,?)', [tuple(map(int,row)) for row in data])
    conn.commit(); conn.execute('ANALYZE')
    return conn

def query_results(conn):
    return [conn.execute(sql,args).fetchall() for _,sql,args in QUERIES]

def measure(conn, repeats=5):
    expected=query_results(conn); samples=[]
    for _ in range(repeats):
        start=time.perf_counter()
        actual=query_results(conn)
        samples.append(time.perf_counter()-start)
        assert actual==expected
    return {'seconds_median':float(np.median(samples)), 'seconds_samples':samples,
            'throughput_queries_per_second':len(QUERIES)/float(np.median(samples)),
            'plans':{name:[list(row) for row in conn.execute('EXPLAIN QUERY PLAN '+sql,args)] for name,sql,args in QUERIES},
            'result_sha256':hashlib.sha256(json.dumps(expected).encode()).hexdigest()}

def select_indexes(sizes, gains, budget, method):
    if len(sizes)!=len(gains) or budget<0 or any(s<=0 for s in sizes): raise ValueError('invalid index selection inputs')
    if not sizes: return []
    if method=='greedy':
        ids=[]; room=budget
        for i in sorted(range(len(sizes)),key=lambda i:gains[i]/sizes[i],reverse=True):
            if gains[i]>0 and sizes[i]<=room: ids.append(i); room-=sizes[i]
        return ids
    if method!='ILP': raise ValueError(method)
    positive=np.maximum(np.asarray(gains,float),0)
    if not positive.any(): return []
    # Change units to avoid HiGHS absolute objective tolerances swallowing tiny gains.
    scaled=positive/positive.max()
    result=milp(-scaled,integrality=np.ones(len(sizes)),bounds=Bounds(0,1),
                constraints=LinearConstraint([sizes],-np.inf,budget))
    if not result.success: raise RuntimeError(result.message)
    return np.flatnonzero(result.x>.5).tolist()

def storage(conn):
    # Used pages excludes freed index pages retained in SQLite's freelist.
    return (conn.execute('PRAGMA page_count').fetchone()[0]-conn.execute('PRAGMA freelist_count').fetchone()[0])*conn.execute('PRAGMA page_size').fetchone()[0]

def run(quick=False):
    rows=[]; estimates=[]
    for seed in range(1 if quick else 5):
        with tempfile.TemporaryDirectory(prefix='optlab-db-') as tmp:
            conn=create_database(Path(tmp)/'sales.sqlite',3000 if quick else 50000,seed)
            expected=query_results(conn); baseline=measure(conn); base_size=storage(conn)
            sizes=[]; gains=[]
            for name,columns in CANDIDATES:
                conn.execute(f'CREATE INDEX {name} ON sales({columns})'); conn.execute('ANALYZE')
                size=storage(conn)-base_size; sample=measure(conn)
                sizes.append(size); gains.append(max(0.,baseline['seconds_median']-sample['seconds_median']))
                conn.execute(f'DROP INDEX {name}'); conn.execute('ANALYZE')
            budget=int(sum(sizes)*.40)
            estimates.append({'seed':seed,'index_sizes_bytes':sizes,'isolated_gains_seconds':gains,'storage_budget_bytes':budget})
            rows.append({'seed':seed,'method':'default_no_secondary_indexes','indexes':[],'storage_bytes':base_size,**baseline})
            for method in ['greedy','ILP']:
                start=time.perf_counter(); ids=select_indexes(sizes,gains,budget,method); selection_time=time.perf_counter()-start
                for i in ids:
                    name,columns=CANDIDATES[i]; conn.execute(f'CREATE INDEX {name} ON sales({columns})')
                conn.execute('ANALYZE'); actual_size=storage(conn)-base_size
                assert actual_size<=budget and query_results(conn)==expected
                sample=measure(conn,3 if quick else 7)
                rows.append({'seed':seed,'method':method,'indexes':[CANDIDATES[i][0] for i in ids],
                             'selection_seconds':selection_time,'storage_bytes':storage(conn),'extra_bytes':actual_size,
                             'speedup':baseline['seconds_median']/sample['seconds_median'],**sample})
                for i in ids: conn.execute(f'DROP INDEX {CANDIDATES[i][0]}')
                conn.execute('ANALYZE')
            conn.close()
    return {'description':'Synthetic integer-valued sales workload on SQLite; binary index selection under measured page-storage budget.',
            'formulation':'maximize sum(gain_i*x_i), sum(size_i*x_i)<=budget, x_i binary; gains measured one index at a time.',
            'measurements':rows,'selection_inputs':estimates,'row_count':3000 if quick else 50000,
            'queries':[{'name':n,'sql':s,'parameters':p} for n,s,p in QUERIES],'sqlite_version':sqlite3.sqlite_version,
            'correctness':True,'limitations':['Additive gain model ignores interacting indexes; ILP optimality applies to that model, not actual query latency.',
            'Warm-cache single-client read workload; throughput is sequential queries per second, not concurrent throughput.',
            'SQLite uses EXPLAIN QUERY PLAN rather than PostgreSQL EXPLAIN ANALYZE; latency measured separately.']}
