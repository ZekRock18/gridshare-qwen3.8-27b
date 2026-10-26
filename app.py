import json
import logging
import math
import os
import subprocess
import threading
import time
from pathlib import Path
from typing import Any

import requests
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger("gridshare-qwen")

PORT = int(os.getenv("PORT", "8080"))
MODEL_PORT = int(os.getenv("MODEL_PORT", "8081"))
MODEL_CTX = int(os.getenv("MODEL_CTX", "4096"))
MODEL_DIR = Path(os.getenv("MODEL_DIR", "/models"))
MODEL_FILE = os.getenv(
    "MODEL_FILE",
    "Qwen3.8-27B-Uncensored-HauhauCS-Aggressive-Q3_K_P.gguf",
)
MODEL_URL = os.getenv(
    "MODEL_URL",
    "https://huggingface.co/HauhauCS/Qwen3.8-27B-Uncensored-HauhauCS-Aggressive-MTP-GGUF/resolve/main/"
    + MODEL_FILE,
)
MODEL_PATH = MODEL_DIR / MODEL_FILE
LLAMA_SERVER = os.getenv("LLAMA_SERVER", "/opt/llama/bin/llama-server")
MODEL_ID = os.getenv("MODEL_ID", "qwen3.8-27b-aggressive-q3")
UPSTREAM = f"http://127.0.0.1:{MODEL_PORT}"
STATE: dict[str, Any] = {
    "phase": "starting",
    "ready": False,
    "error": None,
    "started_at": time.time(),
}
MODEL_PROCESS: subprocess.Popen | None = None
LOCK = threading.Lock()

app = FastAPI(title="GridShare Qwen3.8-27B wrapper", version="1.0.0")


def set_state(phase: str, error: str | None = None) -> None:
    with LOCK:
        STATE["phase"] = phase
        STATE["error"] = error
        if phase != "ready":
            STATE["ready"] = False
        else:
            STATE["ready"] = True


def download_model() -> None:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    if MODEL_PATH.exists() and MODEL_PATH.stat().st_size > 10_000_000_000:
        log.info("Using existing model file at %s (%.2f GB)", MODEL_PATH, MODEL_PATH.stat().st_size / 1e9)
        return

    log.info("Downloading model file (~13.44 GB) from Hugging Face; first cold start may take several minutes.")
    tmp = MODEL_PATH.with_suffix(MODEL_PATH.suffix + ".partial")
    # Resume a partial download on retry within the same worker filesystem.
    command = [
        "curl", "-fL", "--retry", "5", "--retry-delay", "2",
        "--retry-all-errors", "--connect-timeout", "30",
        "-C", "-", MODEL_URL, "-o", str(tmp),
    ]
    result = subprocess.run(command, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"Model download failed (curl exit {result.returncode})")
    size = tmp.stat().st_size if tmp.exists() else 0
    if size < 10_000_000_000:
        raise RuntimeError(f"Downloaded model is unexpectedly small ({size} bytes); refusing to load it")
    tmp.replace(MODEL_PATH)
    log.info("Model downloaded: %.2f GB", MODEL_PATH.stat().st_size / 1e9)


def boot_model() -> None:
    global MODEL_PROCESS
    try:
        set_state("downloading")
        download_model()
        if not Path(LLAMA_SERVER).exists():
            raise RuntimeError(f"llama-server binary not found at {LLAMA_SERVER}")

        set_state("loading")
        cmd = [
            LLAMA_SERVER,
            "--model", str(MODEL_PATH),
            "--host", "127.0.0.1",
            "--port", str(MODEL_PORT),
            "--ctx-size", str(MODEL_CTX),
            "--parallel", "1",
            "--n-gpu-layers", "all",
            "--batch-size", "512",
            "--ubatch-size", "128",
            "--flash-attn", "on",
            "--jinja",
        ]
        log.info("Starting llama.cpp server with context=%s", MODEL_CTX)
        log.info("Command: %s", " ".join(cmd))
        MODEL_PROCESS = subprocess.Popen(
            cmd,
            stdout=None,
            stderr=None,
            env=os.environ.copy(),
        )

        deadline = time.time() + 840
        while time.time() < deadline:
            if MODEL_PROCESS.poll() is not None:
                raise RuntimeError(f"llama-server exited early with code {MODEL_PROCESS.returncode}")
            try:
                response = requests.get(f"{UPSTREAM}/health", timeout=3)
                if response.status_code == 200:
                    set_state("ready")
                    log.info("Model is ready")
                    return
            except requests.RequestException:
                pass
            time.sleep(2)
        raise RuntimeError("Timed out waiting for llama-server readiness")
    except Exception as exc:
        log.exception("Model startup failed")
        set_state("failed", str(exc))


@app.on_event("startup")
def startup_event() -> None:
    thread = threading.Thread(target=boot_model, daemon=True, name="model-bootstrap")
    thread.start()


@app.on_event("shutdown")
def shutdown_event() -> None:
    global MODEL_PROCESS
    if MODEL_PROCESS and MODEL_PROCESS.poll() is None:
        MODEL_PROCESS.terminate()
        try:
            MODEL_PROCESS.wait(timeout=10)
        except subprocess.TimeoutExpired:
            MODEL_PROCESS.kill()


@app.get("/")
def root() -> dict[str, Any]:
    return {
        "service": "GridShare Qwen3.8-27B Q3_K_P",
        "phase": STATE["phase"],
        "ready": STATE["ready"],
        "health": "/health",
        "invoke": "POST /run",
    }


@app.get("/health")
def health():
    if STATE["ready"] and MODEL_PROCESS is not None and MODEL_PROCESS.poll() is not None:
        set_state("failed", f"llama-server exited with code {MODEL_PROCESS.returncode}")
    if STATE["ready"]:
        return {"status": "ok", "ready": True, "model": MODEL_ID}
    # GridShare should keep polling until its warm-up timeout.
    return JSONResponse(
        status_code=503,
        content={
            "status": STATE["phase"],
            "ready": False,
            "error": STATE["error"],
        },
    )


def normalize_input(payload: dict[str, Any]) -> dict[str, Any]:
    if "messages" in payload:
        messages = payload["messages"]
    elif "prompt" in payload:
        messages = [{"role": "user", "content": str(payload["prompt"])}]
    elif "input" in payload and isinstance(payload["input"], str):
        messages = [{"role": "user", "content": payload["input"]}]
    else:
        raise HTTPException(
            status_code=400,
            detail="Expected input.prompt (string) or input.messages (array).",
        )

    if not isinstance(messages, list) or not messages or any(
        not isinstance(message, dict)
        or message.get("role") not in {"system", "user", "assistant", "tool"}
        or not isinstance(message.get("content"), str)
        for message in messages
    ):
        raise HTTPException(status_code=400, detail="messages must be a nonempty array of text messages with valid roles.")
    try:
        max_tokens = min(max(int(payload.get("max_tokens", 256)), 1), 1024)
        temperature = float(payload.get("temperature", 1.0))
        top_p = float(payload.get("top_p", 0.95))
        top_k = int(payload.get("top_k", 20))
        if not math.isfinite(temperature) or not 0 <= temperature <= 2:
            raise ValueError("temperature must be between 0 and 2")
        if not math.isfinite(top_p) or not 0 < top_p <= 1 or top_k < 0:
            raise ValueError("top_p must be in (0, 1] and top_k must be nonnegative")
    except (TypeError, ValueError, OverflowError) as exc:
        raise HTTPException(status_code=400, detail=f"Invalid generation parameters: {exc}") from exc

    body: dict[str, Any] = {
        "model": MODEL_ID,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "top_p": top_p,
        "top_k": top_k,
        "stream": False,
    }
    if payload.get("enable_thinking") is False:
        body["chat_template_kwargs"] = {"enable_thinking": False}
    elif isinstance(payload.get("chat_template_kwargs"), dict):
        body["chat_template_kwargs"] = payload["chat_template_kwargs"]
    return body


@app.post("/run")
def run(payload: dict[str, Any]):
    # GridShare sends {"input": {...}}. The Test Console may wrap this for you.
    inner = payload.get("input", payload)
    if not isinstance(inner, dict):
        raise HTTPException(status_code=400, detail="Expected a JSON object in 'input'.")

    health()
    if not STATE["ready"]:
        raise HTTPException(
            status_code=503,
            detail={"phase": STATE["phase"], "error": STATE["error"], "message": "Model is not ready yet."},
        )

    body = normalize_input(inner)
    try:
        response = requests.post(
            f"{UPSTREAM}/v1/chat/completions",
            json=body,
            timeout=285,
        )
    except requests.RequestException as exc:
        log.exception("Upstream inference request failed")
        raise HTTPException(status_code=502, detail=f"Inference server request failed: {exc}") from exc

    if response.status_code >= 400:
        log.error("llama.cpp returned %s: %s", response.status_code, response.text[:2000])
        return JSONResponse(
            status_code=502,
            content={"error": "llama.cpp inference failed", "upstream_status": response.status_code, "details": response.text[:2000]},
        )
    try:
        return response.json()
    except ValueError:
        return {"output": response.text}
