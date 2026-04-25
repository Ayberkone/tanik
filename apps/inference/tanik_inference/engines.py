"""Modality-agnostic engine contract.

Both `iris_engine` and `fingerprint_engine` satisfy this Protocol structurally.
Routes and storage talk to engines through it, so adding a third modality
later (Phase 4 PAD aside, this is the seam for, e.g., face) does not require
touching the API layer or the persistence layer — only registering the new
engine.

Templates always cross the boundary as `bytes`. Each engine owns its own
serialization format, exposed via `template_version()` so the database row
records what produced it (and can refuse a mismatched matcher later).

`encode` accepts modality-specific keyword arguments. The Protocol does not
enumerate them because they vary by modality (iris needs `eye_side`,
fingerprint will eventually want a finger position). Keeping them as
`**kwargs` keeps the Protocol honest while letting each engine type-check
its own surface internally.
"""

from typing import Optional, Protocol, Tuple, runtime_checkable


@runtime_checkable
class BiometricEngine(Protocol):
    """Contract every modality engine satisfies.

    Engines are module-level singletons (not classes) — this Protocol is
    duck-typed against modules. `name` is the modality identifier the
    storage layer records on each enrolled subject.
    """

    name: str

    def template_version(self) -> str:
        """e.g. ``"open-iris/1.11.1"`` or ``"sourceafis/3.18.1"``."""
        ...

    async def encode(self, image_bytes: bytes, **kwargs) -> Tuple[Optional[bytes], Optional[str]]:
        """Extract a template from a raw image upload.

        Returns ``(template_bytes, None)`` on success, ``(None, error_message)``
        when the engine could not produce a template (no minutiae, segmentation
        failure, etc.). Never raises for normal-shaped inputs; reserves
        exceptions for genuine programmer errors.
        """
        ...

    async def match(self, probe: bytes, gallery: bytes) -> float:
        """Compare two templates and return an engine-native similarity score.

        The semantics of the score (range, whether higher is better, what
        threshold means) are engine-specific and documented at each engine.
        Fusion in Phase 3 normalises them to a common scale.
        """
        ...
