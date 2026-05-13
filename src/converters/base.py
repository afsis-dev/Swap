# Histórico de Alterações:
#   Data       | Desenvolvedor  | Ticket | Observação
#   -----------|----------------|--------|-------------------
#   2026-05-13 | AFSIS Dev      | #001   | Implementação v1.1.0


from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional


class ConversionError(Exception):
    pass


class UnsupportedFormatError(ConversionError):
    pass


@dataclass
class ConversionResult:
    success: bool
    input_path: Path
    output_path: Optional[Path] = None
    duration_ms: float = 0.0
    error: Optional[str] = None
    input_size: int = 0
    output_size: int = 0


@dataclass
class FormatInfo:
    extension: str
    description: str
    category: str


class BaseConverter(ABC):

    def __init__(self, options: Optional[dict] = None):
        self.options = options or {}

    @abstractmethod
    def convert(
        self,
        input_path: Path,
        output_path: Path,
        progress_callback: Optional[Callable[[float], None]] = None,
    ) -> None:
        ...

    @abstractmethod
    def supported_input_formats(self) -> list[str]:
        ...

    @abstractmethod
    def supported_output_formats(self) -> list[str]:
        ...

    @abstractmethod
    def category(self) -> str:
        ...

    def can_convert(self, input_ext: str, output_ext: str) -> bool:
        return input_ext.lower() in self.supported_input_formats() and output_ext.lower() in self.supported_output_formats()

    def get_options_schema(self) -> dict:
        return {}
