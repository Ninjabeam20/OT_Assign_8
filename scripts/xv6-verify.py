#!/usr/bin/env python3
"""Run the real xv6 experiment; executed only when requested."""
import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from optlab.track_g import run
if __name__=='__main__':
    result=run('--quick' in sys.argv)
    path=Path(__file__).resolve().parents[1]/'results/G.json'
    path.write_text(json.dumps(result,indent=2)+'\n')
    print(path)
