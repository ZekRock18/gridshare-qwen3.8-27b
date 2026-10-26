# syntax=docker/dockerfile:1.7
# Official CUDA 12 server, b11889, pinned by immutable image digest.
# The optional HauhauCS FastMTP sidecar is not used, so no FastMTP patch is needed.
FROM ghcr.io/ggml-org/llama.cpp:server-cuda@sha256:b51c252687249a6990ae1c168156cb215c954bfd71f9c434eda9a065b1a40dbe
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    LLAMA_SERVER=/app/llama-server \
    LD_LIBRARY_PATH=/app:/usr/local/cuda/lib64 \
    PORT=8080 \
    MODEL_PORT=8081 \
    MODEL_CTX=4096 \
    MODEL_REPO=HauhauCS/Qwen3.8-27B-Uncensored-HauhauCS-Aggressive-MTP-GGUF \
    MODEL_FILE=Qwen3.8-27B-Uncensored-HauhauCS-Aggressive-Q3_K_P.gguf \
    MODEL_DIR=/models \
    MODEL_URL=https://huggingface.co/HauhauCS/Qwen3.8-27B-Uncensored-HauhauCS-Aggressive-MTP-GGUF/resolve/main/Qwen3.8-27B-Uncensored-HauhauCS-Aggressive-Q3_K_P.gguf

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-venv ca-certificates curl libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/app
COPY requirements.txt .
RUN python3 -m venv /opt/venv && /opt/venv/bin/pip install --no-cache-dir -r requirements.txt
ENV PATH="/opt/venv/bin:${PATH}"
COPY app.py .

RUN mkdir -p /models && chmod 755 /models
EXPOSE 8080
HEALTHCHECK --interval=15s --timeout=5s --start-period=900s --retries=3 \
  CMD python3 -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/health', timeout=3)" || exit 1

ENTRYPOINT []
CMD ["python3", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
