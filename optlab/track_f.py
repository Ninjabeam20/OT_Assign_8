"""Unsigned 64-bit straight-line compiler; no effects at import time."""
from dataclasses import dataclass
import re, subprocess, time, statistics, tempfile
from pathlib import Path
MASK=(1<<64)-1
PASSES=('fold','propagate','dead','cse')
@dataclass(frozen=True)
class Instruction:
    dest:str
    op:str
    args:tuple
@dataclass(frozen=True)
class IR:
    instructions:tuple
    result:object

def parse(source):
    tokens=re.findall(r'\d+|[A-Za-z_]\w*|[+*();=\-]|\S',source)
    pos=0; code=[]; names={'x':'x'}
    def take(w=None):
        nonlocal pos
        if pos>=len(tokens): raise ValueError('unexpected end')
        t=tokens[pos];pos+=1
        if w is not None and t!=w: raise ValueError(f'expected {w}, got {t}')
        return t
    def expr(level=0):
        if level<2:
            a=expr(level+1)
            while pos<len(tokens) and tokens[pos] in (('+','-') if level==0 else ('*',)):
                op=take(); b=expr(level+1); d=f't{len(code)}';code.append(Instruction(d,op,(a,b)));a=d
            return a
        t=take()
        if t=='(':
            a=expr();take(')');return a
        if t.isdigit():return int(t)&MASK
        if t in names:return names[t]
        raise ValueError(f'unknown name/token {t}')
    while pos<len(tokens):
        t=take()
        if t=='return':
            out=expr();take(';')
            if pos!=len(tokens):raise ValueError('tokens after return')
            return IR(tuple(code),out)
        if t!='let':raise ValueError('expected let or return')
        name=take()
        if not re.fullmatch('[A-Za-z_]\\w*',name):raise ValueError('invalid name')
        take('=');value=expr();take(';');d=f't{len(code)}';code.append(Instruction(d,'copy',(value,)));names[name]=d
    raise ValueError('missing return')

def compute(op,args):
    if op=='copy':return args[0]
    a,b=args
    return {'+':lambda:a+b,'-':lambda:a-b,'*':lambda:a*b}[op]()&MASK

def interpret(ir,x):
    env={'x':x&MASK}
    def get(v):return v if isinstance(v,int) else env[v]
    for i in ir.instructions:env[i.dest]=compute(i.op,[get(v) for v in i.args])
    return get(ir.result)

def optimize(ir,order):
    for name in order:
        code=[]; mapping={}; expressions={}
        def subst(v):
            while v in mapping:v=mapping[v]
            return v
        if name=='dead':
            live={ir.result};keep=[]
            for i in reversed(ir.instructions):
                if i.dest in live:keep.append(i);live.update(i.args)
            ir=IR(tuple(reversed(keep)),ir.result);continue
        if name not in PASSES:raise ValueError(name)
        for i in ir.instructions:
            args=tuple(subst(a) for a in i.args) if name in ('propagate','cse') else i.args
            op=i.op
            if name=='fold' and all(isinstance(a,int) for a in args):op='copy';args=(compute(i.op,args),)
            if name=='propagate' and op=='copy':mapping[i.dest]=args[0]
            if name=='cse':
                key=(op,tuple(sorted(args,key=str)) if op in ('+','*') else args)
                if key in expressions:mapping[i.dest]=expressions[key];op='copy';args=(expressions[key],)
                else:expressions[key]=i.dest
            code.append(Instruction(i.dest,op,args))
        ir=IR(tuple(code),subst(ir.result))
    return ir

def cost(ir):return sum(3 if i.op=='*' else 1 for i in ir.instructions)
def greedy_order(ir):
    # Look ahead three passes to cross plateaus, e.g. propagation enables folding.
    import itertools
    order=[];history=[]
    for _ in range(12):
        candidates=[(cost(out:=optimize(ir,pair)),pair,out) for pair in itertools.product(PASSES,repeat=3)]
        score,pair,out=min(candidates,key=lambda c:(c[0],c[1]))
        if score>=cost(ir):break
        history.append({'passes':pair,'before':cost(ir),'after':score});order.extend(pair);ir=out
    return order,ir,history

def emit_c(ir,iterations=1000000):
    def val(v):return f'UINT64_C({v})' if isinstance(v,int) else v
    lines=['#include <stdint.h>','#include <stdio.h>','#include <time.h>','__attribute__((noinline)) uint64_t compiled(uint64_t x) {']
    for i in ir.instructions:
        e=val(i.args[0]) if i.op=='copy' else f'{val(i.args[0])} {i.op} {val(i.args[1])}'
        lines.append(f' uint64_t {i.dest} = {e};')
    lines+=[' return '+val(ir.result)+';','}',f'int main(void) {{ uint64_t sum=0; clock_t start=clock(); for(uint64_t x=0;x<{iterations};x++) sum+=compiled(x); printf("%llu %.9f\\n", (unsigned long long)sum, (double)(clock()-start)/CLOCKS_PER_SEC); }}']
    return '\n'.join(lines)+'\n'

def native_measure(ir,path,iterations=1000000):
    backend_start=time.perf_counter()
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);source=path.with_suffix('.c');source.write_text(emit_c(ir,iterations));start=time.perf_counter()
    subprocess.run(['clang','-O0',str(source),'-o',str(path)],check=True,capture_output=True);elapsed=time.perf_counter()-start;backend_elapsed=time.perf_counter()-backend_start
    asm=subprocess.check_output(['otool','-tvV',str(path)],text=True)
    body=asm.split('_compiled:')[1].split('_main:')[0]
    samples=[subprocess.check_output([str(path)],text=True).split() for _ in range(5)]
    return {'checksum':int(samples[0][0]),'runtime_seconds':statistics.median(float(s[1]) for s in samples),'runtime_samples':[float(s[1]) for s in samples],'compile_seconds':elapsed,'backend_compile_seconds':backend_elapsed,'binary_bytes':path.stat().st_size,'generated_c_bytes':len(source.read_bytes()),'function_instruction_count':sum(bool(re.match(r'^[0-9a-f]{16}\s',line)) for line in body.splitlines()),'ir_cost':cost(ir)}
CASES=[('constant_chain','let a = 2 + 3; let b = a * 9; return b * x;'),('redundancy','let a = x + 7; let b = x + 7; let unused = x * 14; return a * b;'),('mixed','let c = 4 * 5; let a = x + c; let b = x + c; let dead = b * 7; return a * b + c;')]
def run(quick=False):
    rows=[]
    with tempfile.TemporaryDirectory(prefix='optlab-F-') as d:
        for name,source in CASES:
            start=time.perf_counter();ir=parse(source);frontend_seconds=time.perf_counter()-start
            start=time.perf_counter();order,opt,history=greedy_order(ir);search_seconds=time.perf_counter()-start
            n=100000 if quick else 100000000
            baseline=native_measure(ir,Path(d)/(name+'-base'),n);optimized=native_measure(opt,Path(d)/(name+'-opt'),n)
            baseline['end_to_end_compile_seconds']=frontend_seconds+baseline['backend_compile_seconds']
            optimized['end_to_end_compile_seconds']=frontend_seconds+search_seconds+optimized['backend_compile_seconds']
            assert baseline['checksum']==optimized['checksum']
            assert all(interpret(ir,x)==interpret(opt,x) for x in [0,1,7,123,MASK])
            rows.append(dict(name=name,source=source,frontend_seconds=frontend_seconds,search_seconds=search_seconds,order=order,search=history,baseline=baseline,optimized=optimized,speedup=baseline['runtime_seconds']/optimized['runtime_seconds']))
    return {'track':'F','description':'SSA toy uint64 compiler with lexer, recursive descent parser, C generation and greedy three-pass lookahead search','measurements':rows,'correctness':{'native_checksum_equivalent':True,'edge_inputs_equivalent':True},'limitations':['Straight-line unsigned modular arithmetic only; no division or control flow.','Static native instruction count, not hardware retired instructions.','Clang -O0 isolates toy optimizer; executable size includes fixed Mach-O overhead.','Five runtime samples; one compile-time sample per variant. compile_seconds is clang subprocess time; backend_compile_seconds includes C emission and file write; end_to_end_compile_seconds additionally includes parsing and, for optimized, greedy search.'],'objective':'minimize sum(IR weights): multiply=3, other=1; three-pass greedy improvement'}
