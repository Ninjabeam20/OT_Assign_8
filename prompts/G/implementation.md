# Actual task prompt and implementation evidence
Parent task required genuine xv6-riscv lottery scheduling AND copy-on-write fork, CPU/mixed/fork workloads, QEMU boot, usertests, baseline comparisons and pinned source diffs. No simulator substitute.

Installed Homebrew qemu and riscv64-elf-gcc. git clone failed with TLS timeout; fetched MIT's official GitHub codeload archive, then fetched exact commit archive and compared kernel sources. Commit: 4ded343d5d9d40d4e9dcf4867ca45b14170bf364.

COW follows MIT lab requirements: reserved PTE bit, shared page reference counts, store fault handler, kernel copyout handling, read-only text/guard protection. Lottery uses equal tickets and per-hart xorshift PRNG. Benchmarks run both kernels with identical optbench guest program and full upstream usertests.

Primary references: https://github.com/mit-pdos/xv6-riscv and https://pdos.csail.mit.edu/6.1810/2024/labs/cow.html .

Actual outcomes: optimized full usertests passed on one and three harts; baseline full usertests passed on one hart. Initial CPU timings were 0–1 ticks, so workload was increased from 16M to 320M iterations per child and fork count from 40 to 200. Final timing runs were sequential, three repeats each: baseline fork [85,81,81], CPU [13,14,13], mixed [20,20,20]; optimized fork [8,8,8], CPU [13,13,13], mixed [20,20,20]. Full logs preserve initial validation runs separately. No scheduler throughput improvement claimed.

Reviewer-driven runner hardening: regression tests first for zero-duration rejection and explicit full multicore plan; unique per-boot split logs, fresh filesystem, relative paths and repetition/scope metadata. Actual workload and focused three-hart copyout smoke tests passed. Then the complete hardened G runner was executed via `python -m optlab run --track G`: all three full suites passed again, metadata timestamp 2026-10-15T04:31:30.716611+00:00, elapsed 445.51 seconds. Medians remained fork81→8, CPU13→13, mixed20→20. No denominator clipping, no invented fairness data.
