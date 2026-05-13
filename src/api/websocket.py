# Histórico de Alterações:
#   Data       | Desenvolvedor  | Ticket | Observação
#   -----------|----------------|--------|-------------------
#   2026-05-13 | AFSIS Dev      | #001   | Implementação v1.1.0


import asyncio
from fastapi import WebSocket


class WebSocketManager:
    def __init__(self):
        self.connections: dict[str, WebSocket] = {}
        self._queues: dict[str, asyncio.Queue] = {}

    def ensure_queue(self, job_id: str) -> asyncio.Queue:
        if job_id not in self._queues:
            self._queues[job_id] = asyncio.Queue()
        return self._queues[job_id]

    async def connect(self, job_id: str, ws: WebSocket):
        await ws.accept()
        self.connections[job_id] = ws
        self.ensure_queue(job_id)
        queue = self._queues[job_id]
        try:
            while True:
                data = await queue.get()
                await ws.send_json(data)
                if data.get("type") in ("done", "error"):
                    break
        except Exception:
            pass
        finally:
            self.disconnect(job_id)

    def disconnect(self, job_id: str):
        self.connections.pop(job_id, None)
        self._queues.pop(job_id, None)

    def send_progress_sync(self, job_id: str, data: dict, loop: asyncio.AbstractEventLoop):
        queue = self.ensure_queue(job_id)
        asyncio.run_coroutine_threadsafe(queue.put(data), loop)

    async def send_progress(self, job_id: str, data: dict):
        queue = self.ensure_queue(job_id)
        await queue.put(data)


ws_manager = WebSocketManager()