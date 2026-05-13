<!--
Histórico de Alterações:
  Data       | Desenvolvedor  | Ticket | Observação
  -----------|----------------|--------|-------------------
  2026-05-13 | AFSIS Dev      | #001   | Implementação v1.1.0
-->


# Swap — Conversor de Arquivos

Aplicação desktop para converter arquivos entre múltiplos formatos de imagem, documento e planilha. Interface moderna com drag & drop, conversão em lote e progresso em tempo real.

## Funcionalidades

- **Drag & drop** de arquivos e pastas
- **Conversão em lote** com múltiplos arquivos simultâneos
- **Configurações por formato** (qualidade JPEG, DPI, redimensionamento)
- **Barra de progresso** global e individual por arquivo
- **Histórico** das últimas 100 conversões
- **Tema claro/escuro** com persistência
- **Log de erros** com detalhes por arquivo

## Formatos Suportados

| Categoria | Entrada | Saída |
|---|---|---|
| Imagem raster | JPG, PNG, BMP, GIF, TIFF, WEBP, ICO, PPM | JPG, PNG, WEBP, BMP, TIFF, ICO, PDF |
| Imagem vetorial | SVG | PNG, PDF |
| Documento | DOCX, ODT, TXT, RTF, HTML | PDF, DOCX, TXT, HTML |
| PDF | PDF | PNG (por página), DOCX, TXT |
| Planilha | XLSX, CSV, ODS | XLSX, CSV, PDF |

## Instalação

### Dependências do sistema

Para conversão de documentos (ODT, RTF → PDF/DOCX), instale o LibreOffice:

```bash
# Ubuntu/Debian
sudo apt install libreoffice

# Fedora
sudo dnf install libreoffice

# macOS
brew install libreoffice

# Windows
# Baixe em https://www.libreoffice.org/download/
```

### Python

```bash
# Clone o repositório
git clone <repo-url>
cd Swap

# Crie ambiente virtual
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# ou
.venv\Scripts\activate     # Windows

# Instale dependências
pip install -r requirements.txt
```

## Uso

```bash
# Execute com Flet
flet run src/main.py

# Ou diretamente com Python
python src/main.py
```

## Build

```bash
# Linux (AppImage)
flet build linux

# Windows (.exe)
flet build windows

# macOS (.app)
flet build macos
```

## Testes

```bash
# Executar todos os testes
pytest tests/ -v

# Com cobertura
pytest --cov=src --cov-report=term-missing

# Cobertura mínima 80%
pytest --cov=src --cov-report=term-missing --cov-fail-under=80
```

## Estrutura do Projeto

```
Swap/
├── src/
│   ├── main.py                    # Entry point Flet
│   ├── app.py                     # App root, roteamento
│   ├── ui/
│   │   ├── pages/                 # Home, History, Settings
│   │   ├── components/            # FileList, FormatPicker, ProgressView
│   │   └── theme.py               # Tokens claro/escuro
│   ├── converters/
│   │   ├── base.py                # BaseConverter ABC
│   │   ├── image.py               # Pillow + cairosvg
│   │   ├── pdf.py                 # PyMuPDF + pdf2docx
│   │   ├── document.py            # python-docx + LibreOffice
│   │   └── spreadsheet.py         # openpyxl + pandas
│   ├── services/
│   │   ├── conversion_service.py  # ThreadPoolExecutor, batch
│   │   ├── history_service.py     # JSON persistence
│   │   └── format_registry.py     # ext → converter map
│   └── utils/
│       ├── config.py              # JSON config
│       ├── file_utils.py          # pathlib helpers
│       └── logger.py              # logging
├── tests/
│   ├── converters/
│   └── services/
├── requirements.txt
├── pyproject.toml
└── README.md
```

## Configuração

As preferências são salvas em `~/.fileconverter/config.json`:

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

MIT
