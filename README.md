# Qwen3.8-27B GGUF on GridShare Serverless

This repository builds a public GHCR Docker image for GridShare's custom serverless container interface.

It runs the **Q3_K_P** text GGUF from:

`HauhauCS/Qwen3.8-27B-Uncensored-HauhauCS-Aggressive-MTP-GGUF`

Model file: `Qwen3.8-27B-Uncensored-HauhauCS-Aggressive-Q3_K_P.gguf` (~13.44 GB).

## Important before deploying

- This is a best-effort community deployment, not an official GridShare or model-author image.
- GridShare's serverless feature is documented as beta. Confirm its current image-pull and worker-startup behavior before spending your balance.
- The container downloads the 13.44 GB model at worker startup. The first cold start therefore depends on download speed and must fit GridShare's configured warm-up timeout (up to 900 seconds per GridShare docs).
- The model itself needs more VRAM than the GGUF file size. Start with a GPU that has **at least 20–24 GB VRAM**. The app's default context is deliberately limited to 4096 tokens. The 3090/4090 24 GB cards are the sensible first target; an A100/H100 may also work.
- `Min VRAM = 0` means GridShare can pick any GPU; it does **not** guarantee enough memory for this model. If the UI allows it, set minimum VRAM to 24 GB for the first model test. If you must leave it at 0, the endpoint can fail on a smaller GPU.
- This first version serves text only. It does not download the vision projector or use the optional HauhauCS FastMTP sidecar.
- No Hugging Face token is required for this public model repository.

## What the container exposes

- `GET /health` on port `8080`: returns HTTP 200 only when the model server is loaded and ready.
- `POST /run` on port `8080`: accepts GridShare's `{"input": {...}}` envelope and returns a JSON response.
- The wrapper forwards requests to a local `llama.cpp` OpenAI-compatible chat-completions endpoint.

## Files

- `Dockerfile`: digest-pinned official llama.cpp CUDA server (b11889) plus the Python HTTP wrapper.
- `app.py`: GridShare wrapper, model download/startup, health check and request forwarding.
- `.github/workflows/publish.yml`: builds and publishes the image to GitHub Container Registry (GHCR) on push to `main`.
- `.dockerignore`: keeps repository build context small.

## Publish the image to GHCR

1. Create a GitHub repository, for example `gridshare-qwen3.8-27b`.
2. Upload all files in this repository to its root.
3. In GitHub, open **Settings → Actions → General** and allow GitHub Actions to run.
4. Push the files to the `main` branch. The workflow builds the image and publishes:
   `ghcr.io/zekrock18/gridshare-qwen3.8-27b:latest`
5. Open the repository's **Packages** section (or your GitHub profile → Packages) and set the package visibility to **Public** if it is not public already.
6. Copy the exact, lowercase image URI shown by GHCR. GridShare must be able to pull it anonymously.

The workflow uses the built-in `GITHUB_TOKEN`; no personal access token needs to be stored in repository secrets.

## GridShare endpoint settings

In the Docker image dropdown choose **Your own image...**, then paste the image URI below. Wait for the GitHub Actions build to succeed and make the GHCR package public before invoking it.

Use the exact image URI created by your workflow:

- **Endpoint name:** `qwen38-27b-q3`
- **Docker image:** `ghcr.io/zekrock18/gridshare-qwen3.8-27b:latest`
- **Min VRAM:** `20` GB for the budget test; GPU inference is still to be verified.
- **Preferred GPU family:** `RTX 4000 Ada` via API. This was the cheapest available compatible NVIDIA GPU listed on 2026-10-26. The UI dropdown does not offer this family; use `gridshare-endpoint.json` through the API. Do not substitute Any GPU if you need to retain this cost preference.
- **Environment variables** (model URL and filename are already built in):
  - `MODEL_CTX` = `2048`
  - `MODEL_PORT` = `8081`
- **Min workers:** `0`
- **Max workers:** `1`
- **Startup wait:** `900` seconds (maximum documented by GridShare)
- **GPU selection:** if the form offers only the listed families and no minimum VRAM field, choose RTX 4090 or RTX 3090 first.

Do not set Min workers to 1; that can incur warm-worker charges. GridShare's docs say idle workers scale to zero after 10 minutes.

### First invocation

After the endpoint becomes ready, test with a small payload:

```json
{
  "input": {
    "prompt": "In two sentences, explain what a GPU does.",
    "max_tokens": 96,
    "temperature": 0.7
  }
}
```

The GridShare Test Console may ask only for the *inner input* because it wraps the value in `{"input": ...}` automatically. If so, paste:

```json
{
  "prompt": "In two sentences, explain what a GPU does.",
  "max_tokens": 96,
  "temperature": 0.7,
  "enable_thinking": false
}
```

If the first start times out, check GridShare's startup timeout and worker logs before retrying; repeated cold starts may repeat the model download. If it reports CUDA out-of-memory, stop/delete the endpoint and try a GPU with more VRAM or lower `MODEL_CTX` to `2048`.

### API test for a long cold start

The dashboard's synchronous console waits only 300 seconds, even with a 900-second worker warmup. Use the asynchronous API for the first cold request. Set `GRIDSHARE_TOKEN` locally to a GridShare API key (never a GitHub token). From PowerShell in this folder:

```powershell
$headers = @{Authorization = "Bearer $env:GRIDSHARE_TOKEN"}
# Create once. If you already created the endpoint in the UI, list endpoints
# with GET https://gridshare.in/v1/serverless/endpoints/ and use its id instead.
$endpoint = Invoke-RestMethod https://gridshare.in/v1/serverless/endpoints/ -Method Post -Headers $headers -ContentType 'application/json' -Body (Get-Content gridshare-endpoint.json -Raw)
$body = @{input = (Get-Content test-input.json -Raw | ConvertFrom-Json)} | ConvertTo-Json -Depth 10
$job = Invoke-RestMethod "https://gridshare.in/v1/serverless/$($endpoint.id)/run-async" -Method Post -Headers $headers -ContentType 'application/json' -Body $body
do {
    Start-Sleep -Seconds 10
    $result = Invoke-RestMethod "https://gridshare.in/v1/serverless/requests/$($job.request_id)" -Headers $headers
    $result | ConvertTo-Json -Depth 20
} while ($result.status -in @('queued', 'pending', 'running', 'processing'))
```

After testing, delete the endpoint in the dashboard to stop any retained warm worker charges.

## Input schema

Either prompt-style input:

```json
{
  "prompt": "Hello!",
  "max_tokens": 128,
  "temperature": 0.7,
  "top_p": 0.95,
  "top_k": 20
}
```

or chat messages:

```json
{
  "messages": [
    {"role": "user", "content": "Hello!"}
  ],
  "max_tokens": 128
}
```

Optional `enable_thinking: false` is forwarded as `chat_template_kwargs` for compatible llama.cpp builds.

## Cost safety

- Start with one worker and scale-to-zero.
- The dashboard states that workers retained after requests are billed at 20% for up to ten minutes, even with minimum workers set to zero. Delete your test endpoint when finished to stop retained-worker charges.
- Run only one short request initially.
- Check the GridShare wallet and endpoint logs after the test.
- Delete the endpoint when finished. GridShare says cold starts are not billed, active compute is billed per 100 ms, and warm workers are billed at 20% of the active rate when retained.
- The price depends on the GPU actually allocated; ₹0.005/sec is the starting rate, not a guaranteed rate for a 3090/4090/A100/H100.

## Troubleshooting

- **Image pull error:** verify the GHCR package is Public and use the exact lowercase `ghcr.io/...:latest` URI.
- **Health timeout:** model download/load may take too long; check logs and confirm startup wait is set to 900 seconds.
- **CUDA OOM:** choose a 24 GB or larger GPU and lower context to 2048.
- **Unsupported model architecture / flags:** the image uses the official CUDA server b11889, pinned by digest. The custom HauhauCS patch is for its optional FastMTP sidecar, which this text-only deployment does not load.
- **Request timeout:** GridShare documents a synchronous wait of up to 300 seconds; use short prompts and low `max_tokens` for the first test.
