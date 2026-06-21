"""System endpoint schemas."""

from __future__ import annotations

from pydantic import BaseModel


class SystemProcess(BaseModel):
    pid: int
    name: str
    cpu: float
    memory: float
    status: str


class SystemMetricsResponse(BaseModel):
    cpu_percent: float
    ram_total_gb: float
    ram_used_gb: float
    ram_percent: float
    gpu_name: str
    gpu_type: str
    gpu_percent: float | None
    disk_total_gb: float
    disk_used_gb: float
    disk_percent: float
    processes: list[SystemProcess]


class SystemLogsResponse(BaseModel):
    logs: list[dict]
    total: int
