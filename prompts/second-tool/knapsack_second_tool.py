"""0/1 Knapsack: Greedy Heuristic, Dynamic Programming, and Branch-and-Bound.

A self-contained Python 3 module using only the standard library.
Solves the 0/1 Knapsack Problem with:
  1. greedy (value/weight ratio heuristic)
  2. dynamic_programming (exact pseudo-polynomial algorithm)
  3. branch_and_bound (exact search with fractional knapsack upper bound)
"""

import math
import random
import time
import unittest


def validate_inputs(weights, values, capacity):
    """Validate knapsack inputs according to specification.

    Rejects:
      - Mismatched lengths between weights and values
      - Booleans (which are subclasses of int in Python)
      - Non-integer weights, values, or capacity
      - Negative weights, values, or capacity

    Accepts:
      - Nonnegative integer weights and values
      - Nonnegative integer capacity
      - Zero-weight items
      - Empty lists and zero capacity
    """
    if len(weights) != len(values):
        raise ValueError(
            f"Weights length ({len(weights)}) and values length ({len(values)}) must match."
        )

    # Validate capacity
    if isinstance(capacity, bool) or not isinstance(capacity, int) or capacity < 0:
        raise ValueError(
            f"Capacity must be a nonnegative integer, got {repr(capacity)}."
        )

    # Validate items
    for idx, (w, v) in enumerate(zip(weights, values)):
        if isinstance(w, bool) or not isinstance(w, int) or w < 0:
            raise ValueError(
                f"Weight at index {idx} must be a nonnegative integer, got {repr(w)}."
            )
        if isinstance(v, bool) or not isinstance(v, int) or v < 0:
            raise ValueError(
                f"Value at index {idx} must be a nonnegative integer, got {repr(v)}."
            )


def greedy(weights, values, capacity):
    """Greedy heuristic based on value-to-weight ratio.

    Zero-weight items have infinite ratio and are prioritized first.
    Returns:
      (heuristic_value, selected_original_indices)
    """
    validate_inputs(weights, values, capacity)
    if not weights or capacity == 0:
        # Items with weight == 0 can still fit when capacity == 0
        zero_weight_ids = [
            i for i, (w, v) in enumerate(zip(weights, values)) if w == 0 and v > 0
        ]
        total_val = sum(values[i] for i in zero_weight_ids)
        return total_val, zero_weight_ids

    # Sort indices by ratio descending; tie-break by larger value
    # Zero-weight items receive math.inf ratio
    order = sorted(
        range(len(weights)),
        key=lambda i: (
            math.inf if weights[i] == 0 else values[i] / weights[i],
            values[i],
        ),
        reverse=True,
    )

    remaining = capacity
    selected = []
    total_val = 0

    for i in order:
        w = weights[i]
        v = values[i]
        if w <= remaining:
            selected.append(i)
            remaining -= w
            total_val += v

    return total_val, selected


def dynamic_programming(weights, values, capacity):
    """Exact 0/1 knapsack using dynamic programming.

    State space: DP table of size (capacity + 1).
    To guarantee 0/1 choice and prevent reusing items, each item update
    references predecessor states strictly from the prior item's snapshot
    or iterates backward. Here an explicit previous row snapshot guarantees
    immutable reconstruction without item reuse even with zero-weight items.

    Returns:
      (optimal_value, selected_original_indices)
    """
    validate_inputs(weights, values, capacity)
    if not weights:
        return 0, []

    # dp[c] stores (max_value, tuple_of_selected_indices) for capacity c
    dp = [(0, ())] * (capacity + 1)

    for i, (w, v) in enumerate(zip(weights, values)):
        prev = list(dp)
        for c in range(w, capacity + 1):
            cand_val = prev[c - w][0] + v
            if cand_val > prev[c][0]:
                dp[c] = (cand_val, prev[c - w][1] + (i,))

    best_val, best_indices = dp[capacity]
    return best_val, list(best_indices)


def branch_and_bound(weights, values, capacity):
    """Exact 0/1 knapsack using Branch-and-Bound with fractional knapsack upper bound.

    Items are sorted by efficiency (value/weight ratio descending).
    At each search node:
      - We compute the LP relaxation bound (fractional knapsack) on remaining items.
      - If upper_bound <= best_found_value, the branch is pruned.
      - We branch on including or excluding the current item (exploring include first).

    Returns:
      (optimal_value, selected_original_indices)
    """
    validate_inputs(weights, values, capacity)
    if not weights:
        return 0, []

    # Sort items by value/weight ratio descending
    order = sorted(
        range(len(weights)),
        key=lambda i: (
            math.inf if weights[i] == 0 else values[i] / weights[i],
            values[i],
        ),
        reverse=True,
    )

    # Initialize best with greedy heuristic solution
    best_val, best_selected = greedy(weights, values, capacity)
    best_selected = list(best_selected)

    def compute_bound(pos, remaining_cap, current_val):
        """Compute fractional knapsack upper bound on items order[pos:]."""
        bound = float(current_val)
        cap = remaining_cap
        for k in range(pos, len(order)):
            idx = order[k]
            w = weights[idx]
            v = values[idx]
            if w == 0:
                bound += v
            elif w <= cap:
                bound += v
                cap -= w
            else:
                bound += v * (cap / w)
                break
        return bound

    # Depth-First Search with Branch and Bound
    # Stack entries: (pos, remaining_capacity, current_value, tuple_of_indices)
    stack = [(0, capacity, 0, ())]

    while stack:
        pos, rem_cap, cur_val, cur_ids = stack.pop()

        if cur_val > best_val:
            best_val = cur_val
            best_selected = list(cur_ids)

        if pos >= len(order):
            continue

        bound = compute_bound(pos, rem_cap, cur_val)
        # Since all input values are integers, if the relaxed bound cannot exceed
        # best_val, this branch cannot yield a strictly better integer solution.
        if bound <= best_val:
            continue

        item_idx = order[pos]
        item_w = weights[item_idx]
        item_v = values[item_idx]

        # Branch 1: Exclude item
        stack.append((pos + 1, rem_cap, cur_val, cur_ids))

        # Branch 2: Include item (if it fits)
        # Appended after exclude so pop() visits include first (diving deep)
        if item_w <= rem_cap:
            stack.append(
                (pos + 1, rem_cap - item_w, cur_val + item_v, cur_ids + (item_idx,))
            )

    return best_val, best_selected


class TestKnapsackSolvers(unittest.TestCase):
    """Comprehensive unit tests for greedy, dynamic_programming, and branch_and_bound."""

    def test_spec_counterexample(self):
        """Counterexample from specification where greedy fails."""
        weights = [10, 20, 30]
        values = [60, 100, 120]
        capacity = 50

        g_val, g_ids = greedy(weights, values, capacity)
        dp_val, dp_ids = dynamic_programming(weights, values, capacity)
        bb_val, bb_ids = branch_and_bound(weights, values, capacity)

        # Greedy takes item 0 (ratio 6.0) and item 1 (ratio 5.0) -> value 160
        self.assertEqual(g_val, 160)
        self.assertEqual(sorted(g_ids), [0, 1])

        # Exact solutions pick item 1 (w=20) and item 2 (w=30) -> value 220
        self.assertEqual(dp_val, 220)
        self.assertEqual(sorted(dp_ids), [1, 2])
        self.assertEqual(bb_val, 220)
        self.assertEqual(sorted(bb_ids), [1, 2])

    def test_zero_weight_items(self):
        """Zero-weight items must be picked without consuming capacity."""
        weights = [0, 10, 0, 20]
        values = [15, 30, 25, 40]
        capacity = 25

        g_val, g_ids = greedy(weights, values, capacity)
        dp_val, dp_ids = dynamic_programming(weights, values, capacity)
        bb_val, bb_ids = branch_and_bound(weights, values, capacity)

        expected_val = 15 + 25 + 40  # items 0, 2, and 3: weights 0+0+20=20 <= 25, value=80
        self.assertEqual(dp_val, expected_val)
        self.assertEqual(bb_val, expected_val)
        # All three methods must select both zero-weight items
        self.assertIn(0, g_ids)
        self.assertIn(2, g_ids)
        self.assertIn(0, dp_ids)
        self.assertIn(2, dp_ids)
        self.assertIn(0, bb_ids)
        self.assertIn(2, bb_ids)

    def test_empty_inputs_and_zero_capacity(self):
        """Empty inputs and zero capacity must work smoothly."""
        for fn in [greedy, dynamic_programming, branch_and_bound]:
            # Empty items
            val, ids = fn([], [], 10)
            self.assertEqual(val, 0)
            self.assertEqual(ids, [])

            # Zero capacity with no zero-weight items
            val, ids = fn([5, 10], [20, 30], 0)
            self.assertEqual(val, 0)
            self.assertEqual(ids, [])

            # Zero capacity with zero-weight item
            val, ids = fn([0, 5], [15, 20], 0)
            self.assertEqual(val, 15)
            self.assertEqual(ids, [0])

    def test_validation_errors(self):
        """All invalid inputs must raise ValueError."""
        for fn in [greedy, dynamic_programming, branch_and_bound]:
            # Mismatched lengths
            with self.assertRaises(ValueError):
                fn([10], [10, 20], 5)

            # Booleans in weights, values, or capacity
            with self.assertRaises(ValueError):
                fn([True], [10], 5)
            with self.assertRaises(ValueError):
                fn([5], [False], 5)
            with self.assertRaises(ValueError):
                fn([5], [10], True)

            # Negative values
            with self.assertRaises(ValueError):
                fn([-5], [10], 5)
            with self.assertRaises(ValueError):
                fn([5], [-10], 5)
            with self.assertRaises(ValueError):
                fn([5], [10], -1)

            # Non-integers (floats, strings)
            with self.assertRaises(ValueError):
                fn([2.5], [10], 5)
            with self.assertRaises(ValueError):
                fn([5], [10.5], 5)
            with self.assertRaises(ValueError):
                fn([5], [10], 5.5)
            with self.assertRaises(ValueError):
                fn(["5"], [10], 5)

    def test_no_input_mutation(self):
        """Input lists must never be mutated."""
        weights = [10, 20, 30]
        values = [60, 100, 120]
        w_copy = list(weights)
        v_copy = list(values)

        for fn in [greedy, dynamic_programming, branch_and_bound]:
            fn(weights, values, 50)
            self.assertEqual(weights, w_copy)
            self.assertEqual(values, v_copy)

    def test_exact_agreement_on_random_instances(self):
        """DP and Branch-and-Bound must always agree on optimal values."""
        rng = random.Random(42)
        for _ in range(25):
            n = rng.randint(1, 15)
            weights = [rng.randint(0, 30) for _ in range(n)]
            values = [rng.randint(0, 50) for _ in range(n)]
            capacity = rng.randint(0, sum(weights) + 10)

            dp_val, dp_ids = dynamic_programming(weights, values, capacity)
            bb_val, bb_ids = branch_and_bound(weights, values, capacity)

            self.assertEqual(
                dp_val,
                bb_val,
                f"Mismatch on weights={weights}, values={values}, cap={capacity}",
            )
            self.assertEqual(len(dp_ids), len(set(dp_ids)))
            self.assertEqual(len(bb_ids), len(set(bb_ids)))
            self.assertLessEqual(sum(weights[i] for i in dp_ids), capacity)
            self.assertLessEqual(sum(weights[i] for i in bb_ids), capacity)
            self.assertEqual(sum(values[i] for i in dp_ids), dp_val)
            self.assertEqual(sum(values[i] for i in bb_ids), bb_val)


def run_timing_comparison():
    """Run a small, fair benchmark comparing execution times on identical instances."""
    print("\n" + "=" * 65)
    print("FAIR TIMING COMPARISON (Identical instances across methods)")
    print("=" * 65)

    scenarios = [
        ("Small (n=12, C=100)", 12, 100, 50),
        ("Medium (n=20, C=300)", 20, 300, 30),
        ("Hard B&B (n=24, C=500)", 24, 500, 10),
    ]

    rng = random.Random(1337)
    for name, n, capacity, repetitions in scenarios:
        # Generate problem instances
        instances = []
        for _ in range(repetitions):
            w = [rng.randint(1, 40) for _ in range(n)]
            v = [rng.randint(10, 100) for _ in range(n)]
            instances.append((w, v, capacity))

        timings = {"greedy": 0.0, "dynamic_programming": 0.0, "branch_and_bound": 0.0}

        for fn_name, fn in [
            ("greedy", greedy),
            ("dynamic_programming", dynamic_programming),
            ("branch_and_bound", branch_and_bound),
        ]:
            t0 = time.perf_counter()
            for w, v, cap in instances:
                fn(w, v, cap)
            timings[fn_name] = (time.perf_counter() - t0) / repetitions

        print(f"\nScenario: {name} (Averaged over {repetitions} runs)")
        for fn_name, avg_t in timings.items():
            print(f"  {fn_name:<22}: {avg_t * 1e3:8.3f} ms / solve")


if __name__ == "__main__":
    print("=" * 65)
    print("0/1 KNAPSACK SPECIFICATION DEMONSTRATIONS")
    print("=" * 65)

    # 1. Counterexample where greedy fails
    w_ce = [10, 20, 30]
    v_ce = [60, 100, 120]
    c_ce = 50
    g_val, g_ids = greedy(w_ce, v_ce, c_ce)
    dp_val, dp_ids = dynamic_programming(w_ce, v_ce, c_ce)
    bb_val, bb_ids = branch_and_bound(w_ce, v_ce, c_ce)
    print("\n1. Counterexample:")
    print(f"   Weights: {w_ce}, Values: {v_ce}, Capacity: {c_ce}")
    print(f"   Greedy:              Value = {g_val}, Selected = {g_ids}")
    print(f"   Dynamic Programming: Value = {dp_val}, Selected = {dp_ids}")
    print(f"   Branch and Bound:    Value = {bb_val}, Selected = {bb_ids}")

    # 2. Zero-weight items
    w_zw = [0, 15, 0, 10]
    v_zw = [10, 30, 20, 25]
    c_zw = 12
    print("\n2. Zero-weight Item Handling:")
    print(f"   Weights: {w_zw}, Values: {v_zw}, Capacity: {c_zw}")
    print(f"   Greedy:              Value = {greedy(w_zw, v_zw, c_zw)}")
    print(f"   Dynamic Programming: Value = {dynamic_programming(w_zw, v_zw, c_zw)}")
    print(f"   Branch and Bound:    Value = {branch_and_bound(w_zw, v_zw, c_zw)}")

    # 3. Timing comparison
    run_timing_comparison()

    # 4. Run Unittests
    print("\n" + "=" * 65)
    print("RUNNING UNITTEST SUITE")
    print("=" * 65)
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestKnapsackSolvers)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)
