""" pyproject-flake8 (`pflake8`), a monkey patching wrapper to connect flake8 with pyproject.toml configuration """  # noqa

__version__ = '0.0.1a2'

import configparser
from pathlib import Path

import flake8.main.cli
import flake8.options.config
import toml


class ConfigParserTomlMixin:
    def _read(self, fp, filename):
        filename_path = Path(filename)
        if filename_path.suffix == '.toml':
            is_pyproject = filename_path.name == 'pyproject.toml'

            toml_config = toml.load(fp)

            section_to_copy = toml_config if not is_pyproject else toml_config['tool']

            for key, value in section_to_copy.items():
                self._sections[key] = self._dict(value)
        else:
            super(ConfigParserTomlMixin, self)._read(fp, filename)


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
