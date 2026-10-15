"""Single entry point and atomic result files for all ten experiments."""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time

# Fix implicit BLAS worker counts for reproducible process-parallel experiments.
for variable in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS']:
    os.environ.setdefault(variable,'1')
ROOT=Path(__file__).resolve().parents[1]

def run_track(track, quick=False, output_dir=None):
    track=track.upper()
    if track not in 'ABCDEFGHIJ' or len(track)!=1: raise ValueError('track must be A through J')
    module=importlib.import_module('optlab.track_'+track.lower())
    started=time.perf_counter(); result=module.run(quick=quick)
    if not isinstance(result,dict): raise TypeError('track must return an object')
    result['metadata']={'track':track,'mode':'quick' if quick else 'full','timestamp_utc':datetime.now(timezone.utc).isoformat(),
        'python':sys.version,'platform':platform.platform(),'machine':platform.machine(),'cpu_count':os.cpu_count(),
        'thread_environment':{k:os.environ.get(k) for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS']},
        'elapsed_seconds':time.perf_counter()-started,
        'source_sha256':hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest(),
        'dependencies':{name:importlib.metadata.version(name) for name in ['numpy','scipy','scikit-learn']}}
    destination=Path(output_dir) if output_dir else ROOT/'results'/('quick' if quick else '')
    destination.mkdir(parents=True,exist_ok=True)
    path=destination/f'{track}.json'; temporary=path.with_suffix('.json.tmp')
    temporary.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n'); temporary.replace(path)
    return path

def main():
    parser=argparse.ArgumentParser(description='Assignment 8 reproducible optimization experiments')
    sub=parser.add_subparsers(dest='command',required=True)
    run=sub.add_parser('run'); run.add_argument('--track',default='all'); run.add_argument('--quick',action='store_true')
    run.add_argument('--output',type=Path)
    sub.add_parser('report'); sub.add_parser('status')
    args=parser.parse_args()
    if args.command=='run':
        for track in ('ABCDEFGHIJ' if args.track.lower()=='all' else args.track.upper()):
            print(f'Running Track {track} ({"quick" if args.quick else "full"})...',flush=True)
            print(run_track(track,args.quick,args.output),flush=True)
    elif args.command=='report':
        from .report import build_report
        build_report()
    else:
        for track in 'ABCDEFGHIJ':
            path=ROOT/'results'/f'{track}.json'
            print(track, 'results available' if path.exists() else 'not run')
        print('External evidence: inspect docs/SUBMISSION_STATUS.md')
