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
        # Use JPype's default conversion settings (don't pin convertStrings —
        # the flag's default has flipped between releases and pinning has
        # caused subtle Java-string handling drift in the past).
        jpype.startJVM(classpath=[str(sourceafis_jar_path())])
    _jvm_started = True


def template_version() -> str:
    return f"sourceafis/{_SOURCEAFIS_VERSION}"


def _encode_sync(image_bytes: bytes) -> Tuple[Optional[bytes], Optional[str]]:
    _ensure_jvm()
    import jpype
    from com.machinezoo.sourceafis import FingerprintImage, FingerprintTemplate

    try:
        # `bytes(...)` is a documented JArray(JByte) constructor input in
        # JPype 1.5+; bytes(serialized) on the way back uses JArray's
        # buffer protocol support.
        image = FingerprintImage(jpype.JArray(jpype.JByte)(bytes(image_bytes)))
        template = FingerprintTemplate(image)
        return bytes(template.toByteArray()), None
    except jpype.JException as exc:
        return None, f"{type(exc).__name__}: {exc.message()}"
    except Exception as exc:
        return None, f"{type(exc).__name__}: {exc}"


async def encode(image_bytes: bytes, **_: object) -> Tuple[Optional[bytes], Optional[str]]:
    return await run_in_threadpool(_encode_sync, image_bytes)


def _match_sync(probe: bytes, gallery: bytes) -> float:
    _ensure_jvm()
    import jpype
    from com.machinezoo.sourceafis import FingerprintMatcher, FingerprintTemplate

    probe_template = FingerprintTemplate(jpype.JArray(jpype.JByte)(bytes(probe)))
    gallery_template = FingerprintTemplate(jpype.JArray(jpype.JByte)(bytes(gallery)))
    matcher = FingerprintMatcher(probe_template)
    return float(matcher.match(gallery_template))


async def match(probe: bytes, gallery: bytes) -> float:
    return await run_in_threadpool(_match_sync, probe, gallery)
