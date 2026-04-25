# syntax=docker/dockerfile:1.7

# ============================================================================
# Stage 1 — builder: install everything heavy (open-iris, the ONNX model,
# all Python deps) into a self-contained venv at /opt/venv.
# ============================================================================
FROM python:3.10-slim-bookworm AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

# git is needed to install open-iris from the repo URL.
# curl + ca-certificates are needed for the uv installer.
RUN apt-get update && apt-get install -y --no-install-recommends \
        git curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install uv (lightweight Python package manager). It pins itself to ~/.local/bin.
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}"

# Self-contained venv at /opt/venv so the runtime stage just copies it.
RUN uv venv /opt/venv --python 3.10
ENV PATH="/opt/venv/bin:${PATH}"

# Install open-iris first — it is the heaviest dep and rarely changes.
# IRIS_ENV=SERVER is required by open-iris's setup.py.
RUN IRIS_ENV=SERVER uv pip install --python /opt/venv/bin/python \
        "git+https://github.com/worldcoin/open-iris.git"

# open-iris pulls in `opencv-python`, which needs libGL.so.1 — not available
# in slim images. Swap it for `opencv-python-headless` (same `cv2` module,
# no GUI deps). Pin matches the version open-iris transitively brought in.
RUN uv pip uninstall --python /opt/venv/bin/python opencv-python \
    && uv pip install --python /opt/venv/bin/python "opencv-python-headless==4.7.0.68"

# Pre-download the ONNX segmentation model into the HF cache so the runtime
# does not have to fetch ~56 MB on cold start. Cache lives at /root/.cache/huggingface/.
RUN /opt/venv/bin/python -c "import iris; iris.IRISPipeline()"

# Copy the backend project and install it editable. Editable install requires
# the source tree to be present at runtime — we copy it in the runtime stage too.
COPY apps/inference /build/apps/inference
RUN uv pip install --python /opt/venv/bin/python -e /build/apps/inference

# ============================================================================
# Stage 2 — runtime: minimal image with only what's needed to run the server.
# ============================================================================
FROM python:3.10-slim-bookworm AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:${PATH}" \
    TANIK_DB_URL="sqlite:////data/tanik.db"

# Runtime libs:
#   libgomp1     — required by onnxruntime
#   libglib2.0-0 — required by opencv-python-headless
#   libstdc++6   — required by some onnxruntime / numpy bindings (provided by base, listed for clarity)
RUN apt-get update && apt-get install -y --no-install-recommends \
        libgomp1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --shell /usr/sbin/nologin --uid 10001 tanik

WORKDIR /app

# Copy the prebuilt venv, pre-warmed model cache, and source tree.
COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /root/.cache/huggingface /home/tanik/.cache/huggingface
COPY --from=builder /build/apps/inference /app/apps/inference

# SQLite DB lives in /data so an operator can mount a volume to persist
# enrolled templates across container restarts. Owned by the non-root user.
RUN mkdir -p /data && chown -R tanik:tanik /data /home/tanik/.cache /app

USER tanik
ENV HOME=/home/tanik

EXPOSE 8000

# Health check uses the contracted /api/v1/health endpoint.
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/api/v1/health',timeout=3).status==200 else 1)" || exit 1

CMD ["uvicorn", "tanik_inference.main:app", "--host", "0.0.0.0", "--port", "8000"]
