"""Build a measured technical report and standalone figures from saved results."""
from collections import defaultdict
from datetime import datetime
from pathlib import Path
import json
import statistics
from xml.sax.saxutils import escape
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
ROOT=Path(__file__).resolve().parents[1]
NAMES={'A':'Continuous optimization','B':'Discrete optimization','C':'Quantum optimization','D':'Submodular, parallel and distributed','E':'Campus shuttle routing','F':'Compiler optimization','G':'xv6 operating-system optimization','H':'Database index selection','I':'Quantum algorithms and QML','J':'Software-engineering optimization'}


def mean(xs): return statistics.mean(xs)
def fmt(value):
    if isinstance(value,float): return f'{value:.5g}'
    return str(value)


def table_data(t,d):
    m=d['measurements']
    if t=='A':
        landscape=m['optimizers'][0]['landscape']; group=defaultdict(list)
        for r in m['optimizers']:
            if r['landscape']==landscape: group[r['optimizer']].append(r)
        return ['Method ('+landscape+')','Mean objective gap','Mean seconds'],[[k,mean(r['optimality_gap'] for r in v),mean(r['seconds'] for r in v)] for k,v in group.items()]
    if t=='B':
        group=defaultdict(list)
        for r in m:group[r['method']].append(r)
        return ['Method','Mean optimum gap','Mean median seconds'],[[k,mean(r['gap'] for r in v),mean(r['seconds_median'] for r in v)] for k,v in group.items()]
    if t=='C':
        rows=[['QAOA',mean(r['expected_cut'] for r in m['qaoa']),'exact cut 4'],['VQE',max(abs(r['energy']-r['exact_energy']) for r in m['vqe']),'max absolute energy error']]
        group=defaultdict(list)
        for seed_rows in m['optimizers']:
            for r in seed_rows: group[r['method']].append(r)
        rows += [[k,mean(r['final_energy']-r['exact_energy'] for r in v),'mean energy gap'] for k,v in group.items()]
        return ['Experiment','Measured value','Meaning'],rows
    if t=='D':
        group=defaultdict(list)
        for r in m['scheduling']:
            for x in r['schedulers']:group[x['mode']].append(x)
        return ['Scheduler','Mean speedup','Mean efficiency'],[[k,mean(r['speedup'] for r in v),mean(r['efficiency'] for r in v)] for k,v in group.items()]
    if t=='E':
        return ['Stops','Method','Mean distance km'],[[n,name,mean(r['distance_km'] for r in m if r['stops']==n and r['method']==name)] for n in [5,9] for name in ['fixed_order','nearest_neighbor','ILP']]
    if t=='F':return ['Program','Native speedup','Instructions before / after'],[[r['name'],r['baseline']['runtime_seconds']/r['optimized']['runtime_seconds'],f"{r['baseline']['function_instruction_count']} / {r['optimized']['function_instruction_count']}"] for r in m]
    if t=='G':return ['Workload','Baseline ticks','Optimized ticks'],[[k,m['baseline']['median_ticks'][k],m['optimized']['median_ticks'][k]] for k in ['fork','cpu','mixed']]
    if t=='H':
        return ['Index policy','Mean latency ms','Mean storage bytes'],[[name,mean(r['seconds_median']*1000 for r in m if r['method']==name),mean(r['storage_bytes'] for r in m if r['method']==name)] for name in ['default_no_secondary_indexes','greedy','ILP']]
    if t=='I':
        group=defaultdict(list)
        for r in m['classification']:
            for x in r['models']:group[x['model']].append(x)
        return ['Model','Mean test accuracy','Sample SD'],[[k,mean(r['test_accuracy'] for r in v),statistics.stdev(r['test_accuracy'] for r in v)] for k,v in group.items()]
    if t=='J':return ['Suite','Tests / speedup','Detected faults (of 4)'],[[r['method'],f"{r['selected_count']} / {r['speedup']:.3f}x",r['faults_detected']] for r in m]

TEXT={
'A':('Minimize regression/ML loss over continuous parameters; compare convex, strongly convex and nonconvex landscapes.',
'Five seeded datasets; identical initial parameters. GD, SGD, mini-batch, Momentum, NAG, AdaGrad, RMSProp, Adam, Newton and Gauss-Newton are implemented. A nonlinear exponential residual distinguishes the two curvature methods. Manual neural-network backpropagation is checked independently of GD/Adam. Fisher, diagonal/low-rank approximations and Hessian-vector products are measured. Validation selects step size; noise and L2 regularization are varied.',
'Least-squares reference and finite-difference derivative checks establish correctness. Equal update counts are not equal sample-gradient budgets; counts are retained. Saddle initialization can stall and aggressive rates diverge. These small tasks do not establish a universal best optimizer.'),
'B':('Maximize knapsack value under integer capacity; demonstrate exact and heuristic discrete optimization and QUBO/Ising conversion.',
'Five 24-item instances compare ratio greedy, dynamic programming, branch-and-bound and ILP. Each timing has a warm-up and repeated samples. Exact methods are checked against exhaustive tiny-instance enumeration. Four-cycle Max-Cut is represented as QUBO and Ising energies; all 16 assignments agree. Cardinality-two selection demonstrates a penalty exceeding possible objective gains.',
'Greedy is not exact. DP is pseudo-polynomial; storing reconstruction tuples adds path-copy costs. Branch-and-bound uses exact rational ordering and integer bounds after review exposed float precision errors. ILP uses floating-point coefficients on these small bounded integers.'),
'C':('Optimize parameterized quantum circuits with classical feedback; compare objective quality, circuit counts and measurement cost.',
'Five seeds: p=2 QAOA solves the same four-cycle as B, VQE minimizes Z0+Z1+0.5 X0X1, and a PQC regresses sin(x). Parameter-shift gradient descent, SPSA and regularized quantum natural gradient share initial conditions. A density-matrix depolarizing hardware-noise model and finite-shot sampling study measurement error. Random circuits at 2/4/6/8 qubits probe gradient variance.',
'QAOA is bounded by exact enumeration and VQE by diagonalization. QNG state-derivative overhead is counted separately. Statevectors/density matrices run on a classical CPU, not a QPU. Small size/depth sweeps do not prove asymptotic barren plateaus; clean-angle evaluation under noise is not noisy retraining.'),
'D':('Maximize submodular coverage; reduce parallel makespan; study communication and conflicting learning objectives.',
'Coverage greedy is checked against exhaustive optima and diminishing-return conditions, including a 5/6 counterexample. Real spawned processes execute static, dynamic and work-stealing scheduling, locality experiments and data/model/pipeline decompositions. FedAvg varies local steps and rounds against centralized gradient work. MGDA and GradNorm balance a two-task shared model against equal weights.',
'Parallel outputs match serial references. Timings include spawn, IPC, synchronization and shutdown; small tasks often slow down. FedAvg clients are sequential simulations, not a measured network. Amdahl and Gustafson predictions use stated assumed serial fractions; actual speedup and efficiency are separate measurements.'),
'E':('Reduce the travel distance of a simulated campus shuttle while serving every stop within capacity six.',
'Synthetic baseline: index-order visitation, returning to the depot when necessary. Five seeds create 5- and 9-stop datasets in a six-kilometre square with demand 1-3. Compare feasible nearest-neighbor routes with binary-arc ILP using load-based MTZ constraints. Minimize sum(d_ij*x_ij); one arrival/departure per stop, balanced depot flow, q_i <= u_i <= Q and u_i-u_j+Q*x_ij <= Q-q_j.',
'Every route is checked for unique stop coverage and capacity. Four-stop solutions are checked against independent permutation/partition enumeration. Solver statuses, bounds and gaps are retained with a 20-second limit. This is simulated evidence, not an actual campus survey; roads, time windows and fleet limits are excluded.'),
'F':('Reduce generated code cost without changing unsigned 64-bit program behavior; optimize compiler pass ordering.',
'A toy-language lexer/parser produces temporary-based IR, interpreted and compiled to C. Four passes: constant folding, propagation, dead-code elimination and common-subexpression elimination. Greedy triple-pass lookahead minimizes weighted IR cost, subject to output equivalence. Native Clang -O0 executables run 100 million inputs, with five CPU-time samples per variant.',
'All 24 pass permutations are checked on representative programs; native checksums match. Frontend, optimization search, backend and end-to-end compilation costs are recorded after review found omitted overhead. Static function instruction counts are not retired hardware counters; executable padding can hide size reductions.'),
'G':('Optimize xv6 memory sharing and scheduling while preserving kernel correctness.',
'Pinned MIT xv6-riscv runs in QEMU. Baseline round-robin/eager fork is compared with equal-ticket lottery scheduling and copy-on-write fork. Page-reference counts, store faults and kernel copyout handle COW; read-only pages remain protected. Three repetitions each of fork-heavy, CPU and mixed CPU/sleep workloads are measured in guest timer ticks.',
'Fresh-disk full upstream usertests pass for baseline one hart, optimized one hart and optimized three harts; raw logs are retained. Two simultaneous kernel changes prevent clean causal attribution. Fork gains plausibly come from avoided copying. No scheduler fairness advantage is claimed. QEMU timing is not physical RISC-V performance.'),
'H':('Choose database indexes to reduce a real SQLite query workload under a storage budget.',
'Five synthetic 50,000-row sales databases and five fixed SQL queries compare default no-secondary-index planning with greedy and ILP index selection. Candidate sizes are measured occupied pages. The binary objective sums isolated latency gains subject to 40% of total candidate storage. Chosen combinations are then actually benchmarked; EXPLAIN QUERY PLAN and exact result hashes are retained.',
'Integer currency avoids floating-point aggregation-order changes. Median warm-cache latency, raw samples, sequential throughput and storage are measured. Additive gain estimates ignore index interactions, so ILP optimality applies to the selection model, not necessarily measured runtime. Normalized objective units avoid solver-tolerance errors.'),
'I':('Measure quantum algorithm behavior and QML tradeoffs relative to classical methods.',
'Direct circuits demonstrate Deutsch-Jozsa, Bernstein-Vazirani, Grover, QFT, QPE and Shor order finding for 15. Suzuki-Trotter Monte Carlo models annealing and is compared with classical annealing. A nine-parameter variational classifier and fidelity-kernel SVM share train/test rows with classical models on 72 two-moons samples. Scalers fit training data only.',
'Grover includes actual linear-search comparisons, logical gate/query counts and separately labeled simulator timings. QML reports accuracy, training time, parameters and circuit evaluations; cached feature-state work differs from hardware overlap circuits. Classical models outperform these quantum classifiers on average. Dense Shor multiplication and simulated annealing are small demonstrations, not scalable hardware implementations.'),
'J':('Minimize test execution cost while preserving all Python JSON lines covered by a candidate suite.',
'The target is public CPython json (1,317 Python source lines), not the small toy compiler. Fifty-three cases cover parsing, encoding, Unicode, invalid syntax and options. cProfile establishes baseline costs. Weighted set cover compares full suite, naive prefix, greedy and ILP. Minimize sum(t_i*x_i) subject to each observed line retaining at least one selected test.',
'All selected suites preserve observed line coverage, but reduced suites miss one of four deliberate API mutations detected by the full suite. This proves coverage retention alone does not guarantee behavior retention. C accelerator lines are not traced. Microsecond timings are noisy and selection overhead may require many CI runs to amortize.')}


def figure(t,d,path):
    fig,ax=plt.subplots(figsize=(7.1,2.6));m=d['measurements']
    if t=='A':
        rows=[r for r in m['optimizers'] if r['seed']==0 and r['landscape']==m['optimizers'][0]['landscape']]
        ax.barh([r['optimizer'] for r in rows],[max(abs(r['optimality_gap']),1e-16) for r in rows]);ax.set_xscale('log');ax.set_xlabel('Absolute objective gap (seed 0, log scale)')
    elif t=='E':
        rows=[r for r in m if r['seed']==0 and r['stops']==9];ax.bar([r['method'] for r in rows],[r['distance_km'] for r in rows]);ax.set_ylabel('Distance (km)');ax.set_title('Seed 0, nine stops')
    elif t=='F':
        ax.bar([r['name'] for r in m],[r['baseline']['runtime_seconds']/r['optimized']['runtime_seconds'] for r in m]);ax.axhline(1,color='black',linestyle='--');ax.set_ylabel('Native speedup')
    elif t=='G':
        ks=['fork','cpu','mixed'];xs=range(3);ax.bar([x-.18 for x in xs],[m['baseline']['median_ticks'][k] for k in ks],width=.36,label='baseline');ax.bar([x+.18 for x in xs],[m['optimized']['median_ticks'][k] for k in ks],width=.36,label='optimized');ax.set_xticks(list(xs),ks);ax.set_ylabel('Guest timer ticks');ax.legend()
    elif t=='I':
        headers,rows=table_data(t,d);ax.barh([r[0].replace('classical_','C: ').replace('quantum_','Q: ').replace('variational_','') for r in rows],[r[1] for r in rows],xerr=[r[2] for r in rows]);ax.set_xlim(0,1.05);ax.set_xlabel('Held-out accuracy: mean ± sample SD, five splits')
    elif t=='J':
        ax.bar([r['method'] for r in m],[r['selected_count'] for r in m]);ax.set_ylabel('Selected test cases');ax.set_title('Full suite detects 4 faults; reduced suites detect 3')
    elif t=='C':
        groups=defaultdict(list)
        for seed_rows in m['optimizers']:
            for r in seed_rows: groups[r['method']].append(r['final_energy']-r['exact_energy'])
        ax.bar(['shift GD','SPSA','QNG'],[max(mean(v),1e-16) for v in groups.values()]);ax.set_yscale('log');ax.set_ylabel('Mean VQE energy gap (log)')
    elif t=='D':
        _,rows=table_data(t,d);ax.bar([r[0] for r in rows],[r[1] for r in rows]);ax.axhline(1,color='black',linestyle='--');ax.set_ylabel('Mean speedup, two workers')
    elif t=='H':
        _,rows=table_data(t,d);ax.bar(['default','greedy','ILP'],[r[1] for r in rows]);ax.set_ylabel('Mean median query-batch latency (ms)')
    elif t=='B':
        _,rows=table_data(t,d);ax.barh([r[0] for r in rows],[r[1] for r in rows]);ax.set_xlabel('Mean knapsack value shortfall from optimum')
    ax.spines[['top','right']].set_visible(False);fig.tight_layout();fig.savefig(path,dpi=180);plt.close(fig)


def build_report():
    results={t:json.loads((ROOT/'results'/f'{t}.json').read_text()) for t in NAMES}
    for t,d in results.items():
        if 'metadata' not in d:raise RuntimeError(f'Track {t} lacks verified runner provenance')
    figdir=ROOT/'output/figures';figdir.mkdir(parents=True,exist_ok=True)
    styles=getSampleStyleSheet();styles.add(ParagraphStyle(name='SmallBody',fontName='Helvetica',fontSize=9,leading=12,spaceAfter=7));styles.add(ParagraphStyle(name='Cell',fontSize=8,leading=10))
    styles['Title'].textColor=colors.HexColor('#17324d');styles['Heading1'].textColor=colors.HexColor('#17324d')
    story=[];md=['# Assignment 8 - Optimize Anything','', 'Technical report. All figures and tables are derived from saved full-run results; generated '+datetime.now().strftime('%Y-%m-%d')+'.','']
    def para(text,style='SmallBody'):story.append(Paragraph(escape(text),styles[style]))
    def heading(text):story.append(Paragraph(escape(text),styles['Heading1']))
    para('OPTIMIZE ANYTHING','Title');para('Assignment 8 - Ten-track experimental portfolio','Heading2')
    para('Main case study: capacity-constrained campus shuttle routing. Development: AI-assisted implementations, independent tests, measured comparisons and documented corrections.')
    heading('Evidence and interpretation')
    para('This portfolio contains executable experiments for all ten compulsory tracks. Exact solutions, numerical references, native program outputs, SQL result hashes and real xv6 test logs provide correctness evidence. Negative results are retained: tiny parallel workloads can be slower, quantum classifiers can lose to classical models, and line-preserving test reduction can lose fault detection.')
    para('The second-tool output is supplied as Gemini 3.8 Flash (High). Its original code and metadata claims are preserved. The student confirms that this work was done in Google Antigravity IDE. Codex independently reran checks and found large-integer errors and unsupported analysis claims. See the AI comparison and prompts/second-tool/ANTIGRAVITY_EVIDENCE.md.')
    para('Submission repository: https://github.com/Ninjabeam20/OT_Assign_8. The verified publication status is recorded in docs/SUBMISSION_STATUS.md. Live demonstration/viva must be performed by the student; this report does not claim either occurred.')
    heading('Reproducibility')
    para('Python 3.12 with uv.lock; Apple Silicon host. Full stochastic experiments use seeds 0-4. Systems use repeated native/guest workloads. The shared runner records timestamp, platform, dependency versions, source hashes and thread settings. Run: uv sync --frozen; uv run python -m pytest; uv run python -m optlab run --track all; uv run python -m optlab report. xv6 also requires QEMU and a RISC-V toolchain; see README.')
    para('Quick mode writes results/quick and never overwrites full results. Raw data, source references, detailed formulas and the complete Chapter 6 checklist accompany this report. Timings are host observations, not cross-machine guarantees.')
    para('Source map: optlab/track_[a-j].py; tests/; results/[A-J].json; docs/COVERAGE.md; docs/numerical.md; docs/quantum.md; docs/systems.md; docs/COMBINATORIAL_DATABASE_SOFTWARE.md.')
    for t,d in results.items():
        story.append(PageBreak());heading(f'Track {t} - {NAMES[t]}')
        code_url=f'https://github.com/Ninjabeam20/OT_Assign_8/blob/main/optlab/track_{t.lower()}.py'
        result_url=f'https://github.com/Ninjabeam20/OT_Assign_8/blob/main/results/{t}.json'
        story.append(Paragraph(f'<link href="{code_url}" color="#17324d">Source code</link> | <link href="{result_url}" color="#17324d">Full measured results</link>',styles['SmallBody']))
        md += [f'## Track {t} - {NAMES[t]}','',f'[Source code](../optlab/track_{t.lower()}.py) | [Full results](../results/{t}.json)','']
        for text in TEXT[t]:para(text);md += [text,'']
        headers,rows=table_data(t,d)
        cells=[[Paragraph(escape(str(v)),styles['Cell']) for v in row] for row in [headers]+[[fmt(v) for v in r] for r in rows]]
        table=Table(cells,colWidths=[2.8*inch,1.45*inch,2.2*inch],repeatRows=1,hAlign='LEFT')
        table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#dfeaf3')),('VALIGN',(0,0),(-1,-1),'TOP'),('BOTTOMPADDING',(0,0),(-1,-1),5),('TOPPADDING',(0,0),(-1,-1),5),('LINEBELOW',(0,0),(-1,0),.5,colors.HexColor('#54728b')),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f4f7fa')])]))
        story.append(table);story.append(Spacer(1,9))
        md += ['| '+' | '.join(headers)+' |','| '+' | '.join(['---']*len(headers))+' |']+['| '+' | '.join(fmt(v) for v in r)+' |' for r in rows]+['']
        path=figdir/f'{t}.png';figure(t,d,path);story.append(Image(str(path),width=6.45*inch,height=2.36*inch));md += [f'![Track {t}](../output/figures/{t}.png)','']
        para(f'Evidence: results/{t}.json. Full-run source hash: {d["metadata"]["source_sha256"][:16]}. Execution UTC: {d["metadata"]["timestamp_utc"]}.')
    story.append(PageBreak());heading('AI comparison and development failures')
    ai=json.loads((ROOT/'results/AI_COMPARISON.json').read_text())
    para('Original Codex and Gemini outputs passed 100 independently generated small-integer instances, with exhaustive optimum checks for both exact methods. Six Gemini embedded tests pass. Both original branch-and-bound implementations fail on permitted large integers because floating-point upper bounds can prune a better solution. Corrected Codex uses exact rational ordering and integer bounds; accepted NumPy integers are normalized to Python integers to prevent overflow.')
    para('The comparison is not a controlled ranking of foundation models: Codex had assignment context and its original module imports NumPy/SciPy; Gemini received a standard-library-only prompt. Corrected Codex has the benefit of review. The original response claims approximately 2.5 seconds; this is unverified response latency. The Antigravity workflow statement is supplied by the student.')
    cells=[['Original implementation','Small exact checks','Adversarial issue']]+[[label,str(ai['checks'][label]['exact_checks_passed'])+'/200','float bound precision'] for label in ['Codex original','Gemini original']]
    tab=Table([[Paragraph(escape(x),styles['Cell']) for x in r] for r in cells],colWidths=[2.2*inch,1.5*inch,2.75*inch]);story.append(tab);story.append(Spacer(1,10))
    para('Measured timing samples and preserved outputs are in prompts/second-tool/COMPARISON.md and results/AI_COMPARISON.json. Greedy ties may legitimately yield different answers. Tuple-based DP reconstruction costs more than the supplied O(C)-space claim; original analysis also overstated how hard some branch-and-bound benchmarks were.')
    para('Other genuine AI errors: database ILP coefficients were too small for solver tolerance; compiler timing omitted optimization search; Grover comparison omitted classical execution. Each was independently reproduced or inspected, corrected and regression-tested. docs/AI_FAILURE_LOG.md links the evidence. Deliberate mutation faults are kept separate from real AI mistakes.')
    heading('Disclosure and responsibility')
    para('Codex model label from local execution records: gpt-6-astra. Work: planning, code, tests, debugging, review, report; tracks A-J. Supplied Gemini label: Gemini 3.8 Flash (High); work: Track B comparison and draft documentation, corrected after review. Prompt records, visible conversation excerpts, source changes and AI-marked integration commits are retained. No secret credentials are included.')
    heading('What remains human work')
    para('The student must understand and explain the implementations, run the short demonstration and modify code live without AI during the viva. The assignment is not satisfied by possessing generated files. Repository publication status and any remaining evidence requirements are listed honestly in docs/SUBMISSION_STATUS.md.')
    story.append(PageBreak());heading('Answers to the assignment’s final questions')
    answers=[
      '1. Process and inefficiency: simulated campus shuttle routing; index-order routes provide an explicit measured baseline. The recorded dataset makes the choice reproducible.',
      '2. Formulation: minimize total Euclidean arc distance under unique stop visitation, positive indivisible demand, depot flow and vehicle-capacity constraints. See E for equations.',
      '3. Methods: continuous gradients/curvature for smooth losses; discrete exact/heuristic methods for combinatorial choices; submodular greedy only where diminishing returns holds; hybrid quantum methods on suitable small circuits. Coverage maps each required method to code/results.',
      '4. Improvement: consult each measured table. Routing/compilation/index selection/COW yield gains on these workloads; some quantum and parallel cases lose. No single algorithm is universally best.',
      '5. Tradeoffs: exact ILP search costs time; greedy sacrifices quality; process startup can dominate; QML simulation/measurement costs matter; coverage reduction may sacrifice behavioral fault detection.',
      '6. Evidence: analytical/exhaustive references, derivative checks, equivalent native outputs, exact SQL results, full xv6 usertests, fixed seeds, raw samples and locked dependencies.',
      '7. Adaptation: larger instances may need heuristic/local-search methods, sparse curvature, real road constraints, held-out workloads, distributed hardware and noise-aware models. Change the formulation when constraints change.',
      '8. Systems concepts: compiler IR transformations and pass ordering; xv6 page tables/reference counting/fault handling and scheduling; database access paths/storage budgets. Correctness is verified before performance claims.',
      '9. Quantum/parallel advantages and limits: Grover reduces oracle queries but classical simulation is slower; QML accuracy is lower here; parallel results expose startup/IPC overhead. Theoretical, simulated and hardware measurements are explicitly distinguished.',
      '10. AI tools: Codex and supplied Gemini. Review exposed solver scaling, omitted compiler/search timing, incorrect large-integer pruning and unsupported documentation. Original outputs and fixes are preserved.'
    ]
    for answer in answers:para(answer)
    heading('Primary references')
    for source in ['MIT xv6 source and COW lab: github.com/mit-pdos/xv6-riscv; pdos.csail.mit.edu/6.1810/2024/labs/cow.html', 'SciPy MILP documentation: docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.milp.html; SQLite query plans: sqlite.org/eqp.html', 'Adam: arxiv.org/abs/1412.6980; FedAvg: proceedings.mlr.press/v54/mcmahan17a.html; MGDA: arxiv.org/abs/1810.04650; GradNorm: proceedings.mlr.press/v80/chen18a.html', 'Quantum reference links and implementation caveats: docs/quantum.md. CPython JSON source/license: github.com/python/cpython/tree/v3.12.13/Lib/json; docs.python.org/3/license.html']:
        para(source)
    md += ['## AI comparison','', 'The student confirms Gemini 3.8 Flash (High) was used in Google Antigravity IDE for Track B. See [usage statement](../prompts/second-tool/ANTIGRAVITY_EVIDENCE.md).','', 'See [verified comparison](../prompts/second-tool/COMPARISON.md), [failure log](AI_FAILURE_LOG.md), and [coverage checklist](COVERAGE.md).','']+answers
    (ROOT/'docs/REPORT.md').write_text('\n'.join(md)+'\n')
    out=ROOT/'output/pdf/Assignment_8_Technical_Report.pdf';out.parent.mkdir(parents=True,exist_ok=True)
    def footer(canvas,doc):
        canvas.setFont('Helvetica',8);canvas.setFillColor(colors.HexColor('#546b7d'));canvas.drawString(42,25,'Assignment 8 | Measured optimization portfolio');canvas.drawRightString(553,25,str(doc.page))
    SimpleDocTemplate(str(out),pagesize=(595.28,841.89),leftMargin=42,rightMargin=42,topMargin=36,bottomMargin=40,title='Assignment 8 - Optimize Anything',author='AI-assisted student portfolio').build(story,onFirstPage=footer,onLaterPages=footer)
    print(out)

if __name__=='__main__':build_report()
