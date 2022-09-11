import sys
from ast import literal_eval
from pathlib import Path
from typing import Any, Dict, List, Tuple, Union

import requests
import tomli


def get_package_info(name: str) -> Dict[str, Any]:
    return requests.get(f"https://pypi.org/pypi/{name}/json").json()


VERSION = "__version__"


def _get_lines(path: Union[Path, str], encoding: str = "utf-8"):
    return Path(path).read_text(encoding).splitlines(keepends=True)


def get_version(
    file_name: Union[Path, str], token: str = VERSION, encoding: str = "utf-8"
) -> str:
    for line in _get_lines(file_name, encoding=encoding):
        if line.startswith(token):
            return literal_eval(line.split("=", 1)[1])
    raise RuntimeError(f"{token} not found")


def patch_version(
    file_name: Union[Path, str],
    new_version: str,
    token: str = VERSION,
    encoding: str = "utf-8",
) -> None:

    patched_string = "".join(
        line
        if not line.startswith(token)
        else f"{token} = '{new_version}'{line[len(line.strip()):]}"
        for line in _get_lines(file_name, encoding=encoding)
    )

    Path(file_name).write_text(patched_string, encoding=encoding)


def find_dependency_version_string(
    pyproject: Union[Path, str], search_string: str
) -> str:
    with Path(pyproject).open('rb') as fp:
        result = tomli.load(fp)

    deps = [dep for dep in result["project"]["dependencies"] if search_string in dep]
    assert len(deps) == 1, "Multiple dependencies matched!"
    return deps[0]


def patch_pyproject_string(
    pyproject: Union[Path, str],
    search_string: str,
    replacement_str: str,
    quotes: Tuple[str, ...] = ('"', "'"),
    encoding: str = "utf-8",
) -> None:
    current = Path(pyproject).read_bytes()
    pairs = [
        (
            f"{quote}{search_string}{quote}".encode(encoding),
            f"{quote}{replacement_str}{quote}".encode(encoding),
        )
        for quote in quotes
    ]
    matches = [(search, replace) for search, replace in pairs if search in current]

    assert (
        len(matches) == 1
    ), f"Either {search_string} is ambiguous or non-existent in {pyproject}."

    search, replace = matches[0]

    split = current.split(search)
    assert (
        len(split) == 2
    ), f"Trying to replace ambiguous {search_string} in {pyproject}."

    patched = split[0] + replace + split[1]

    Path(pyproject).write_bytes(patched)


FLAKE8 = 'flake8'
FLAKE8_MINIMUM_VERSION = '3.8.0'

PFLAKE8 = 'pyproject-flake8'
PFLAKE8_PYPROJECT = "pyproject.toml"
PFLAKE8_INIT = 'pflake8/__init__.py'
PFLAKE8_PYPROJECT = 'pyproject.toml'


def _is_release(version: str) -> bool:
    if 'a' in version or 'rc' in version or 'b' in version:
        return False
    return True


def get_flake8_versions() -> List[str]:
    flake8_releases = get_package_info(FLAKE8)['releases']
    flake8_versions = list(sorted(flake8_releases.keys(), reverse=True))
    # only consider versions newer or equal than minimum version
    flake8_versions = [
        version for version in flake8_versions if version >= FLAKE8_MINIMUM_VERSION
    ]
    # only consider releases
    flake8_versions = [version for version in flake8_versions if _is_release(version)]

    return flake8_versions


def get_pflake8_versions() -> List[str]:
    pflake8_releases = get_package_info(PFLAKE8)['releases']
    pflake8_versions = list(sorted(pflake8_releases.keys(), reverse=True))
    return pflake8_versions


def command_check():
    flake8_versions, pflake8_versions = get_flake8_versions(), get_pflake8_versions()
    print(f"Available  flake8 versions: {flake8_versions}")
    print(f"Available pflake8 versions: {pflake8_versions}")

    missing_versions = list(
        sorted(set(flake8_versions) - set(pflake8_versions), reverse=True)
    )

    print(f"The following versions do not have a correspondence: {missing_versions}")

    if missing_versions:
        print("There are missing versions!")
        return 1
    else:
        print("All well.")
        return 0


def str2bool(value: Union[bool, str]) -> bool:
    if isinstance(value, bool):
        return value
    if value.lower() in ('y', 't', 'yes', 'true'):
        return True
    return False


def command_bump(target_version, alpha=False, post=None):
    alpha = str2bool(alpha)
    suffix = "" if post is None else f".post{int(post)}"
    target_version_pflake8 = (
        target_version if not alpha else f"{target_version}a1"
    ) + suffix

    flake8_versions, pflake8_versions = get_flake8_versions(), get_pflake8_versions()

    if target_version not in flake8_versions:
        raise RuntimeError("Specified version does not exist for flake8!")

    if target_version_pflake8 in pflake8_versions:
        raise RuntimeError("Specified version already exists for pflake8!")

    local_pflake8_version = get_version(PFLAKE8_INIT)

    if local_pflake8_version == target_version_pflake8:
        raise RuntimeError("Already at specified version.")

    print(f"Current pflake8 version: {local_pflake8_version}")

    print(
        f"Bumping to {target_version_pflake8}. "
        f"This will be a {'alpha' if alpha else 'normal'} release."
    )

    patch_version(PFLAKE8_INIT, target_version_pflake8)
    replacement_string = find_dependency_version_string(PFLAKE8_PYPROJECT, FLAKE8)

    new_version_specification = (
        f"{FLAKE8} >= {target_version}" if alpha else f"{FLAKE8} == {target_version}"
    )
    patch_pyproject_string(
        PFLAKE8_PYPROJECT, replacement_string, new_version_specification
    )

    todo = [
        f'git add {PFLAKE8_INIT} {PFLAKE8_PYPROJECT}',
        f'git commit -m "Version {target_version_pflake8}"',
        f'git tag v{target_version_pflake8}',
    ]

    print("Done. You should now run:")

    for cmd in todo:
        print(cmd)


commands = dict(
    check=command_check,
    bump=command_bump,
)


def main(args: List[str] = sys.argv[1:]):
    if not args:
        print(f"Supported commands are {tuple(commands.keys())!r}")
        return 1

    return commands[args[0]](*args[1:])


if __name__ == '__main__':
    sys.exit(main())
