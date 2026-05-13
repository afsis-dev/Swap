# Histórico de Alterações:
#   Data       | Desenvolvedor  | Ticket | Observação
#   -----------|----------------|--------|-------------------
#   2026-05-13 | AFSIS Dev      | #001   | Implementação v1.1.0


from src.api.websocket import ws_manager
from src.services.conversion_service import ConversionService
from src.utils.config import load_config, save_config


def get_ws_manager():
    return ws_manager


def get_conversion_service() -> ConversionService:
    config = load_config()
    return ConversionService(max_workers=config.get("max_workers", 4))


def get_settings():
    return load_config()


def save_settings(settings: dict):
    save_config(settings)
    return settings