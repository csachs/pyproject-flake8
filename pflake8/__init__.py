""" pyproject-flake8 (`pflake8`), a monkey patching wrapper to connect flake8 with pyproject.toml configuration """  # noqa

__version__ = '3.8.4'

import configparser
from pathlib import Path

import flake8.main.cli
import flake8.options.config

try:
    # from Python 3.11 onward
    from tomllib import load as toml_load
except ImportError:
    from tomli import load as toml_load


class ConfigParserTomlMixin:
    def _read(self, fp, filename):
        filename_path = Path(filename)
        if filename_path.suffix == '.toml':
            is_pyproject = filename_path.name == 'pyproject.toml'

            toml_config = toml_load(fp.buffer)

            section_to_copy = (
                toml_config if not is_pyproject else toml_config.get('tool', {})
            )

            for key, value in section_to_copy.items():
                self._sections[key] = self._dict(value)
        else:
            super(ConfigParserTomlMixin, self)._read(fp, filename)

    def _convert_to_boolean(self, value):
        if isinstance(value, bool):
            return value
        else:
            return super()._convert_to_boolean(value)


class DivertingRawConfigParser(ConfigParserTomlMixin, configparser.RawConfigParser):
    pass


class DivertingConfigParser(ConfigParserTomlMixin, configparser.ConfigParser):
    pass


class DivertingSafeConfigParser(ConfigParserTomlMixin, configparser.SafeConfigParser):
    pass


class ModifiedConfigFileFinder(flake8.options.config.ConfigFileFinder):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.project_filenames = self.project_filenames + ('pyproject.toml',)


configparser.RawConfigParser = DivertingRawConfigParser
configparser.ConfigParser = DivertingConfigParser
configparser.SafeConfigParser = DivertingSafeConfigParser
flake8.options.config.ConfigFileFinder = ModifiedConfigFileFinder

main = flake8.main.cli.main

__all__ = 'main'
