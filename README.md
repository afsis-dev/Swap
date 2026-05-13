<!--
Histórico de Alterações:
  Data       | Desenvolvedor  | Ticket | Observação
  -----------|----------------|--------|-------------------
  2026-05-13 | AFSIS Dev      | #001   | Implementação v1.1.0
-->

# Swap — Conversor de Arquivos

Aplicação web para converter arquivos entre 50+ formatos. Interface moderna com drag & drop, conversão em lote, progresso via WebSocket e upload por URL.

## Funcionalidades

- **Drag & drop** de arquivos pelo navegador
- **Conversão em lote** com ThreadPoolExecutor
- **Upload via URL** — converter arquivo diretamente de um link
- **Barra de progresso** em tempo real via WebSocket
- **Histórico** das últimas 100 conversões (JSON)
- **Tema claro/escuro** com persistência
- **Acessibilidade** — ARIA labels, navegação por teclado

## Formatos Suportados

| Categoria | Entrada | Saída |
|---|---|---|
| Imagem raster | JPG, PNG, BMP, GIF, TIFF, WEBP, ICO, PPM | JPG, PNG, WEBP, BMP, TIFF, ICO, PDF |
| Imagem vetorial | SVG | PNG, PDF, JPG, WEBP |
| Documento | DOCX, ODT, TXT, RTF, HTML | PDF, DOCX, TXT, HTML |
| PDF | PDF | PNG (páginas), DOCX, TXT |
| Planilha | XLSX, CSV, ODS | XLSX, CSV, PDF |
| Ebook | EPUB, MOBI, AZW3, FB2, LRF, RB, TCR, SNB, PDB | EPUB, PDF, TXT, MOBI |
| Apresentação | PPT, PPTX, ODP, PPS, PPSX, PPTM, POT, POTX, POTM, PPSM | PDF, PPTX, ODP, PNG |
| Quadrinhos | CBZ, CBR, CB7, ZIP, RAR, 7Z | PDF, CBZ |

## Stack

| Camada | Tecnologia |
|--------|-----------|
| Backend | Python 3.11 + FastAPI + Uvicorn |
| Frontend | Vanilla JS (ES6+) + CSS3 + HTML5 |
| Comunicação | REST API + WebSocket |
| Conversão | Pillow, PyMuPDF, cairosvg, openpyxl, pandas, python-docx, Calibre, LibreOffice |
| Deploy | Docker + nginx |

## Instalação

### Dependências do sistema

```bash
# LibreOffice (documentos, apresentações, planilhas → PDF)
sudo apt install libreoffice       # Ubuntu/Debian
sudo dnf install libreoffice       # Fedora
brew install libreoffice           # macOS

# Calibre (eBooks)
sudo apt install calibre           # Ubuntu/Debian
brew install calibre               # macOS

# Ferramentas de arquivo (quadrinhos)
sudo apt install unrar p7zip-full  # Ubuntu/Debian
```

### Python

```bash
git clone https://github.com/afsis-dev/Swap.git
cd Swap

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
```

## Uso

```bash
# Iniciar servidor
uvicorn src.api.main:app --host 0.0.0.0 --port 8000

# Acessar no navegador
open http://localhost:8000/app

# Documentação da API
open http://localhost:8000/docs
```

## Docker

```bash
docker build -t swap .
docker run -p 8000:8000 swap
```

## API Endpoints

| Método | Rota | Descrição |
|--------|------|-----------|
| `POST` | `/api/convert` | Upload + conversão em lote |
| `POST` | `/api/convert/url` | Conversão a partir de URL |
| `GET` | `/api/convert/{job_id}` | Status do job |
| `GET` | `/api/download/{job_id}/{filename}` | Download do arquivo |
| `GET` | `/api/history` | Histórico de conversões |
| `GET` | `/api/formats` | Formatos disponíveis |
| `GET` | `/api/settings` | Configurações |
| `WS` | `/ws/progress/{job_id}` | Progresso em tempo real |

## Estrutura do Projeto

```
Swap/
├── src/
│   ├── api/
│   │   ├── main.py                 # FastAPI app, CORS, lifespan
│   │   ├── models.py               # Pydantic models
│   │   ├── websocket.py            # WebSocket manager
│   │   └── routes/
│   │       ├── convert.py          # Conversão + URL upload
│   │       ├── history.py          # Histórico CRUD
│   │       ├── settings.py         # Configurações
│   │       └── formats.py          # Descoberta de formatos
│   ├── converters/
│   │   ├── base.py                 # BaseConverter ABC
│   │   ├── image.py                # Pillow + cairosvg
│   │   ├── pdf.py                  # PyMuPDF + pdf2docx
│   │   ├── document.py             # python-docx + LibreOffice
│   │   ├── spreadsheet.py          # openpyxl + pandas
│   │   ├── ebook.py                # Calibre
│   │   ├── presentation.py         # LibreOffice Impress
│   │   ├── vector.py               # cairosvg + Pillow
│   │   └── comic.py                # Pillow + zipfile
│   ├── services/
│   │   ├── conversion_service.py   # ThreadPoolExecutor, batch
│   │   ├── history_service.py      # JSON persistence
│   │   └── format_registry.py      # ext → converter map
│   └── utils/
│       ├── config.py               # JSON config
│       ├── file_utils.py           # pathlib helpers
│       └── logger.py               # Structured logging
├── frontend/
│   ├── index.html                  # SPA entry point
│   ├── css/
│   │   ├── main.css                # Layout, componentes
│   │   └── theme.css               # Light/dark tokens
│   └── js/
│       ├── app.js                  # Router, state, DnD
│       ├── api.js                  # REST fetch wrapper
│       ├── websocket.js            # Progress WS client
│       ├── components.js           # UI builders
│       └── utils.js                # Helpers, formatters
├── tests/
│   ├── converters/
│   └── services/
├── requirements.txt
├── pyproject.toml
├── Dockerfile
└── README.md
```

## Testes

```bash
pytest tests/ -v
pytest --cov=src --cov-report=term-missing
pytest --cov=src --cov-report=term-missing --cov-fail-under=80
```

## Configuração

Preferências salvas em `~/.fileconverter/config.json`:

```json
{
  "output_dir": "~/FileConverter",
  "max_workers": 4,
  "quality_jpeg": 85,
  "dpi": 150,
  "theme_mode": "system",
  "language": "pt-BR"
}
```

## Licença

MIT — Projeto mantido pela [AFSIS](https://github.com/afsis-dev/Swap).