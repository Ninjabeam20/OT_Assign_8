#!/usr/bin/env python3
"""Fetch exact verified MIT sources and prepare two reproducible variants."""
from pathlib import Path
import hashlib,io,json,shutil,subprocess,tarfile,urllib.request
ROOT=Path(__file__).resolve().parents[1]
def main():
    meta=json.loads((ROOT/'scripts/xv6-upstream.json').read_text())
    targets=[ROOT/'vendor'/('xv6-'+name) for name in ('baseline','optimized')]
    if any(p.exists() for p in targets):
        raise SystemExit('Existing xv6 directory: preserve it; move it aside before setup.')
    url=f"https://codeload.github.com/mit-pdos/xv6-riscv/tar.gz/{meta['commit']}"
    data=urllib.request.urlopen(url,timeout=60).read()
    if hashlib.sha256(data).hexdigest()!=meta['archive_sha256']:raise RuntimeError('upstream archive checksum mismatch')
    (ROOT/'vendor').mkdir(exist_ok=True)
    with tarfile.open(fileobj=io.BytesIO(data),mode='r:gz') as tar:
        tar.extractall(ROOT/'vendor',filter='data')
    (ROOT/'vendor'/('xv6-riscv-'+meta['commit'])).rename(targets[0])
    shutil.copytree(targets[0],targets[1])
    for p in targets:
        shutil.copyfile(ROOT/'scripts/xv6-optbench.c',p/'user/optbench.c')
        make=p/'Makefile';make.write_text(make.read_text().replace('UPROGS=\\','UPROGS=\\\n\t$U/_optbench\\',1))
    subprocess.run(['patch','-p1','-i',str(ROOT/'scripts/xv6-optimization.patch')],cwd=targets[1],check=True)
    print('Prepared baseline and optimized pinned xv6 sources.')
if __name__=='__main__':main()
