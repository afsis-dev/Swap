# Histórico de Alterações:
#   Data       | Desenvolvedor  | Ticket | Observação
#   -----------|----------------|--------|-------------------
#   2026-05-13 | AFSIS Dev      | #001   | Implementação v1.1.0


from fastapi import APIRouter, HTTPException
from src.api.models import FormatsResponse, FormatInfo
from src.services.format_registry import (
    get_supported_input_formats,
    get_output_formats_for,
    _converter_for_extension,
)

router = APIRouter(prefix="/api", tags=["formats"])


@router.get("/formats", response_model=FormatsResponse)
async def get_formats():
    formats = {}
    for ext in get_supported_input_formats():
        try:
            outputs = get_output_formats_for(ext)
            converter = _converter_for_extension(ext)
            schema = converter.get_options_schema() if converter else {}
            formats[ext] = FormatInfo(outputs=outputs, options=schema)
        except Exception:
            formats[ext] = FormatInfo(outputs=[], options={})

    return FormatsResponse(formats=formats)


@router.get("/formats/{extension}")
async def get_format(extension: str):
    ext = extension.lower() if extension.startswith(".") else f".{extension.lower()}"

    outputs = get_output_formats_for(ext)
    if not outputs:
        raise HTTPException(status_code=404, detail=f"Format {ext} not supported")

    converter = _converter_for_extension(ext)
    schema = converter.get_options_schema() if converter else {}

    return FormatInfo(outputs=outputs, options=schema)
