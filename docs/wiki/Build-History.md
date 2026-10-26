# Build history

[Wiki home](Home.md)

| Run | Result | What it establishes |
| --- | --- | --- |
| [40285420367](https://github.com/ZekRock18/gridshare-qwen3.8-27b/actions/runs/40285420367) | Cancelled | Source CUDA build reached 137/464 tasks after roughly 40 minutes; replaced with a pinned precompiled runtime. |
| [40289582417](https://github.com/ZekRock18/gridshare-qwen3.8-27b/actions/runs/40289582417) | Success | First image built from official CUDA server b11889 and published publicly. |
| [40289635679](https://github.com/ZekRock18/gridshare-qwen3.8-27b/actions/runs/40289635679) | Skipped | Verification triggered by the cancelled build; no job logs exist. |
| [40290133571](https://github.com/ZekRock18/gridshare-qwen3.8-27b/actions/runs/40290133571) | Failure | Smoke test exposed missing shared-library resolution after the working-directory change. |
| [40290374641](https://github.com/ZekRock18/gridshare-qwen3.8-27b/actions/runs/40290374641) | Success | Corrected image published from commit `39ca308abe6464fcb469a23d9b29fe02ca4b9859`. |
| [40290613596](https://github.com/ZekRock18/gridshare-qwen3.8-27b/actions/runs/40290613596) | Success | Corrected binary started and HTTP wrapper exposed the expected startup health response. |

The subsequent live GridShare test completed successfully on the RTX 4000 Ada. It verified the exact model file, not just the wrapper. See [results](Costs-and-Results.md).

All available workflow text logs, including failed and cancelled attempts, are retained in the [archive](../../logs/2026-10-26/README.md). The Git history snapshot identifies implementation and documentation commits made during setup. Documentation-only archive commits use `[skip ci]` to avoid rebuilding an unchanged application.
