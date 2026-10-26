# Deployment

[Wiki home](Home.md)

## Model and runtime

- Model repository: https://huggingface.co/HauhauCS/Qwen3.8-27B-Uncensored-HauhauCS-Aggressive-MTP-GGUF
- File: `Qwen3.8-27B-Uncensored-HauhauCS-Aggressive-Q3_K_P.gguf` (13,441,058,944 bytes verified by HTTP HEAD).
- Text inference only; neither the vision projector nor the optional FastMTP draft sidecar is loaded.
- Runtime: official llama.cpp CUDA 12 server b11889, revision `d854d98bae598388ecea1ed84396587e5edc326d`.
- Base image pinned in [Dockerfile](../../Dockerfile) by digest `sha256:b51c252687249a6990ae1c168156cb215c954bfd71f9c434eda9a065b1a40dbe`.
- `LD_LIBRARY_PATH=/app:/usr/local/cuda/lib64` ensures the server finds its libraries when the wrapper runs in `/opt/app`.
- `GET /health` on port 8080 returns 200 only after model readiness, otherwise 503.
- `POST /run` accepts `{"input": {...}}` and forwards to llama.cpp on loopback port 8081.

## Verified endpoint settings

| Field | Value |
| --- | --- |
| Name | `qwen38-27b-q3` |
| Docker image | `ghcr.io/zekrock18/gridshare-qwen3.8-27b:latest` |
| Minimum VRAM | 20 GB |
| Preferred GPU family | `RTX 4000 Ada` |
| Environment | `MODEL_CTX=2048` |
| Minimum workers | 0 |
| Maximum workers | 1 |
| Startup wait | 900 seconds |
| Request timeout | 300 seconds |

The endpoint already exists. Do not create a duplicate just to test it. The UI dropdown did not list RTX 4000 Ada; the API accepted it and allocated an NVIDIA RTX 4000 Ada Generation with 20 GB. Use [gridshare-endpoint.json](../../gridshare-endpoint.json) for recreation. Availability and prices change; this was the cheapest available compatible CUDA GPU checked at deployment time, not a permanent guarantee.

The GPU selection fields were ignored when PATCHing the initial endpoint. The unused 4090 endpoint was therefore deleted and recreated before any requests were submitted. Environment updates did persist through PATCH.

## Publishing

Push implementation changes to `main` to run [publish.yml](../../.github/workflows/publish.yml). It runs the HTTP tests and pushes `latest` plus a `sha-<commit>` tag. The package is public and anonymous manifest access was verified. Use the SHA tag to reproduce a particular build; `latest` may change.

Successful tested image tag: `ghcr.io/zekrock18/gridshare-qwen3.8-27b:sha-39ca308abe6464fcb469a23d9b29fe02ca4b9859`.

The following workflow verifies binary startup and the HTTP wrapper without downloading model weights: [verify-image.yml](../../.github/workflows/verify-image.yml). A successful workflow does not replace a GPU inference test.

Reference: https://gridshare.in/docs
