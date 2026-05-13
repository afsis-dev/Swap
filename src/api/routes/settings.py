# Histórico de Alterações:
#   Data       | Desenvolvedor  | Ticket | Observação
#   -----------|----------------|--------|-------------------
#   2026-05-13 | AFSIS Dev      | #001   | Implementação v1.1.0


from fastapi import APIRouter
from src.api.models import Settings
from src.utils.config import load_config, save_config

router = APIRouter(prefix="/api", tags=["settings"])


@router.get("/settings", response_model=Settings)
async def get_settings():
    config = load_config()
    return Settings(
        output_dir=config.get("output_dir", ""),
        max_workers=config.get("max_workers", 4),
        default_format=config.get("default_format", ""),
        theme=config.get("theme", "light"),
        cleanup_after_download=config.get("cleanup_after_download", True),
    )


@router.put("/settings", response_model=Settings)
async def update_settings(settings: Settings):
    config = settings.model_dump()
    save_config(config)
    return settings
