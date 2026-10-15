# Tracks B, E, H and J

## B: binary decisions
Knapsack maximizes sum(v_i x_i) subject to sum(w_i x_i)<=capacity, x_i in {0,1}. Greedy orders by value/weight; dynamic programming stores immutable predecessor tuples so zero-weight items cannot be reused; branch-and-bound uses a fractional-knapsack upper bound; SciPy/HiGHS solves the ILP. Tiny random instances are independently exhaustively enumerated. Five 24-item instances use capacity 100, integer weights 1..29 and values 1..79. All methods see identical data; time samples follow a warm-up.

Max-Cut on the four-cycle is min x'Qx with negative diagonal degree and positive symmetric adjacency. Under x=(1-s)/2 the exact constant/field/coupling terms are verified for every bitstring. A separate cardinality-two example adds P(sum(x)-2)^2 with P=sum(values)+1, exceeding every possible objective benefit from violating cardinality.

## E: shuttle routing case study
A simulated campus shuttle starts/ends at a depot. Stops have indivisible passenger demands 1..3 and vehicle capacity six. Coordinates are uniform in a 6km square, seed 0..4, with 5 and 9 stops; every full dataset is saved. Baseline visits stops by index, closing a route at capacity. Nearest-neighbor chooses the nearest feasible stop. Both are compared to a binary-arc CVRP ILP with load-based MTZ constraints. Objective is total Euclidean distance, not money or time. The depot is (0,0); there is no fleet limit, traffic or time window.

The baseline is a reproducible inefficient process, not an observed campus transport service. Raw coordinates and routes make it inspectable. Positive demands eliminate customer-only subtours through the load inequalities. Each stop has exactly one incoming/outgoing edge; depot flow balances. HiGHS has a 20-second per-instance limit; incumbent routes, status, bound and gap are saved. Exact independent permutation/partition enumeration tests four stops. More passengers, roads or time windows require changing the model rather than claiming these results transfer automatically.

## H: database index selection
SQLite stores 50,000 synthetic sales rows per seed with integer currency amounts, avoiding floating-point SUM reordering errors. Five fixed queries exercise customer filters, region filters, date ranges, combined filters and grouping. Five candidate indexes include simple and composite indexes. Index sizes use occupied SQLite pages, excluding the freelist. Budget is 40% of the sum of individual index sizes. Isolated warm-cache latency savings are estimates in an additive knapsack model; greedy and binary ILP select indexes under this budget. Every selected configuration is then measured, so interactions are exposed rather than assumed away.

Query results must match exactly and hashes are retained. EXPLAIN QUERY PLAN outputs, sequential-query throughput, median latency, raw repetitions, and storage are saved. SQLite has no PostgreSQL-style EXPLAIN ANALYZE; runtime is measured separately. These experiments compare index choices while leaving SQLite's query planner active. Selection costs and warm-cache conditions are explicit. Normalizing ILP gains avoids absolute solver objective tolerances overwhelming nanosecond-scale inputs.

## J: software-engineering optimization
The realistic target is the public CPython standard-library json package, not the small educational compiler. Source version, line count and PSF attribution are recorded. Cases cover scalar/container roundtrips, Unicode, invalid syntax, custom parsing, circular references and NaN policy; deliberately redundant cases provide a measurable test-reduction opportunity. Coverage collection traces Python lines; the C accelerator remains active and untraced. The constraint preserves every line observed in this candidate suite, not every line in CPython.

A cProfile baseline identifies work. Weighted set cover minimizes measured case execution time subject to each observed line remaining covered. Compare full suite, naive prefix, greedy new-coverage/cost and exact ILP. Raw repeated suite times and optimization overhead are reported. Four deliberate API mutations test behavior preservation. The saved reduced suites can retain 100% of observed line coverage while missing a mutation detected by the full suite: this is a key negative result, not a correctness guarantee. Source readability is unchanged; maintaining instrumentation and an evolving coverage matrix adds maintenance cost.

## Primary references
- SciPy MILP: https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.milp.html
- SQLite query plans: https://sqlite.org/eqp.html
- CPython JSON source: https://github.com/python/cpython/tree/v3.12.13/Lib/json
- CPython license: https://docs.python.org/3/license.html
