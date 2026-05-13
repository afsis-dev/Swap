<!--
Histórico de Alterações:
  Data       | Desenvolvedor  | Ticket | Observação
  -----------|----------------|--------|-------------------
  2026-05-13 | AFSIS Dev      | #001   | Implementação v1.1.0
-->


# Roadmap

## v1.0.0 — Lançamento Inicial
- [x] Conversão de imagens raster (JPG, PNG, WEBP, BMP, TIFF, ICO)
- [x] Conversão SVG → PNG/PDF
- [x] Conversão PDF → PNG, DOCX, TXT
- [x] Conversão de documentos (DOCX, ODT, TXT, RTF, HTML)
- [x] Conversão de planilhas (XLSX, CSV, ODS)
- [x] Drag & drop de arquivos
- [x] Conversão em lote com ThreadPoolExecutor
- [x] Barra de progresso via WebSocket
- [x] Histórico de conversões
- [x] Tema claro/escuro
- [x] Interface 100% web (FastAPI + Vanilla JS)

## v1.1.0 — Atual
- [x] Conversão de eBooks (EPUB, MOBI, AZW3, FB2, LRF, RB, TCR, SNB, PDB)
- [x] Conversão de apresentações (PPT, PPTX, ODP, PPS, PPSX, PPTM, POT, POTX, POTM, PPSM)
- [x] Conversão de vetores (SVG → PNG, PDF, JPG, WEBP)
- [x] Conversão de quadrinhos (CBZ, CBR, CB7 → PDF, CBZ)
- [x] Upload via URL (converter arquivo diretamente de um link)
- [x] Páginas Changelog, Roadmap e Sobre
- [x] Acessibilidade (ARIA labels, navegação por teclado)

## v1.2.0 — Em Breve
- [ ] Compressão de arquivos (ZIP, TAR, GZ)
- [ ] Redimensionamento de imagens em lote
- [ ] Ajuste de qualidade/DPI por arquivo
- [ ] Pré-visualização de arquivos antes da conversão
- [ ] Notificações desktop (Web Notification API)
- [ ] Suporte a pastas (upload de diretório inteiro)
- [ ] Conversão para Markdown via markitdown (Microsoft)

## v1.3.0 — Futuro
- [ ] Autenticação de usuários (OAuth2 / JWT)
- [ ] Painel de administração
- [ ] Agendamento de conversões
- [ ] Integração com armazenamento cloud (Google Drive, Dropbox)
- [ ] API pública documentada com Swagger
- [ ] Rate limiting e quotas por usuário
- [ ] Logs de auditoria

## v2.0.0 — Visão de Longo Prazo
- [ ] Aplicativo mobile (PWA)
- [ ] Processamento distribuído com fila de jobs (Redis/Celery)
- [ ] Suporte a OCR em imagens e PDFs
- [ ] Tradução de documentos via IA
- [ ] Plugins/extensões da comunidade
- [ ] Deploy one-click em VPS próprias
