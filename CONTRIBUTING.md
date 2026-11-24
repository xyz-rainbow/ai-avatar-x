**English** | [Español](CONTRIBUTING.es.md)

# Contributing to ai-avatar-x

Thanks for taking the time to contribute. Interactive desktop AI avatar (Python, Flask, pywebview) with local Ollama, trilingual EN/ES/ZH UI.

## License and contributions

By opening an issue or sending a pull request you accept the contribution clause in [LICENSE](LICENSE): you assign to Rainbow Technology all rights in your contribution, or, if that assignment is not effective, you grant a perpetual, irrevocable, exclusive license, and you warrant that you have the right to contribute it.

Please do not open a public issue for a security vulnerability; use the repository Security advisory form if it is available.

## Development setup

Follow the **Quick Start** in [README.md](README.md):

```bash
git clone https://github.com/xyz-rainbow/ai-avatar-x.git
cd ai-avatar-x
bash install.sh                 # Linux/macOS
# or: python interactive_install.py
```

`package.json` scripts include `start` and `dev`. CI is defined in `.github/workflows/ci.yml`.

## Pull requests

1. Create a topic branch from the default branch (`main`).
2. Keep the change focused.
3. Update [CHANGELOG.md](CHANGELOG.md) and add a line to `docs/logs/YYYY-MM.md` when the change is user-visible or touches process or docs.
4. Never commit secrets, API keys, or private data.
5. Wait for CI to go green when the repository has workflows. Maintainers squash-merge into the default branch.
