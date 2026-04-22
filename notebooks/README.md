# Notebooks

Exploratory / teaching notebooks. Run from the repo root.

## 00_iris_spike.ipynb — Phase 0

End-to-end walkthrough of Worldcoin's `open-iris` pipeline on sample iris captures. Visualizes every stage from raw image through segmentation, geometry, rubber-sheet normalization, and the final iris code, then compares same-eye vs different-eye Hamming distances on 24 + 96 pairs.

### First-time setup

The notebook needs Python **3.10** (`open-iris` upstream supports 3.8–3.10; 3.10 is our pin). The setup below uses [`uv`](https://github.com/astral-sh/uv) to install a managed Python without touching the system interpreter; if you already have a Python 3.10 on `$PATH` you can skip to step 3.

```bash
# 1. Install uv (one-time, installs to ~/.local/bin)
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"

# 2. Install a managed CPython 3.10
uv python install 3.10

# 3. Create the repo-local virtual environment
uv venv .venv --python 3.10

# 4. Install open-iris with the SERVER profile + Jupyter
IRIS_ENV=SERVER uv pip install --python .venv/bin/python \
    "git+https://github.com/worldcoin/open-iris.git"
uv pip install --python .venv/bin/python jupyter notebook ipykernel

# 5. Register the venv as a Jupyter kernel
.venv/bin/python -m ipykernel install --user --name tanik \
    --display-name "Python 3 (tanik venv)"
```

First pipeline construction downloads a ~56 MB ONNX segmentation model into the user's Hugging Face cache — budget a minute for that on the first run.

### Running the notebook

```bash
.venv/bin/jupyter notebook notebooks/00_iris_spike.ipynb
```

Select the **Python 3 (tanik venv)** kernel. Run cells top-to-bottom. The data-fetch cell downloads ~20 iris images into `notebooks/data/` (gitignored) on the first execution; subsequent runs are no-ops.

To re-execute non-interactively:

```bash
.venv/bin/jupyter nbconvert --to notebook --execute \
    notebooks/00_iris_spike.ipynb --output 00_iris_spike.ipynb \
    --ExecutePreprocessor.timeout=600
```

### Sample data — provenance

The notebook pulls from two places, both gitignored on disk:

| Source | Role | Provenance |
|---|---|---|
| `wld-ml-ai-data-public.s3.amazonaws.com/public-iris-images/example_orb_image_{1,2,3}.png` | Sanity check: 2 captures of subject 1 + 1 of subject 2 | Exactly the images `open-iris`'s own `colab/MatchingEntities.ipynb` fetches. Publicly hosted by Worldcoin for that demo. |
| `raw.githubusercontent.com/emrealtann/IrisRecognition/master/MMU/{0..3}/*.bmp` | Full same-vs-different separation experiment (4 subjects × 4 captures) | MIT-licensed GitHub mirror of the MMU Iris Database (Multimedia University, Malaysia). Academic research use only — see `docs/datasets.md`. |

Images are not committed to this repository. If you want to run the notebook offline, pre-populate `notebooks/data/` using the URLs above, or keep them in a separate path and adjust `DATA_DIR`.

### Expected Phase 0 result

With the bundled data, the separation plot should show:

- Same-eye pairs clustered between roughly 0.05 and 0.30.
- Different-eye pairs clustered between roughly 0.40 and 0.50.
- Zero overlap — every same-eye pair comfortably below the 0.37 operating threshold, every different-eye pair comfortably above.

If the notebook fails to download data, check outbound network access to GitHub raw and the Worldcoin S3 bucket. If the pipeline produces `error != None` on a given image, the ONNX model probably didn't download — `iris.IRISPipeline()` must succeed offline once the model is cached.
