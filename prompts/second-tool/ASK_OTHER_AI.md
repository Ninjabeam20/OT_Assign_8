# What you should do
Paste the prompt below into one other AI tool (ChatGPT, Claude, Gemini, etc.). Save its FULL answer/code and any follow-up prompts in this folder. Tell Codex the tool and visible model name, date, approximate response time, and number of attempts. Export the chat or take screenshots. Never invent a model version that the interface does not show.

## Exact prompt to paste
I am comparing AI-generated implementations for an Optimization Techniques assignment. Write a self-contained Python 3 module using only the standard library to solve 0/1 knapsack using (1) greedy value/weight ratio, (2) exact dynamic programming, and (3) exact branch-and-bound using a fractional-knapsack upper bound. Each item can be chosen at most once. Inputs are lists of nonnegative integer weights and values and a nonnegative integer capacity. Zero-weight items are allowed. Reject mismatched lengths, negative inputs, non-integer inputs, and booleans with ValueError. Empty inputs and zero capacity must work.

Use these exact functions:
greedy(weights, values, capacity) -> (optimal_or_heuristic_value, selected_original_indices)
dynamic_programming(weights, values, capacity) -> (optimal_value, selected_original_indices)
branch_and_bound(weights, values, capacity) -> (optimal_value, selected_original_indices)

Return selected indices as a list without duplicates; ties may be broken arbitrarily. Do not modify inputs. Include unittest tests, a small fair timing comparison, complexity explanations, and a concrete counterexample where greedy fails. Example: weights=[10,20,30], values=[60,100,120], capacity=50; exact answer 220, whereas ratio greedy yields 160. Include a zero-weight example. Explain pruning validity and ensure dynamic-programming reconstruction never reuses an item. No internet/API calls, filesystem writes, eval/exec, or installation commands in the module. Provide the complete code in a single code block, followed by a concise explanation. Do not claim benchmarks you have not run.

## What to return to Codex
1. Full response and code, without silently correcting mistakes.
2. Tool/model label shown in the UI, date, response time (approximate is fine).
3. Every follow-up prompt and response, if any.
4. Chat export or screenshots as evidence.

Codex will independently inspect and test the response before running it, compare it with the same-task Codex implementation, and write the comparison. Do not share private data or API keys.
