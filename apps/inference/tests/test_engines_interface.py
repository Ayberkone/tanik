"""Verifies both engine modules satisfy the BiometricEngine Protocol.

The conformance check is structural — it asserts the modules expose the right
names and shapes, not that the underlying biometrics actually work (those are
the per-engine smoke tests).

The fingerprint engine is parametrised in only when JPype is importable so
the iris conformance check still runs in JVM-less local dev. CI installs
JPype + Temurin, so both engines are exercised there.
"""

import importlib
import importlib.util
import inspect

import pytest

from tanik_inference import iris_engine
from tanik_inference.engines import BiometricEngine

ENGINE_MODULES = [pytest.param(iris_engine, id="iris")]

if importlib.util.find_spec("jpype") is not None:
    ENGINE_MODULES.append(
        pytest.param(importlib.import_module("tanik_inference.fingerprint_engine"), id="fingerprint")
    )


@pytest.mark.parametrize("engine", ENGINE_MODULES)
def test_engine_has_name(engine):
    assert isinstance(engine.name, str) and engine.name


@pytest.mark.parametrize("engine", ENGINE_MODULES)
def test_engine_template_version_returns_string(engine):
    version = engine.template_version()
    assert isinstance(version, str) and "/" in version


@pytest.mark.parametrize("engine", ENGINE_MODULES)
def test_engine_encode_is_async_callable(engine):
    assert inspect.iscoroutinefunction(engine.encode)


@pytest.mark.parametrize("engine", ENGINE_MODULES)
def test_engine_match_is_async_callable(engine):
    assert inspect.iscoroutinefunction(engine.match)


@pytest.mark.parametrize("engine", ENGINE_MODULES)
def test_engine_satisfies_protocol(engine):
    """`runtime_checkable` Protocol gives a structural isinstance check.

    Note: Protocols only check attribute presence at runtime, not signatures —
    the per-attribute tests above cover the shape side.
    """
    assert isinstance(engine, BiometricEngine)
