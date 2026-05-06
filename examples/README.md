# Examples

The examples focus on the public Python API and use tiny deterministic
synthetic datasets from `woodpecker.testing`.

## Notebook

- `cmip7_api_example.ipynb`: create a broken synthetic CMIP7 dataset, detect
  applicable fixes, dry-run the changes, apply them in memory, and re-check the
  result.

Run it from an environment where Woodpecker and the bundled plugins are
installed:

```bash
conda activate woodpecker
make dev
jupyter notebook examples/cmip7_api_example.ipynb
```
