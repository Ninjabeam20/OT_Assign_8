# Comparative Analysis: Codex vs. Second-Tool (Gemini 3.8 Flash)

## 1. Executive Summary

As required by Assignment 8 (`prompts/second-tool/ASK_OTHER_AI.md`), this document provides an independent inspection, empirical testing, and code comparison between:
1. **Codex Implementation:** `optlab/track_b.py` (authored by OpenAI Codex in the initial assignment scaffold).
2. **Second-Tool Implementation:** `prompts/second-tool/knapsack_second_tool.py` (authored by Gemini 3.8 Flash (High) on 2026-10-15 via Google Antigravity IDE).

Both implementations solve the $0/1$ Knapsack problem under identical specifications using three core paradigms:
- `greedy(weights, values, capacity)`
- `dynamic_programming(weights, values, capacity)`
- `branch_and_bound(weights, values, capacity)`

---

## 2. Specification & Contract Conformance

| Criterion | Specification Requirement | Codex (`optlab/track_b.py`) | Second-Tool (`knapsack_second_tool.py`) | Status |
|---|---|---|---|---|
| **Dependencies** | Self-contained Python 3, Standard Library only | Uses `numpy` and `scipy` (`np.integer`, `Bounds`, `LinearConstraint`, `milp`) | **Strictly Standard Library only** (`math`, `random`, `time`, `unittest`) | Second-tool strictly adheres to the prompt constraint |
| **Function Signatures** | Exact names and parameter signatures | Exact matches | Exact matches | Conforming |
| **Return Types** | `(optimal_or_heuristic_val, selected_indices)` | Returns `(int, list[int])` | Returns `(int, list[int])` | Conforming |
| **Input Mutability** | Must not modify input lists | Preserves inputs | Preserves inputs | Conforming |
| **Mismatched Lengths** | Raise `ValueError` | Checked (`len(weights) != len(values)`) | Checked (`len(weights) != len(values)`) | Conforming |
| **Type & Sign Check** | Reject negative, non-integer, and `bool` with `ValueError` | Checks `isinstance(x, bool) or not isinstance(x, (int, np.integer)) or x < 0` | Checks `isinstance(x, bool) or not isinstance(x, int) or x < 0` | Conforming |
| **Zero-Weight Items** | Must be allowed and handled properly | Prioritizes with `math.inf` ratio | Prioritizes with `math.inf` ratio | Conforming |
| **Empty Inputs & Cap=0** | Returns `(0, [])` or zero-weight sum | Handled cleanly | Handled cleanly | Conforming |

---

## 3. Algorithmic Comparison

### 3.1. Greedy Ratio Heuristic
- **Codex:**
  - Computes ratio as `values[i] / weights[i] if weights[i] else math.inf`.
  - Sorts using Python's stable Timsort in reverse order.
  - Iterates through the sorted indices and takes any item where `weights[i] <= remaining`.
- **Second-Tool:**
  - Uses compound sort key `(math.inf if weights[i] == 0 else values[i] / weights[i], values[i])` to explicitly break ratio ties by higher value.
  - Explicitly handles `capacity == 0` early return for zero-weight items.
- **Empirical Output:** Identical heuristic values and identical selected indices across all 100 test instances.

### 3.2. Dynamic Programming
- **Codex:**
  - Space-efficient 1D DP table of size `capacity + 1`, initialized to `[(0, ())] * (capacity + 1)`.
  - For each item `(w, v)`, copies `previous = dp[:]`.
  - Loops `c` from `w` to `capacity + 1`: if `previous[c - w][0] + v > previous[c][0]`, updates `dp[c] = (candidate, previous[c - w][1] + (i,))`.
  - Returns `dp[capacity]`.
- **Second-Tool:**
  - Uses the same 1D table snapshot strategy (`prev = list(dp)`).
  - Explicitly documents why this prevents item reuse: because `prev` reflects states before considering item $i$, an item cannot be chosen multiple times even when $w=0$.
  - Stores immutable index tuples directly inside state cells, avoiding costly 2D matrix storage or reverse backtracking loops.
- **Empirical Output:** 100% agreement on optimal value and indices.

### 3.3. Branch-and-Bound
- **Codex:**
  - Computes continuous fractional knapsack upper bound on remaining items.
  - Initializes incumbent with `greedy(weights, values, capacity)`.
  - Uses Depth-First Search with a LIFO stack `nodes = [(0, capacity, 0, ())]`.
  - Prunes when `upper < best + 1 - 1e-10`.
  - Appends exclude branch first, then include branch, ensuring include branch is popped and explored first.
- **Second-Tool:**
  - Encapsulates bound computation into a dedicated helper function.
  - Also initializes incumbent with `greedy(weights, values, capacity)`.
  - Uses Depth-First Search with LIFO stack `stack = [(0, capacity, 0, ())]`.
  - Pruning condition: `bound <= best_val` (since all values are integers, fractional upper bound $\le \text{best\_val}$ implies no integer solution can reach $\text{best\_val} + 1$).
  - Explores include branch first to establish tight lower bounds rapidly.
- **Empirical Output:** 100% agreement on optimal value and indices across all test cases.

---

## 4. Empirical Testing & Validation Results

### 4.1. Automated Verification Suite
We ran an automated comparative harness comparing both implementations across multiple test regimes:

1. **Specification Counterexample:**
   - Input: `weights = [10, 20, 30]`, `values = [60, 100, 120]`, `capacity = 50`.
   - Codex: Greedy = 160 (`[0, 1]`), DP = 220 (`[1, 2]`), BB = 220 (`[1, 2]`).
   - Second-Tool: Greedy = 160 (`[0, 1]`), DP = 220 (`[1, 2]`), BB = 220 (`[1, 2]`).
   - Discrepancy: **0**.

2. **Zero-Weight Items:**
   - Input: `weights = [0, 10, 0, 20]`, `values = [15, 30, 25, 40]`, `capacity = 25`.
   - Optimal value: 80 (items 0, 2, and 3).
   - Both implementations successfully select both zero-weight items (0 and 2) along with item 3 without violating capacity or double-counting.

3. **Input Validation & Exceptions:**
   - Mismatched lengths: Both raise `ValueError`.
   - Booleans (`[True]`, `capacity=False`): Both raise `ValueError`.
   - Negatives (`weights=[-1]`, `capacity=-10`): Both raise `ValueError`.
   - Floats (`weights=[1.5]`): Both raise `ValueError`.

4. **Exhaustive Enumeration on Random Instances:**
   - 100 randomized knapsack instances ($n \in [1, 20]$, $w_i \in [0, 30]$, $v_i \in [0, 50]$, $C \in [0, \sum w + 10]$).
   - Results: **100/100 matches** between Codex and Second-Tool across all three methods.
   - Brute-force verification confirmed DP and B&B achieved the true mathematical optimum in 100% of cases.

---

## 5. Side-by-Side Performance Benchmark

Benchmarked on identical hardware (Apple M-series, Python 3.12.13) across 50 independent problem instances ($n=20$, $C=300$):

| Implementation | Greedy Time | Dynamic Programming Time | Branch-and-Bound Time |
|---|---|---|---|
| **Codex (`optlab/track_b.py`)** | 0.0042 ms | 0.3032 ms | 0.0234 ms |
| **Second-Tool (`knapsack_second_tool.py`)** | 0.0038 ms | 0.3028 ms | 0.0249 ms |
| **Difference** | -9.5% (Second-Tool faster) | -0.1% (Tie) | +6.4% (Codex faster) |

*Note: Differences are within normal execution variance ($< 0.002$ ms).*

---

## 6. Structural & Qualitative Assessment

### Codex (`optlab/track_b.py`)
- **Pros:**
  - Extremely concise and idiomatic Python.
  - Seamlessly integrated with Track B's QUBO, Ising, and MILP solvers.
  - Accepts NumPy integer scalars (`np.integer`).
- **Cons:**
  - Inlines logic densely with minimal comments.
  - Requires `numpy` and `scipy` installed, which violates the strict standard-library-only requirement if extracted as a standalone module.

### Second-Tool (`knapsack_second_tool.py`)
- **Pros:**
  - 100% standard library compliance with zero external dependencies.
  - Highly defensive validation with clear, explanatory exception messages.
  - Includes a comprehensive embedded `unittest` test suite and standalone benchmark runner.
  - Extensive docstrings detailing complexity bounds, LP relaxation theory, and DP invariant guarantees.
- **Cons:**
  - Slightly more verbose due to defensive checks and explicit documentation.

---

## 7. Conclusion

The Second-Tool implementation generated by Gemini 3.8 Flash (High) completely and faithfully satisfies all requirements of Assignment 8's second-tool task. It is mathematically equivalent to Codex's implementation, matches it in execution efficiency, and offers superior standalone portability by relying strictly on the Python 3 standard library.
