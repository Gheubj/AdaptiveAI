from __future__ import annotations

import logging
import os
import tomllib
from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, field_validator


@dataclass(frozen=True)
class Settings:
    root: Path = Path(os.getenv("ADAPTIVEAI_ROOT", ".")).resolve()
    random_seed: int = int(os.getenv("ADAPTIVEAI_SEED", "3407"))
    log_level: str = os.getenv("ADAPTIVEAI_LOG_LEVEL", "INFO")

    @property
    def raw_dir(self) -> Path:
        return self.root / "data" / "raw"

    @property
    def processed_dir(self) -> Path:
        return self.root / "data" / "processed"


def configure_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)


class ProductConfig(BaseModel):
    """Validated local-first runtime configuration. Unknown keys are rejected."""

    model_config = ConfigDict(extra="forbid")

    registry_path: Path = Path("data/local_model_registry.json")
    backend_path: Path = Path("vendor/llama.cpp/build/bin/llama-server")
    default_routing_mode: str = "balanced"
    local_only: bool = True
    host: str = "127.0.0.1"
    port: int = Field(8088, ge=1, le=65535)
    request_timeout_seconds: float = Field(120.0, gt=0, le=3600)
    max_request_bytes: int = Field(1_048_576, ge=1024, le=16_777_216)
    max_concurrency: int = Field(1, ge=1, le=32)
    keep_alive_seconds: float = Field(300.0, ge=0, le=86_400)
    switch_hysteresis_seconds: float = Field(0.5, ge=0, le=60)
    balanced_latency_weight: float = Field(0.15, ge=0, le=10)
    max_latency_seconds: float | None = Field(None, gt=0)
    available_memory_bytes: int | None = Field(None, gt=0)
    log_level: str = "INFO"
    research_logging: bool = False

    @field_validator("default_routing_mode")
    @classmethod
    def validate_mode(cls, value: str) -> str:
        allowed = {"fastest", "quality", "balanced", "hardware-aware"}
        if value not in allowed:
            raise ValueError(f"must be one of {sorted(allowed)}")
        return value

    @field_validator("host")
    @classmethod
    def validate_host(cls, value: str) -> str:
        if value not in {"127.0.0.1", "localhost", "::1"}:
            raise ValueError(
                "remote binding is disabled in the experimental server; use a secured proxy"
            )
        return value


def load_product_config(path: Path | None = None) -> ProductConfig:
    config_path = path or Path(os.getenv("ADAPTIVEAI_CONFIG", "adaptiveai.toml"))
    if not config_path.exists():
        return ProductConfig()
    payload = tomllib.loads(config_path.read_text())
    return ProductConfig.model_validate(payload.get("adaptiveai", payload))
