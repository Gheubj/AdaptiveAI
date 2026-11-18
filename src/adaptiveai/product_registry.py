from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from adaptiveai.local_backend import LocalModel, load_registry


@dataclass(frozen=True)
class RegistryStatus:
    model: LocalModel
    available: bool
    hash_valid: bool | None
    message: str


class ModelRegistry:
    def __init__(self, path: Path):
        self.path = path
        if not path.exists():
            raise FileNotFoundError(f"Model registry not found: {path}")
        models = load_registry(path)
        identifiers = [model.model_id for model in models]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("Model registry contains duplicate model_id values")
        self._models = {model.model_id: model for model in models}

    def models(self) -> tuple[LocalModel, ...]:
        return tuple(self._models.values())

    def get(self, model_id: str) -> LocalModel:
        try:
            return self._models[model_id]
        except KeyError as error:
            raise ValueError(f"Unknown model: {model_id}") from error

    def inspect(self, *, verify_hash: bool = False) -> tuple[RegistryStatus, ...]:
        statuses = []
        for model in self.models():
            available = model.path.is_file()
            valid = None
            message = "available" if available else f"missing weight: {model.path}"
            if available and verify_hash and model.file_sha256:
                digest = hashlib.sha256(model.path.read_bytes()).hexdigest()
                valid = digest == model.file_sha256
                message = "available; hash valid" if valid else "hash mismatch"
            statuses.append(RegistryStatus(model, available, valid, message))
        return tuple(statuses)
