from __future__ import annotations

import json
import os
import platform
import shutil
from dataclasses import asdict, dataclass
from pathlib import Path

import psutil


@dataclass(frozen=True)
class HardwareProfile:
    cpu_model: str
    physical_cores: int | None
    logical_cores: int | None
    total_ram_bytes: int
    available_ram_bytes: int
    operating_system: str
    architecture: str
    gpu_devices: tuple[dict[str, object], ...]
    disk_free_bytes: int
    inference_backends: tuple[str, ...]
    energy_measurement: str | None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _cpu_model() -> str:
    path = Path("/proc/cpuinfo")
    if path.exists():
        for line in path.read_text(errors="replace").splitlines():
            if line.lower().startswith("model name"):
                return line.split(":", 1)[1].strip()
    return platform.processor() or "unknown"


def _gpu_devices() -> tuple[dict[str, object], ...]:
    devices = []
    drm = Path("/sys/class/drm")
    cards = [path for path in drm.glob("card*") if path.name.removeprefix("card").isdigit()]
    for card in sorted(cards) if drm.exists() else []:
        vendor_path = card / "device/vendor"
        device_path = card / "device/device"
        devices.append(
            {
                "name": card.name,
                "vendor_id": vendor_path.read_text().strip() if vendor_path.exists() else None,
                "device_id": device_path.read_text().strip() if device_path.exists() else None,
                "memory_bytes": None,
            }
        )
    return tuple(devices)


def discover_hardware(workspace: Path = Path(".")) -> HardwareProfile:
    memory = psutil.virtual_memory()
    backends = []
    candidates = {
        "ollama": shutil.which("ollama"),
        "llama.cpp": shutil.which("llama-cli") or str(Path("vendor/llama.cpp/build/bin/llama-cli"))
        if Path("vendor/llama.cpp/build/bin/llama-cli").exists()
        else None,
    }
    backends.extend(name for name, path in candidates.items() if path)
    powercap = Path("/sys/class/powercap")
    rapl = any(
        path.is_file() and os.access(path, os.R_OK) for path in powercap.glob("**/energy_uj")
    )
    return HardwareProfile(
        cpu_model=_cpu_model(),
        physical_cores=psutil.cpu_count(logical=False),
        logical_cores=psutil.cpu_count(logical=True),
        total_ram_bytes=memory.total,
        available_ram_bytes=memory.available,
        operating_system=f"{platform.system()} {platform.release()}",
        architecture=platform.machine(),
        gpu_devices=_gpu_devices(),
        disk_free_bytes=shutil.disk_usage(workspace).free,
        inference_backends=tuple(backends),
        energy_measurement="RAPL" if rapl else None,
    )


def save_hardware_profile(path: Path, workspace: Path = Path(".")) -> HardwareProfile:
    profile = discover_hardware(workspace)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(profile.to_dict(), indent=2))
    return profile
