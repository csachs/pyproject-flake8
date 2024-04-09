import sys
import unittest
import pflake8


class TestAppendConfig(unittest.TestCase):
    def test_append_config_toml(self):
        sys.argv = [
            "pflake8",
            "--config",
            "./test/data/setup.cfg",
            "--append-config",
            "./test/data/pyproject.toml",
            "./test/data/dummy.py",
        ]

        pflake8.main()  # OK if this raises no exception.

    def test_append_config_normal(self):
        sys.argv = [
            "pflake8",
            "--config",
            "./test/data/setup.cfg",
            "--append-config",
            "./test/data/setup_custom.cfg",
            "./test/data/dummy.py",
        ]

        pflake8.main()  # OK if this raises no exception.


if __name__ == '__main__':
    unittest.main()
