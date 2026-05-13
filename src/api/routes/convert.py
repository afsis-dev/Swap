# Histórico de Alterações:
#   Data       | Desenvolvedor  | Ticket | Observação
#   -----------|----------------|--------|-------------------
#   2026-05-13 | AFSIS Dev      | #001   | Implementação v1.1.0


import ipaddress
import json
import re
import socket
import uuid
import asyncio
import tempfile
from pathlib import Path
from urllib.parse import unquote, urlparse

import httpx
from fastapi import APIRouter, UploadFile, File, Form, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse

from src.api.models import ConvertResponse, ConvertUrlRequest, JobStatus
from src.api.websocket import ws_manager
from src.services.conversion_service import ConversionService, BatchProgress
from src.services.history_service import add_conversion
from src.utils.config import get_setting
from src.utils.logger import get_logger

logger = get_logger(__name__)

_MAX_URL_DOWNLOAD_BYTES = 100 * 1024 * 1024  # 100 MB

_PRIVATE_NETWORKS = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("224.0.0.0/4"),
    ipaddress.ip_network("240.0.0.0/4"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("::/128"),
]

_BLOCKED_HOSTS = {"localhost", "127.0.0.1", "0.0.0.0", "[::1]", "::1"}

_ALLOWED_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif", ".tiff", ".tif", ".ico", ".ppm",
    ".svg",
    ".pdf",
    ".docx", ".odt", ".txt", ".rtf", ".html", ".htm",
    ".xlsx", ".csv", ".ods",
    ".epub", ".mobi", ".azw3", ".fb2", ".lrf", ".rb", ".tcr", ".snb", ".pdb",
    ".ppt", ".pptx", ".pps", ".ppsx", ".pptm", ".pot", ".potx", ".potm", ".ppsm",
    ".cbz", ".zip", ".cbr", ".rar", ".cb7", ".7z",
}


def _validate_download_url(url: str) -> str:
    try:
        parsed = urlparse(url)
    except Exception:
        raise HTTPException(status_code=400, detail="URL mal formatada")

    if parsed.scheme not in ("http", "https"):
        raise HTTPException(status_code=400, detail="Apenas URLs HTTP/HTTPS são permitidas")

    hostname = parsed.hostname
    if not hostname:
        raise HTTPException(status_code=400, detail="URL sem hostname válido")

    hostname_lower = hostname.lower()

    if hostname_lower in _BLOCKED_HOSTS:
        raise HTTPException(status_code=400, detail="URLs para endereços locais não são permitidas")

    if re.search(r"\.local$", hostname_lower):
        raise HTTPException(status_code=400, detail="Domínios .local não são permitidos")

    try:
        resolved = socket.getaddrinfo(hostname_lower, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
    except socket.gaierror:
        raise HTTPException(status_code=400, detail="Não foi possível resolver o hostname da URL")

    for _, _, _, _, sockaddr in resolved:
        ip_str = sockaddr[0]
        try:
            ip = ipaddress.ip_address(ip_str)
        except ValueError:
            continue

        if ip.is_loopback or ip.is_private or ip.is_multicast or ip.is_reserved or ip.is_unspecified or ip.is_link_local:
            raise HTTPException(status_code=400, detail=f"IP interno/bloqueado detectado: {ip_str}")

        for net in _PRIVATE_NETWORKS:
            if ip in net:
                raise HTTPException(status_code=400, detail=f"Rede privada/bloqueada detectada: {ip_str}")

    if parsed.path:
        if ".." in parsed.path or "%00" in parsed.path or "\x00" in parsed.path:
            raise HTTPException(status_code=400, detail="Caminho da URL contém sequências suspeitas")

        path_obj = Path(unquote(parsed.path))
        stem = path_obj.name
        ext = path_obj.suffix.lower()

        if stem and ext and ext not in _ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Extensão '{ext}' não suportada. Formatos aceitos: {', '.join(sorted(_ALLOWED_EXTENSIONS))}",
            )

    return hostname_lower

router = APIRouter(prefix="/api", tags=["conversion"])

_jobs: dict[str, dict] = {}


def _convert_one(
    job_id: str,
    file_path: Path,
    target_format: str,
    output_dir: Path,
    loop: asyncio.AbstractEventLoop,
    file_index: int,
    total_files: int,
):
    service = ConversionService(max_workers=1)
    try:
        result = service.convert_single(file_path, output_dir, target_format)
    except Exception as e:
        result = None
        logger.error(f"Conversion failed for {file_path.name}: {e}")

    output_size = 0
    if result and result.success and result.output_path and result.output_path.exists():
        output_size = result.output_path.stat().st_size

    entry = {
        "file": file_path.name,
        "success": result.success if result else False,
        "output": result.output_path.name if result and result.success and result.output_path else "",
        "output_size": output_size,
        "error": result.error if result and not result.success else ("Conversion failed" if not result else None),
    }

    pct = (file_index + 1) / total_files

    ws_manager.send_progress_sync(job_id, {
        "type": "result",
        **entry,
    }, loop)

    ws_manager.send_progress_sync(job_id, {
        "type": "progress",
        "file": file_path.name,
        "current": file_index + 1,
        "total": total_files,
        "percent": pct,
    }, loop)

    if result and result.success:
        try:
            add_conversion({
                "input_file": str(result.input_path),
                "output_file": str(result.output_path),
                "format": target_format,
                "status": "success",
                "duration_ms": result.duration_ms,
            })
        except Exception as e:
            logger.error(f"Failed to save history: {e}")

    return entry


def _run_conversion_sync(
    job_id: str,
    file_paths: list[Path],
    format_map: dict[str, str],
    options: dict,
    temp_dir: Path,
    loop: asyncio.AbstractEventLoop,
):
    _jobs[job_id]["status"] = "running"

    output_dir = temp_dir / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    total = len(file_paths)
    result_list = []
    success_count = 0

    try:
        for i, file_path in enumerate(file_paths):
            target_format = format_map.get(file_path.name, format_map.get("*", ".webp"))
            entry = _convert_one(job_id, file_path, target_format, output_dir, loop, i, total)
            result_list.append(entry)
            if entry["success"]:
                success_count += 1

        error_count = total - success_count

        _jobs[job_id]["status"] = "done"
        _jobs[job_id]["results"] = result_list
        _jobs[job_id]["progress"] = 1.0

        ws_manager.send_progress_sync(job_id, {
            "type": "done",
            "success_count": success_count,
            "error_count": error_count,
            "results": result_list,
        }, loop)

    except Exception as e:
        logger.error(f"Conversion job {job_id} failed: {e}")
        _jobs[job_id]["status"] = "failed"
        _jobs[job_id]["error"] = str(e)

        ws_manager.send_progress_sync(job_id, {
            "type": "error",
            "message": str(e),
        }, loop)


@router.post("/convert", response_model=ConvertResponse)
async def convert_files(
    files: list[UploadFile] = File(...),
    format_map: str = Form("{}"),
    options: str = Form("{}"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
):
    job_id = str(uuid.uuid4())
    temp_dir = Path(f"/tmp/swap/{job_id}")
    temp_dir.mkdir(parents=True, exist_ok=True)

    saved_paths = []
    for f in files:
        if not f.filename:
            continue
        path = temp_dir / f.filename
        content = await f.read()
        with open(path, "wb") as buf:
            buf.write(content)
        saved_paths.append(path)

    if not saved_paths:
        raise HTTPException(status_code=400, detail="No valid files uploaded")

    _jobs[job_id] = {
        "job_id": job_id,
        "status": "pending",
        "progress": 0.0,
        "current_file": None,
        "results": [],
        "temp_dir": str(temp_dir),
    }

    fmt_map = json.loads(format_map)
    parsed_options = json.loads(options)

    ws_manager.ensure_queue(job_id)

    loop = asyncio.get_running_loop()

    background_tasks.add_task(
        _run_conversion_sync,
        job_id=job_id,
        file_paths=saved_paths,
        format_map=fmt_map,
        options=parsed_options,
        temp_dir=temp_dir,
        loop=loop,
    )

    return ConvertResponse(job_id=job_id, status="pending", total_files=len(saved_paths))


@router.get("/convert/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str):
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return JobStatus(
        job_id=job["job_id"],
        status=job["status"],
        progress=job.get("progress", 0.0),
        current_file=job.get("current_file"),
        results=job.get("results", []),
    )


@router.delete("/convert/{job_id}")
async def cancel_job(job_id: str):
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job["status"] in ("done", "failed"):
        return {"message": "Job already finished"}

    job["status"] = "cancelled"
    return {"message": "Job cancelled"}


@router.post("/convert/url", response_model=ConvertResponse)
async def convert_from_url(
    body: ConvertUrlRequest,
    background_tasks: BackgroundTasks = BackgroundTasks(),
):
    _validate_download_url(body.url)

    job_id = str(uuid.uuid4())
    temp_dir = Path(f"/tmp/swap/{job_id}")
    temp_dir.mkdir(parents=True, exist_ok=True)

    parsed = urlparse(body.url)
    filename = None
    if parsed.path:
        filename = unquote(Path(parsed.path).name) or "download"

    if not filename or "." not in filename:
        filename = "download.bin"

    file_path = temp_dir / filename

    try:
        async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
            async with client.stream("GET", body.url) as response:
                response.raise_for_status()

                content_length = response.headers.get("content-length")
                if content_length:
                    cl = int(content_length)
                    if cl > _MAX_URL_DOWNLOAD_BYTES:
                        raise HTTPException(
                            status_code=400,
                            detail=f"Arquivo excede o limite de {_MAX_URL_DOWNLOAD_BYTES // (1024*1024)} MB",
                        )

                downloaded = 0
                with open(file_path, "wb") as f:
                    async for chunk in response.aiter_bytes(chunk_size=8192):
                        downloaded += len(chunk)
                        if downloaded > _MAX_URL_DOWNLOAD_BYTES:
                            raise HTTPException(
                                status_code=400,
                                detail=f"Arquivo excede o limite de {_MAX_URL_DOWNLOAD_BYTES // (1024*1024)} MB",
                            )
                        f.write(chunk)

                if downloaded == 0:
                    raise HTTPException(status_code=400, detail="Arquivo baixado está vazio")

    except httpx.HTTPError as e:
        raise HTTPException(status_code=400, detail=f"Falha ao baixar URL: {e}")
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(status_code=400, detail=f"Erro ao baixar URL: {e}")

    fmt = body.target_format
    if not fmt.startswith("."):
        fmt = f".{fmt}"

    _jobs[job_id] = {
        "job_id": job_id,
        "status": "pending",
        "progress": 0.0,
        "current_file": None,
        "results": [],
        "temp_dir": str(temp_dir),
    }

    ws_manager.ensure_queue(job_id)
    loop = asyncio.get_running_loop()

    background_tasks.add_task(
        _run_conversion_sync,
        job_id=job_id,
        file_paths=[file_path],
        format_map={filename: fmt},
        options=body.options,
        temp_dir=temp_dir,
        loop=loop,
    )

    return ConvertResponse(job_id=job_id, status="pending", total_files=1)


@router.get("/download/{job_id}/{filename}")
async def download_file(job_id: str, filename: str):
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    temp_dir = Path(job.get("temp_dir", f"/tmp/swap/{job_id}"))
    file_path = temp_dir / "output" / filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type="application/octet-stream",
    )