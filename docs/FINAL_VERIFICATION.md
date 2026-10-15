# Reproducibility and evidence verification

The implemented algorithms and original AI outputs were preserved during submission curation. All ten full result source hashes match their track modules. The six original AI files are protected by `prompts/ORIGINAL_ARTIFACTS_SHA256.json`; both supplied screenshots are copied unchanged with a separate SHA-256 manifest.

## Executed checks

- Current full local audit: 63 tests passed in 5.87s. The submission retains 61 algorithm/native correctness tests; two extra runner-infrastructure checks stay local. A fresh Python 3.12.13 environment installed all 52 locked packages from cache; 63 tests passed there too. Restricted sandboxes need local multiprocessing socket permission for D.
- Clean-environment quick runs B/E/H/I/J completed with outputs separate from full results. Native compiler equivalence is covered by systems tests.
- `scripts/compare_ai.py`: 100 independently generated exhaustive-oracle instances, invalid inputs, repeated timings and adversarial large-integer examples. Gemini's six embedded tests pass; original unrestricted-integer failures remain disclosed.
- Saved G baseline one-hart, optimized one-hart and optimized three-hart full guest logs each contain `ALL TESTS PASSED`. Only those final referenced logs are included; unchanged expensive guest tests were not repeated during curation.
- The report is generated from saved measurements. Its appended screenshots document the second tool's original claims, not independent correctness or latency. The final 15-page report was rendered with Poppler and visually reviewed, including both original screenshot appendix pages. The exact submission suite passed 61 tests in 5.35s; the broader local suite passed 63. Selected-file/hash/link and private-path checks are run before publication.

## Reproduction limits and evidence scope

Host-native compiler metrics were verified on macOS Apple Silicon. Other OS/architecture reproduction is not claimed. A fresh cached environment verifies dependencies but not internet availability. Track J profiling has the absolute local home prefix redacted to `[HOME]`; raw private evidence is retained locally. Source hashes and numerical results are unchanged.

Per-track indexes label retrospective summaries explicitly. Original revised prompts that are not available are not reconstructed as quotations. Supplied screenshots fulfill second-tool interface evidence but do not establish exact response latency or every prompt iteration. Integration commits are dated when the verified artifacts were selected for submission, not backdated to development edits. The earlier broader integration branch and extra local checks remain local; public history includes only faculty deliverables.

## Verified public submission

GitHub confirms `Ninjabeam20/OT_Assign_8` is PUBLIC, with default branch `main`. The complete remote Git tree matches the 108 audited file paths and blob hashes. Selected history contains only faculty deliverables; the old broad local branch, two extra runner checks, 23 duplicate/progress artifacts, environments, vendor trees, private raw evidence and ZIP remain local. The screenshot and original-artifact hash manifests verify unchanged originals.

A clean `git archive` export of the exact submission (without ignored local files or the two extra runner checks) passed **61 tests in 5.60s** using the locked project interpreter. This confirms the published test suite does not depend on the extra local tests or duplicate artifacts.
