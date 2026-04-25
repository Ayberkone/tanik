"""Vendored third-party binaries shipped with the inference wheel.

The SourceAFIS Java JAR is loaded by `fingerprint_engine` via JPype. Resolving
the path through `importlib.resources` makes it work whether the package is
installed from a wheel, in editable mode, or copied into a Docker image.
"""

from importlib import resources
from pathlib import Path

SOURCEAFIS_JAR_NAME = "sourceafis-3.18.1.jar"


def sourceafis_jar_path() -> Path:
    return Path(resources.files(__name__).joinpath(SOURCEAFIS_JAR_NAME))
