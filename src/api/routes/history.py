# Histórico de Alterações:
#   Data       | Desenvolvedor  | Ticket | Observação
#   -----------|----------------|--------|-------------------
#   2026-05-13 | AFSIS Dev      | #001   | Implementação v1.1.0


from fastapi import APIRouter, HTTPException
from src.api.models import HistoryList, HistoryEntry
from src.services.history_service import get_entries, count, delete, clear_history

router = APIRouter(prefix="/api", tags=["history"])


@router.get("/history", response_model=HistoryList)
async def get_history(limit: int = 50, offset: int = 0):
    entries = get_entries(limit=limit, offset=offset)
    total = count()

    return HistoryList(
        entries=[
            HistoryEntry(
                id=e.get("id", ""),
                input_file=e.get("input_file", ""),
                output_file=e.get("output_file", ""),
                format=e.get("format", ""),
                status=e.get("status", ""),
                duration_ms=round(e.get("duration_ms", 0) or 0, 2),
                timestamp=e.get("timestamp", ""),
            )
            for e in entries
        ],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.delete("/history/{entry_id}")
async def delete_history_entry(entry_id: str):
    success = delete(entry_id)
    if not success:
        raise HTTPException(status_code=404, detail="Entry not found")
    return {"message": "Entry deleted"}


@router.post("/history/clear")
async def clear():
    clear_history()
    return {"message": "History cleared"}
