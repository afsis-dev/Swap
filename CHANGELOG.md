<!--
Histórico de Alterações:
  Data       | Desenvolvedor  | Ticket | Observação
  -----------|----------------|--------|-------------------
  2026-05-13 | AFSIS Dev      | #001   | Implementação v1.1.0
-->


# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2026-05-13

### Added

- Conversão de eBooks (EPUB, MOBI, AZW3, FB2, LRF, RB, TCR, SNB, PDB) via Calibre e LibreOffice
- Conversão de apresentações (PPT, PPTX, ODP, PPS, PPSX, PPTM, POT, POTX, POTM, PPSM) via LibreOffice
- Conversão de vetores (SVG → PNG, PDF, JPG, WEBP) via cairosvg + Pillow
- Conversão de quadrinhos (CBZ, CBR, CB7 → PDF, CBZ) via Pillow
- Upload via URL (`POST /api/convert/url`) — converter arquivo diretamente de um link
- Acessibilidade com ARIA labels e navegação por teclado (Ctrl+1-5 para páginas, Esc para cancelar)
- Páginas Changelog, Roadmap e Sobre no menu de navegação
- Checkboxes visuais no Roadmap (☑/☐) com progresso por versão
- Informações da organização AFSIS e link do repositório na página Sobre
- Abas de upload: Arrastar arquivos / Colar URL
- Favicon atualizado (logo preta)

### Changed

- Melhorias de alinhamento e espaçamento uniforme em todos os componentes
- Atualização do endpoint `/health` para retornar versão 1.1.0

### Fixed

- Erro na conversão XLSX → PDF via LibreOffice (arquivo copiado para diretório local antes da conversão)
- Mensagens de erro do LibreOffice agora incluem stdout quando stderr está vazio

## [1.0.0] - 2026-05-12

### Added

- Conversão de imagens raster (JPG, PNG, WEBP, BMP, TIFF, ICO) via Pillow
- Conversão SVG → PNG/PDF via cairosvg
- Conversão PDF → PNG (por página), DOCX, TXT via PyMuPDF e pdf2docx
- Conversão de documentos (DOCX, ODT, TXT, RTF, HTML) via python-docx e LibreOffice
- Conversão de planilhas (XLSX, CSV, ODS) via openpyxl e pandas
- Drag & drop de arquivos na interface
- Conversão em lote com ThreadPoolExecutor
- Barra de progresso global e individual
- Histórico de conversões com persistência JSON
- Configurações por formato (qualidade, DPI, redimensionamento)
- Tema claro/escuro com persistência
- Interface Flet com Material 3
- Localização pt-BR
- Tratamento de erros por arquivo (falha isolada no lote)
- Log estruturado em `~/.fileconverter/fileconverter.log`
- Testes unitários com pytest
