# Histórico de Alterações:
#   Data       | Desenvolvedor  | Ticket | Observação
#   -----------|----------------|--------|-------------------
#   2026-05-13 | AFSIS Dev      | #001   | Implementação v1.1.0


#!/usr/bin/env python3
"""Run the Swap web application."""

import sys
import uvicorn

if __name__ == "__main__":
    host = sys.argv[1] if len(sys.argv) > 1 else "0.0.0.0"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8000

    print(f"Swap — Conversor de Arquivos")
    print(f"Backend:  http://{host}:{port}")
    print(f"Frontend: http://{host}:{port}/app/")
    print(f"Docs:     http://{host}:{port}/docs")
    print()

    uvicorn.run("src.api.main:app", host=host, port=port, reload=True)
