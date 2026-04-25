"""Async-safe wrapper around SourceAFIS (Java) via JPype.

Mirrors the shape of `iris_engine`:
- one process-wide JVM instance, started lazily
- CPU-bound calls offloaded via `run_in_threadpool`
- templates round-trip as bytes so the storage layer stays modality-agnostic

The JVM is started exactly once per process; subsequent calls reuse it. This is
a hard JPype constraint (only one JVM per process for the JVM's lifetime), and
it lines up with FastAPI's single-worker-per-pod deployment model.

JPype is imported lazily so that `import tanik_inference.fingerprint_engine`
does not fail in environments where JPype is not installed (e.g. an
out-of-date local venv). Calls only fail at the point you actually try to
encode or match — the FastAPI app and the iris stack continue to work.
"""

from typing import Optional, Tuple

from fastapi.concurrency import run_in_threadpool

from .vendor import sourceafis_jar_path

name = "fingerprint"

_SOURCEAFIS_VERSION = "3.18.1"

_jvm_started = False


def _ensure_jvm() -> None:
    global _jvm_started
    if _jvm_started:
        return
    import jpype
    import jpype.imports  # noqa: F401  enables `from com.machinezoo... import ...`

    if not jpype.isJVMStarted():
        jpype.startJVM(classpath=[str(sourceafis_jar_path())], convertStrings=False)
    _jvm_started = True


def template_version() -> str:
    return f"sourceafis/{_SOURCEAFIS_VERSION}"


def _encode_sync(image_bytes: bytes) -> Tuple[Optional[bytes], Optional[str]]:
    _ensure_jvm()
    import jpype
    from com.machinezoo.sourceafis import FingerprintImage, FingerprintTemplate

    try:
        java_bytes = jpype.JArray(jpype.JByte)(image_bytes)
        image = FingerprintImage(java_bytes)
        template = FingerprintTemplate(image)
        serialized = template.toByteArray()
        return bytes(serialized), None
    except jpype.JException as exc:
        return None, str(exc.message())
    except Exception as exc:
        return None, str(exc)


async def encode(image_bytes: bytes, **_: object) -> Tuple[Optional[bytes], Optional[str]]:
    return await run_in_threadpool(_encode_sync, image_bytes)


def _match_sync(probe: bytes, gallery: bytes) -> float:
    _ensure_jvm()
    import jpype
    from com.machinezoo.sourceafis import FingerprintMatcher, FingerprintTemplate

    probe_template = FingerprintTemplate(jpype.JArray(jpype.JByte)(probe))
    gallery_template = FingerprintTemplate(jpype.JArray(jpype.JByte)(gallery))
    matcher = FingerprintMatcher(probe_template)
    return float(matcher.match(gallery_template))


async def match(probe: bytes, gallery: bytes) -> float:
    return await run_in_threadpool(_match_sync, probe, gallery)
