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

# Pre-download the ~56 MB ONNX segmentation model so cold-starts don't stall
# pulling it. open-iris caches the model *inside the installed package*
# (iris/nodes/segmentation/assets/), so it rides along when we COPY /opt/venv
# into the runtime stage — no extra COPY needed for an HF cache directory.
RUN /opt/venv/bin/python -c "import iris; iris.IRISPipeline()"

# Copy the backend project and install it (NON-editable — editable installs
# leave a .pth file pointing at the source tree, which would force us to also
# copy the source into the runtime stage at the same path. Plain install
# bakes the package into site-packages, so /opt/venv is fully self-contained).
COPY apps/inference /build/apps/inference
RUN uv pip install --python /opt/venv/bin/python /build/apps/inference

# ============================================================================
# Stage 2 — runtime: minimal image with only what's needed to run the server.
# ============================================================================
FROM python:3.10-slim-bookworm AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:${PATH}" \
    TANIK_DB_URL="sqlite:////data/tanik.db" \
    JAVA_HOME="/usr/lib/jvm/default-java"

# Runtime libs:
#   libgomp1     — required by onnxruntime
#   libglib2.0-0 — required by opencv-python-headless
#   libstdc++6   — required by some onnxruntime / numpy bindings (provided by base, listed for clarity)
#   default-jre-headless — JVM for the SourceAFIS binding (JPype loads the
#                          vendored sourceafis-3.18.1.jar via this JRE)
RUN apt-get update && apt-get install -y --no-install-recommends \
        libgomp1 libglib2.0-0 default-jre-headless \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --shell /usr/sbin/nologin --uid 10001 tanik

WORKDIR /app

# Copy the prebuilt venv. It contains both the installed tanik_inference
# package and the pre-downloaded ONNX model (cached inside open-iris's
# package directory). No source tree needs to ship to runtime.
COPY --from=builder /opt/venv /opt/venv

# SQLite DB lives in /data so an operator can mount a volume to persist
# enrolled templates across container restarts. Owned by the non-root user.
RUN mkdir -p /data && chown -R tanik:tanik /data /app

USER tanik
ENV HOME=/home/tanik

EXPOSE 8000

# Health check uses the contracted /api/v1/health endpoint.
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/api/v1/health',timeout=3).status==200 else 1)" || exit 1

CMD ["uvicorn", "tanik_inference.main:app", "--host", "0.0.0.0", "--port", "8000"]
