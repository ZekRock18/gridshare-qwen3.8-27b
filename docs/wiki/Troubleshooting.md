# Troubleshooting

[Wiki home](Home.md)

| Symptom | Checks and action |
| --- | --- |
| Image cannot be pulled | Check the public GHCR package and exact lowercase image URI. |
| Missing `libllama-server-impl.so` | Use the corrected image from commit `39ca308`; its loader path includes `/app`. |
| Health returns 503 during startup | Expected until model download/load completes. Inspect worker status and allow up to the configured 900 seconds. |
| Console times out at 300 seconds | Use the asynchronous request API and poll the same request; avoid duplicate invocations. |
| Request queued with no live workers in trust summary | Inspect the endpoint's `/workers` API. A warming worker was not counted as live in the observed trust response. |
| CUDA out of memory | Keep context at 2048 for this 20 GB GPU. Inspect actual GPU availability before selecting a larger card, which may cost more. |
| GPU selection does not update | GPU fields did not persist through PATCH in this session. Recreate the unused endpoint if needed; do not delete one with work you need to preserve. |
| `Any GPU` chooses incompatible hardware | This image requires NVIDIA CUDA. Memory capacity alone does not make Apple or AMD GPUs compatible. |
| Source compilation is very slow | Use the pinned official CUDA image in the current Dockerfile. The optional FastMTP patch is unnecessary without the draft sidecar. |

Raw GPU-container stdout/stderr was not retrievable through the tested worker-log API route, which returned 404. The archived worker state and inference result are API observations; they are not raw CUDA or download logs.

Never publish API tokens in logs. Rotate credentials exposed in chat. The repository ignores `.env` and `*.env`, and build context excludes them.
