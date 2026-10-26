# syntax=docker/dockerfile:1.7
# Build llama.cpp with CUDA support. Model weights are downloaded at worker startup,
# not baked into the image, so GHCR does not need to store a 13+ GB model layer.
FROM nvidia/cuda:12.8.1-devel-ubuntu22.04 AS builder

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates git curl cmake ninja-build build-essential pkg-config \
    libcurl4-openssl-dev libssl-dev libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /src
# Pinned commit referenced by the model card's runtime instructions.
RUN git clone https://github.com/ggerganov/llama.cpp.git && \
    cd llama.cpp && \
    git checkout 4df29be4f4c3673f428170fda944a5b19f743bb8 && \
    curl -fL --retry 4 --retry-all-errors \
      -o HauhauCS-FastMTP-llama.cpp.patch \
      https://huggingface.co/HauhauCS/Qwen3.8-27B-Uncensored-HauhauCS-Aggressive-MTP-GGUF/resolve/main/HauhauCS-FastMTP-llama.cpp.patch && \
    git apply --check HauhauCS-FastMTP-llama.cpp.patch && \
    git apply HauhauCS-FastMTP-llama.cpp.patch

WORKDIR /src/llama.cpp
RUN cmake -S . -B build -G Ninja \
      -DGGML_CUDA=ON \
      -DCMAKE_CUDA_ARCHITECTURES="80;86;89;90;120" \
      -DGGML_NATIVE=OFF \
      -DCMAKE_BUILD_TYPE=Release \
      -DLLAMA_BUILD_SERVER=ON \
      -DLLAMA_BUILD_TESTS=OFF \
      -DLLAMA_BUILD_EXAMPLES=OFF && \
    cmake --build build --target llama-server -j 4

FROM nvidia/cuda:12.8.1-runtime-ubuntu22.04 AS runtime
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080 \
    MODEL_PORT=8081 \
    MODEL_CTX=4096 \
    MODEL_REPO=HauhauCS/Qwen3.8-27B-Uncensored-HauhauCS-Aggressive-MTP-GGUF \
    MODEL_FILE=Qwen3.8-27B-Uncensored-HauhauCS-Aggressive-Q3_K_P.gguf \
    MODEL_DIR=/models \
    MODEL_URL=https://huggingface.co/HauhauCS/Qwen3.8-27B-Uncensored-HauhauCS-Aggressive-MTP-GGUF/resolve/main/Qwen3.8-27B-Uncensored-HauhauCS-Aggressive-Q3_K_P.gguf

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip ca-certificates curl libgomp1 libcurl4 libssl3 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/app
COPY --from=builder /src/llama.cpp/build/bin/ /opt/llama/bin/
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt
COPY app.py .

RUN mkdir -p /models && chmod 755 /models
EXPOSE 8080
HEALTHCHECK --interval=15s --timeout=5s --start-period=900s --retries=3 \
  CMD python3 -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/health', timeout=3)" || exit 1

CMD ["python3", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
