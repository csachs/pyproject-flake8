# pyproject-flake8 (`pflake8`)

A monkey patching wrapper to connect flake8 with `pyproject.toml` configuration.

## Rationale

[`flake8`](https://flake8.pycqa.org/) is one of the most popular Python linters, `pyproject.toml` has become the [standard](https://www.python.org/dev/peps/pep-0518/) for Python project metadata.

More and more tools are able to utilize a shared `pyproject.toml`, alleviating the need for many individual configuration files cluttering a project repository.

Since excellent `flake8` is not aimed to support `pyproject.toml`, this wrapper script tries to fix the situation.

## Installation

### From github 

```bash
pip install .
```

### From PyPI

```bash
pip install pyproject-flake8
```

### Building packages

Use your favorite [PEP517](https://www.python.org/dev/peps/pep-0517/) compliant builder, e.g.:
```bash
# install first via: pip install build
python -m build
# packges will reside in dist/
```

## Usage

Call `pflake8` instead of `flake8`.

Configuration goes into the `tool.flake8` section of `pyproject.toml`: 

```toml
[tool.flake8]
max-line-length = 88
extend-ignore = "E203,"
max-complexity = 10
```

## See also

Two other projects aim to address the same problem:

- [flake9](https://gitlab.com/retnikt/flake9)
- [FlakeHell](https://github.com/life4/flakehell)

Both seem to try to do a lot more than just getting `pyproject.toml` support. `pyproject-flake8` tries to stay minimal while solving its task (with currently around 40 lines). 

## Caveat

This script monkey-patches flake8 and the configparser library of Python, therefore loading it as a module may have unforeseen consequences.
Alpha quality. Use at your own risk. It will likely break if either Python or flake8 restructure their code significantly. No guarantees for stability between versions.

## License

Unlicense