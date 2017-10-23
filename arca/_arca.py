from __future__ import unicode_literals, print_function

from pathlib import Path
from typing import Union, Optional, Dict, Any

import os

from .backend import BaseBackend, VenvBackend
from .result import Result
from .task import Task
from .utils import load_class, Settings

BackendDefinitionType = Union[type, BaseBackend, str]


class Arca:

    def __init__(self, backend: BackendDefinitionType=VenvBackend, settings=None):
        self.settings: Settings = self._get_settings(settings)

        self.backend: BaseBackend = self._get_backend_instance(backend)
        self.backend.inject_arca(self)

    def _get_backend_instance(self, backend: BackendDefinitionType) -> BaseBackend:
        if isinstance(backend, str):
            backend = load_class(backend)

        if isinstance(backend, type):
            backend = backend()

        if not issubclass(backend.__class__, VenvBackend):
            raise ValueError(f"{backend.__class__} is not an subclass of BaseBackend")

        return backend

    def _get_settings(self, settings: Optional[Dict[str, Any]]) -> Settings:
        if settings is not None:
            settings = Settings(settings)
        else:
            settings = Settings()

        for key, val in os.environ.items():
            settings[key] = val

        return settings

    def run(self, repo: str, branch: str, task: Task) -> Result:
        return self.backend.run(repo, branch, task)

    def static_filename(self, repo: str, branch: str, relative_path: Union[str, Path]) -> Path:
        if not isinstance(relative_path, Path):
            relative_path = Path(relative_path)
        return self.backend.static_filename(repo, branch, relative_path)
