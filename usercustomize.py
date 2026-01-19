"""
User-level customizations to silence known noisy dependency warnings.
This module installs an import hook that suppresses langsmith's
Python 3.14 warning when its schemas module is imported.
"""

import importlib.abc
import importlib.machinery
import warnings
import sys


class _LangsmithSchemasFilter(importlib.abc.MetaPathFinder, importlib.abc.Loader):
    """Intercept langsmith.schemas import to mute its Python 3.14 warning."""

    target = "langsmith.schemas"

    def __init__(self):
        self._orig_loader = None

    def find_spec(self, fullname, path, target=None):
        if fullname != self.target:
            return None
        spec = importlib.machinery.PathFinder.find_spec(fullname, path)
        if not spec:
            return None
        self._orig_loader = spec.loader
        spec.loader = self
        return spec

    def create_module(self, spec):
        return None  # default module creation

    def exec_module(self, module):
        if not self._orig_loader:
            return
        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore",
                message="Core Pydantic V1 functionality isn't compatible with Python 3.14 or greater.",
                category=UserWarning,
            )
            self._orig_loader.exec_module(module)


sys.meta_path.insert(0, _LangsmithSchemasFilter())
