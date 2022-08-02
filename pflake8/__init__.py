""" pyproject-flake8 (`pflake8`), a monkey patching wrapper to connect flake8 with pyproject.toml configuration """  # noqa

__version__ = '0.0.1a5'

import configparser
import os.path
from pathlib import Path
from typing import Optional

import flake8.main.cli
import flake8.options.config
from flake8.options.config import _stat_key
from flake8.options.config import LOG


try:
    # from Python 3.11 onward
    from tomllib import load as toml_load
except ImportError:
    from tomli import load as toml_load


class ConfigParserTomlMixin:
    @staticmethod
    def get_section_data(fp, is_pyproject):
        toml_config = toml_load(fp.buffer)
        if not is_pyproject:
            return toml_config
        else:
            return toml_config.get('tool', {})

    def copy_section_data(self, section_data):
        for section, config in section_data.items():
            self.add_section(section)
            self._sections[section] = self._dict(config)

    def _read(self, fp, filename):
        path = Path(filename)
        if path.suffix == '.toml':
            is_pyproject = path.name == 'pyproject.toml'
            section_data = self.get_section_data(fp, is_pyproject)
            self.copy_section_data(section_data)
        else:
            super()._read(fp, filename)

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


# Copied from flake8 version 5.0.2.
# Extended candidate list with "pyproject.toml".
def _find_config_file(path: str) -> Optional[str]:
    # on windows if the homedir isn't detected this returns back `~`
    home = os.path.expanduser("~")
    try:
        home_stat = _stat_key(home) if home != "~" else None
    except OSError:  # FileNotFoundError / PermissionError / etc.
        home_stat = None

    dir_stat = _stat_key(path)
    cfg = configparser.RawConfigParser()
    while True:
        for candidate in ("setup.cfg", "tox.ini", ".flake8", "pyproject.toml"):
            cfg_path = os.path.join(path, candidate)
            try:
                cfg.read(cfg_path, encoding="UTF-8")
            except (UnicodeDecodeError, configparser.ParsingError) as e:
                LOG.warning("ignoring unparseable config %s: %s", cfg_path, e)
            else:
                # only consider it a config if it contains flake8 sections
                if "flake8" in cfg or "flake8:local-plugins" in cfg:
                    return cfg_path

        new_path = os.path.dirname(path)
        new_dir_stat = _stat_key(new_path)
        if new_dir_stat == dir_stat or new_dir_stat == home_stat:
            break
        else:
            path = new_path
            dir_stat = new_dir_stat

    # did not find any configuration file
    return None


configparser.RawConfigParser = DivertingRawConfigParser
configparser.ConfigParser = DivertingConfigParser
configparser.SafeConfigParser = DivertingSafeConfigParser
flake8.options.config._find_config_file = _find_config_file

main = flake8.main.cli.main

__all__ = 'main'
