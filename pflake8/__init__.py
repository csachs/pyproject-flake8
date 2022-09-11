""" pyproject-flake8 (`pflake8`), a monkey patching wrapper to connect flake8 with pyproject.toml configuration """  # noqa

__version__ = '5.0.4a1'

import ast
import configparser
import sys
from types import ModuleType
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

            for section, config in section_to_copy.items():
                self.add_section(section)
                self._sections[section] = self._dict(config)
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


configparser.RawConfigParser = DivertingRawConfigParser
configparser.ConfigParser = DivertingConfigParser
configparser.SafeConfigParser = DivertingSafeConfigParser


class FixFilenames(ast.NodeTransformer):
    tuple_of_interest = ("setup.cfg", "tox.ini", ".flake8")
    fix_applied = False

    def visit_Tuple(self, node: ast.Tuple) -> ast.Tuple:
        if all(isinstance(el, ast.Constant) for el in node.elts) and set(
            self.tuple_of_interest
        ) == {el.value for el in node.elts}:
            node.elts.append(ast.Constant(value="pyproject.toml"))
            ast.fix_missing_locations(node)
            self.fix_applied = True
        return node

    @classmethod
    def apply(cls, module: ModuleType = flake8.options.config) -> None:
        filename = module.__file__

        original_ast = ast.parse(
            Path(filename).read_text(encoding='UTF-8'), filename=filename
        )

        transformer = cls()
        fixed_ast = transformer.visit(original_ast)

        if not transformer.fix_applied:
            print(
                "[pflake8] Warning: Failed applying patch for pyproject.toml parsing.",
                file=sys.stderr,
            )

        compiled = compile(fixed_ast, filename=filename, mode="exec")
        exec(compiled, module.__dict__)


FixFilenames.apply()


main = flake8.main.cli.main

__all__ = 'main'
