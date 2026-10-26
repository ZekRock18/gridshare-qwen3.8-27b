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

- `Dockerfile`: multi-stage CUDA build of `llama.cpp` and runtime image.
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

Use the exact image URI created by your workflow:

- **Endpoint name:** `qwen38-27b-q3`
- **Docker image:** `ghcr.io/zekrock18/gridshare-qwen3.8-27b:latest`
- **Min VRAM:** `24` GB
- **Preferred GPU family:** `Any` (the 24 GB minimum should filter out smaller GPUs, while allowing compatible RTX 3090/4090 or larger cards)
- **Environment variables** (model URL and filename are already built in):
  - `MODEL_CTX` = `4096`
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
- **Unsupported model architecture / flags:** the model requires a recent Qwen3.8-compatible `llama.cpp`. This Dockerfile checks out the commit specified in the model card and applies its runtime patch. If the upstream model card changes, review its build instructions.
- **Request timeout:** GridShare documents a synchronous wait of up to 300 seconds; use short prompts and low `max_tokens` for the first test.
