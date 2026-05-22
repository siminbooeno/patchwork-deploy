# patchwork-deploy

Minimal deployment pipeline runner using YAML configs with rollback and dry-run support.

---

## Installation

```bash
pip install patchwork-deploy
```

Or install from source:

```bash
git clone https://github.com/yourname/patchwork-deploy.git && pip install -e .
```

---

## Usage

Define your deployment pipeline in a YAML config file:

```yaml
# deploy.yml
pipeline:
  - name: build
    run: ./scripts/build.sh
  - name: test
    run: pytest tests/
  - name: deploy
    run: ./scripts/deploy.sh
    rollback: ./scripts/rollback.sh
```

Run the pipeline:

```bash
patchwork-deploy run deploy.yml
```

Perform a dry run to preview steps without executing them:

```bash
patchwork-deploy run deploy.yml --dry-run
```

Trigger a rollback on a failed stage:

```bash
patchwork-deploy rollback deploy.yml --stage deploy
```

---

## Options

| Flag | Description |
|------|-------------|
| `--dry-run` | Preview pipeline steps without executing |
| `--stage` | Target a specific stage by name |
| `--verbose` | Show detailed output for each step |

---

## License

MIT © 2024 [yourname](https://github.com/yourname)