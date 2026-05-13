# Histórico de Alterações:
#   Data       | Desenvolvedor  | Ticket | Observação
#   -----------|----------------|--------|-------------------
#   2026-05-13 | AFSIS Dev      | #001   | Implementação v1.1.0


from pydantic import BaseModel, Field, HttpUrl
from typing import Optional


class ConvertResponse(BaseModel):
    job_id: str
    status: str
    total_files: int


class ConvertUrlRequest(BaseModel):
    url: str
    target_format: str
    options: dict = Field(default_factory=dict)


class JobStatus(BaseModel):
    job_id: str
    status: str
    progress: float = 0.0
    current_file: Optional[str] = None
    results: list[dict] = Field(default_factory=list)


class HistoryEntry(BaseModel):
    id: str
    input_file: str
    output_file: str
    format: str
    status: str
    duration_ms: float
    timestamp: str


class HistoryList(BaseModel):
    entries: list[HistoryEntry]
    total: int
    limit: int
    offset: int


class Settings(BaseModel):
    output_dir: str
    max_workers: int = 4
    default_format: str = ""
    theme: str = "light"
    cleanup_after_download: bool = True


class FormatInfo(BaseModel):
    outputs: list[str]
    options: dict = Field(default_factory=dict)


class FormatsResponse(BaseModel):
    formats: dict[str, FormatInfo]
