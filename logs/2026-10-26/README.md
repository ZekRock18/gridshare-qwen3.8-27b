# Deployment evidence archive — 26 October 2026

## Contents

- [GitHub workflow metadata](actions/runs.json): all six setup workflow runs and their outcomes.
- Full text logs: [cancelled source build](actions/run-40285420367.log), [first image build](actions/run-40289582417.log), [skipped verification marker](actions/run-40289635679.log), [failed smoke check](actions/run-40290133571.log), [corrected image build](actions/run-40290374641.log), [successful smoke check](actions/run-40290613596.log).
- [GridShare snapshot](gridshare-snapshot.json): complete test prompt and model answer, token timings, request charge, endpoint configuration, cumulative cost, worker status, metrics and scale-to-zero confirmation.
- [Git history before archival](git-history.txt).
- [SHA-256 inventory](inventory.json): integrity hashes for archived logs, API evidence and local build records.
- [Documentation wiki](../../docs/wiki/Home.md).

Two original Docker build-record artifacts were downloaded locally under `.build-artifacts/40289582417/` and `.build-artifacts/40290374641/` in the project directory. These opaque build records are retained locally and excluded from Git; the public archive contains their filenames and checksums, plus the readable workflow logs. The original artifacts also remain attached to their GitHub runs until GitHub's retention period expires.

## Scope and limitations

This archive preserves all workflow text logs returned by GitHub for the six setup runs. The skipped workflow has an explicit marker because no job logs were returned. The logs were not truncated. Known credential formats are redacted before saving; account profile and wallet identity details were not included.

The GridShare snapshot is an API observation at its embedded UTC capture time, not a continuous event stream. Raw GPU worker stdout/stderr and a complete historical terminal/chat transcript were not available for export. No such logs are fabricated. The successful response and platform metrics are retained as the inference evidence.

At capture time, the worker was offline, zero workers were live, and the endpoint had scaled to zero. The cumulative endpoint charge was INR 1.5828, including additional charges beyond the INR 0.040565 inference request.
