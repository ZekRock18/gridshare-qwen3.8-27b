# Costs and measured results

[Wiki home](Home.md)

Evidence: [GridShare API snapshot](../../logs/2026-10-26/gridshare-snapshot.json), captured on 26 October 2026 after the worker scaled down.

| Measurement | Observed result |
| --- | --- |
| GPU | NVIDIA RTX 4000 Ada Generation, 20 GB |
| Marketplace hourly price when selected | INR 30.50/hour |
| Context limit | 2048 tokens |
| Prompt tokens | 22 |
| Completion tokens | 69 |
| Active compute | 3.192 seconds |
| Queue/startup wait | 457.0103 seconds |
| End-to-end wall time | Approximately 460.278 seconds |
| Generation speed | 22.8758 tokens/second |
| Inference request charge | INR 0.040565 |
| Endpoint cumulative charge after retention | INR 1.5828 |
| Live workers at archive time | 0 |

The recorded cumulative endpoint charge exceeds the inference charge by INR 1.542235. This reflects additional endpoint billing including warm retention; the snapshot does not provide a separate itemized warm-charge ledger. Request metrics show INR 0.0406 rounded, whereas the endpoint total includes the additional charges. Do not confuse those totals.

Dividing the request charge by active compute gives approximately INR 0.0127083/second. At a nominal 20% warm rate, ten minutes would cost approximately INR 1.525. The actual cumulative total above is the observed API value, not an estimate. The endpoint's generic `effective_rate_per_second_inr` was higher at approximately 0.0229167; actual request billing is the evidence for the serving node's rate.

Keep minimum workers at zero and maximum workers at one for small tests. Minimum zero does not eliminate the retention period following a request. Delete the endpoint when finished if you want to stop retained-worker charges immediately. Creating it again requires the deployment settings.

This was one short prompt, not a benchmark suite. Throughput, memory usage, startup time and pricing may differ for longer prompts, reasoning mode, other GPUs or later deployments. Lower hourly price also does not by itself prove the lowest cost per generated token.
