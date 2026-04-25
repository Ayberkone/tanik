# Vendored third-party JARs

The TANIK inference service calls SourceAFIS (Java) in-process via JPype. The
JAR is checked into the repository so that builds are deterministic and offline,
and the Python wheel ships with the JAR included as package data.

## sourceafis-3.18.1.jar

| | |
|---|---|
| Source | https://repo1.maven.org/maven2/com/machinezoo/sourceafis/sourceafis/3.18.1/sourceafis-3.18.1.jar |
| Coordinates | `com.machinezoo.sourceafis:sourceafis:3.18.1` |
| Size | 181,525 bytes |
| SHA-256 | `850582c842a7c7bf4ab87d8e8785674d9e092eb379a021d46bc053d2fc6028c0` |
| License | Apache License 2.0 |
| Upstream | https://sourceafis.machinezoo.com/ — https://github.com/robertvazan/sourceafis-java |

To verify the file matches what is documented above:

```sh
shasum -a 256 sourceafis-3.18.1.jar
```

## Updating

To bump the version: download the new JAR from Maven Central, replace the file,
update the version in:

- `tanik_inference/fingerprint_engine.py` (`_SOURCEAFIS_VERSION`)
- `tanik_inference/vendor/__init__.py` (`SOURCEAFIS_JAR`)
- This file (size, hash, source URL)

Then rerun `pytest -k fingerprint_engine` to confirm the JVM still loads it.
