# Contributing

Thanks for your interest in contributing to **TW Lottery Recommendation**! This guide covers how to set up the project, run the tests, and submit changes.

## Development setup

This project uses [uv](https://docs.astral.sh/uv/) for dependency and environment management, and requires **Python 3.14+**.

```bash
# 1. Clone your fork
git clone https://github.com/<your-username>/tw-lottery-recommendation.git
cd tw-lottery-recommendation

# 2. Install dependencies (creates a .venv automatically)
uv sync

# 3. Verify the CLI works
uv run lottery --help
```

## Running tests

All changes should keep the test suite green:

```bash
uv run pytest          # run everything
uv run pytest -v       # verbose
uv run pytest tests/test_analyzer.py   # a single file
```

The same suite runs in CI on every push and pull request (`.github/workflows/test.yml`).

## Making changes

1. Create a branch off `main`: `git checkout -b my-change`
2. Make your change and **add or update tests** for it.
3. Run `uv run pytest` and make sure it passes.
4. Commit with a clear, descriptive message.
5. Push and open a pull request against `main`.

### Pull request guidelines

- Keep PRs focused — one logical change per PR is easier to review.
- Describe **what** the change does and **why**.
- Make sure CI is green before requesting review.
- Update the `README.md` if you change user-facing behavior or commands.

## Reporting bugs / requesting features

Please open a [GitHub issue](https://github.com/zients/tw-lottery-recommendation/issues) and include, where relevant:

- What you expected to happen vs. what actually happened
- Steps to reproduce (the exact `lottery ...` command helps)
- Your OS and Python version (`python --version`)

## Scope & disclaimer

This is an educational/research project. Lottery draws are random and the model does **not** predict winning numbers — please keep that in mind when proposing features. See the disclaimer in the [README](README.md) for details.

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE) that covers this project.
