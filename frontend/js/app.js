// Histórico de Alterações:
//   Data       | Desenvolvedor  | Ticket | Observação
//   -----------|----------------|--------|-------------------
//   2026-05-13 | AFSIS Dev      | #001   | Implementação v1.1.0


const APP_VERSION = '1.1.0';

import * as api from './api.js';
import { ProgressWS } from './websocket.js';
import { createFileItem, createResultCard, createHistoryItem } from './components.js';
import { formatSize, showToast, getExtension, FORMAT_CATEGORIES } from './utils.js';

class App {
    constructor() {
        this.selectedFiles = [];
        this.fileFormats = new Map();
        this.isConverting = false;
        this.formats = {};
        this.conversionResults = [];
        this.originalSizes = {};
        this.currentJobId = null;

        this.initElements();
        this.bindEvents();
        this.loadFormats();
        this.applyTheme(this.getPreferredTheme());
        this.animateEntry();
    }

    initElements() {
        this.dropZone = document.getElementById('drop-zone');
        this.fileInput = document.getElementById('file-input');
        this.filePanel = document.getElementById('file-panel');
        this.fileList = document.getElementById('file-list');
        this.fileCount = document.getElementById('file-count');
        this.clearBtn = document.getElementById('clear-btn');
        this.convertBtn = document.getElementById('convert-btn');
        this.convertSummary = document.getElementById('convert-summary');
        this.summaryCount = document.getElementById('summary-count');
        this.progressCard = document.getElementById('progress-card');
        this.progressBar = document.getElementById('progress-bar');
        this.progressLabel = document.getElementById('progress-label');
        this.progressPercent = document.getElementById('progress-percent');
        this.resultsCard = document.getElementById('results-card');
        this.resultsList = document.getElementById('results-list');
        this.downloadAllBtn = document.getElementById('download-all-btn');
        this.historyList = document.getElementById('history-list');
        this.historyEmpty = document.getElementById('history-empty');
        this.clearHistoryBtn = document.getElementById('clear-history-btn');
        this.themeToggle = document.getElementById('theme-toggle');
        this.convertCard = document.getElementById('convert-card');

        this.tabDrop = document.getElementById('tab-drop');
        this.tabUrl = document.getElementById('tab-url');
        this.urlCard = document.getElementById('url-card');
        this.urlInput = document.getElementById('url-input');
        this.urlFormat = document.getElementById('url-format');
        this.urlFetchBtn = document.getElementById('url-fetch-btn');
        this.urlHint = document.getElementById('url-hint');
        this.uploadMode = 'drop';
    }

    bindEvents() {
        document.querySelectorAll('.topbar-btn').forEach(btn => {
            btn.addEventListener('click', () => this.navigate(btn.dataset.page));
        });

        this.dropZone.addEventListener('click', () => this.fileInput.click());
        this.fileInput.addEventListener('change', (e) => this.handleFiles(e.target.files));

        this.dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            this.dropZone.classList.add('drag-over');
        });

        this.dropZone.addEventListener('dragleave', () => {
            this.dropZone.classList.remove('drag-over');
        });

        this.dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            this.dropZone.classList.remove('drag-over');
            if (e.dataTransfer.files.length) this.handleFiles(e.dataTransfer.files);
        });

        this.clearBtn.addEventListener('click', () => this.resetConverter());
        this.convertBtn.addEventListener('click', () => this.startConversion());
        this.downloadAllBtn.addEventListener('click', () => this.downloadAll());
        this.clearHistoryBtn.addEventListener('click', () => this.clearHistory());
        this.themeToggle.addEventListener('click', () => this.toggleTheme());

        this.tabDrop.addEventListener('click', () => this.switchUploadMode('drop'));
        this.tabUrl.addEventListener('click', () => this.switchUploadMode('url'));

        this.urlInput.addEventListener('input', () => this.updateUrlButton());
        this.urlFormat.addEventListener('change', () => this.updateUrlButton());
        this.urlFetchBtn.addEventListener('click', () => this.startUrlConversion());

        this.fileList.addEventListener('click', (e) => {
            const removeBtn = e.target.closest('.file-remove');
            if (removeBtn) this.animateRemoveFile(parseInt(removeBtn.dataset.index));
        });

        this.fileList.addEventListener('change', (e) => {
            const select = e.target.closest('.fmt-select');
            if (select) {
                const index = parseInt(select.dataset.index);
                const file = this.selectedFiles[index];
                if (file) {
                    this.fileFormats.set(file.name, `.${select.value}`);
                    this.updateSummary();
                    this.updateConvertButton();
                }
            }
        });

        document.addEventListener('keydown', (e) => this.handleKeyboard(e));
    }

    animateEntry() {
        document.querySelectorAll('.topbar-btn').forEach((btn, i) => {
            btn.style.animation = `fadeScale 0.4s var(--ease-spring) ${i * 0.06}s both`;
        });
    }

    switchUploadMode(mode) {
        this.uploadMode = mode;
        this.tabDrop.classList.toggle('active', mode === 'drop');
        this.tabDrop.setAttribute('aria-pressed', mode === 'drop');
        this.tabUrl.classList.toggle('active', mode === 'url');
        this.tabUrl.setAttribute('aria-pressed', mode === 'url');

        if (mode === 'url') {
            this.resetConverter();
            this.populateUrlFormats();
            this.urlHint.textContent = '';
            this.urlInput.classList.remove('invalid');
        }

        this.dropZone.hidden = mode !== 'drop';
        this.urlCard.hidden = mode !== 'url';
    }

    populateUrlFormats() {
        const allFormats = [];
        const seen = new Set();
        for (const [ext, info] of Object.entries(this.formats)) {
            for (const out of info.outputs || []) {
                const clean = out.replace('.', '').toLowerCase();
                if (!seen.has(clean)) {
                    seen.add(clean);
                    allFormats.push(clean);
                }
            }
        }
        allFormats.sort();

        this.urlFormat.innerHTML = '<option value="">Formato</option>' +
            allFormats.map(f => `<option value="${f}">${f.toUpperCase()}</option>`).join('');
    }

    updateUrlButton() {
        const raw = this.urlInput.value.trim();
        const hasFormat = this.urlFormat.value.length > 0;

        this.urlHint.textContent = '';
        this.urlHint.className = 'url-hint';
        this.urlInput.classList.remove('invalid');

        if (raw.length === 0) {
            this.urlFetchBtn.disabled = true;
            return;
        }

        let parsed;
        try {
            parsed = new URL(raw);
        } catch {
            this.urlHint.textContent = 'URL inválida — use http:// ou https://';
            this.urlHint.className = 'url-hint error';
            this.urlInput.classList.add('invalid');
            this.urlFetchBtn.disabled = true;
            return;
        }

        if (parsed.protocol !== 'http:' && parsed.protocol !== 'https:') {
            this.urlHint.textContent = 'Apenas URLs HTTP/HTTPS são permitidas';
            this.urlHint.className = 'url-hint error';
            this.urlInput.classList.add('invalid');
            this.urlFetchBtn.disabled = true;
            return;
        }

        const host = parsed.hostname.toLowerCase();
        if (host === 'localhost' || host === '127.0.0.1' || host === '0.0.0.0' || host === '[::1]') {
            this.urlHint.textContent = 'URLs locais não são permitidas';
            this.urlHint.className = 'url-hint error';
            this.urlInput.classList.add('invalid');
            this.urlFetchBtn.disabled = true;
            return;
        }

        this.urlFetchBtn.disabled = !(hasFormat && !this.isConverting);
    }

    async startUrlConversion() {
        const url = this.urlInput.value.trim();
        const fmt = this.urlFormat.value;
        if (!url || !fmt) return;

        this.isConverting = true;
        this.updateUrlButton();
        this.conversionResults = [];
        this.resultsList.innerHTML = '';
        this.resultsCard.hidden = true;
        this.downloadAllBtn.hidden = true;

        this.progressCard.hidden = false;
        this.progressCard.style.animation = 'none';
        this.progressCard.offsetHeight;
        this.progressCard.style.animation = 'fadeScale 0.3s var(--ease-base)';
        this.updateProgress(0, 'Baixando arquivo da URL...');

        try {
            const response = await api.convertUrl(url, fmt, {});

            this.currentJobId = response.job_id;
            this.connectWebSocket(response.job_id);
        } catch (e) {
            showToast(`Erro: URL inválida ou arquivo não encontrado`, 'error');
            this.isConverting = false;
            this.updateUrlButton();
            this.progressCard.hidden = true;
        }
    }

    handleKeyboard(e) {
        if (e.key === 'Escape') {
            if (this.progressCard.hidden === false) {
                this.progressCard.hidden = true;
                this.isConverting = false;
                this.updateConvertButton();
                this.updateUrlButton();
            }
        }

        if (e.ctrlKey || e.metaKey) {
            const pageMap = { '1': 'converter', '2': 'history', '3': 'changelog', '4': 'roadmap', '5': 'about' };
            const page = pageMap[e.key];
            if (page) {
                e.preventDefault();
                this.navigate(page);
            }
        }
    }

    navigate(page) {
        document.querySelectorAll('.topbar-btn').forEach(b => b.classList.remove('active'));
        const targetBtn = document.querySelector(`.topbar-btn[data-page="${page}"]`);
        targetBtn.classList.add('active');

        document.querySelectorAll('.page').forEach(p => {
            p.classList.remove('active');
            p.hidden = true;
        });
        const target = document.getElementById(`page-${page}`);
        target.hidden = false;
        requestAnimationFrame(() => target.classList.add('active'));

        if (page === 'history') this.loadHistory();
    }

    handleFiles(fileList) {
        const files = Array.from(fileList);
        let added = 0;
        files.forEach(file => {
            if (!this.selectedFiles.some(f => f.name === file.name && f.size === file.size)) {
                this.selectedFiles.push(file);
                this.originalSizes[file.name] = file.size;

                const ext = getExtension(file.name);
                const availableOutputs = this.formats[ext]?.outputs || [];

                if (availableOutputs.length > 0) {
                    const clean = availableOutputs.map(f => f.replace('.', '').toLowerCase());
                    const existing = this.fileFormats.get(file.name);
                    if (!existing || !clean.includes(existing.replace('.', '').toLowerCase())) {
                        this.fileFormats.set(file.name, `.${clean[0]}`);
                    }
                } else {
                    this.fileFormats.set(file.name, '');
                }

                added++;
            }
        });

        if (added > 0) {
            this.updateFileList();
        }
    }

    getAvailableFormats(file) {
        const ext = getExtension(file.name);
        const availableOutputs = this.formats[ext]?.outputs || [];
        return availableOutputs.map(f => f.replace('.', '').toLowerCase());
    }

    updateFileList() {
        this.fileList.innerHTML = '';
        this.selectedFiles.forEach((file, index) => {
            const availableFormats = this.getAvailableFormats(file);
            const selectedFormat = this.fileFormats.get(file.name) || '';
            const item = createFileItem(file, index, availableFormats, selectedFormat.replace('.', ''));
            this.fileList.appendChild(item);
        });

        const hasFiles = this.selectedFiles.length > 0;
        if (hasFiles && this.filePanel.hidden) {
            this.filePanel.hidden = false;
        }
        this.fileCount.textContent = `${this.selectedFiles.length} arquivo${this.selectedFiles.length !== 1 ? 's' : ''}`;
        this.dropZone.hidden = hasFiles;
        this.updateSummary();
        this.updateConvertButton();
    }

    updateSummary() {
        const ready = this.selectedFiles.filter(f => this.fileFormats.has(f.name) && this.fileFormats.get(f.name)).length;
        if (ready === 0 && this.selectedFiles.length === 0) {
            this.convertSummary.hidden = true;
        } else {
            this.convertSummary.hidden = false;
            this.summaryCount.textContent = `${ready}/${this.selectedFiles.length}`;
        }
    }

    animateRemoveFile(index) {
        const items = this.fileList.querySelectorAll('.file-item');
        const item = items[index];
        if (!item) return;

        item.style.animation = 'none';
        item.offsetHeight;
        item.style.transition = 'all 0.25s cubic-bezier(0.4,0,0.2,1)';
        item.style.opacity = '0';
        item.style.transform = 'translateX(20px)';

        setTimeout(() => {
            const file = this.selectedFiles[index];
            delete this.originalSizes[file.name];
            this.fileFormats.delete(file.name);
            this.selectedFiles.splice(index, 1);

            if (this.selectedFiles.length === 0) {
                this.resetConverter();
            } else {
                this.updateFileList();
            }
        }, 250);
    }

    resetConverter() {
        this.selectedFiles = [];
        this.fileFormats.clear();
        this.originalSizes = {};
        this.conversionResults = [];
        this.currentJobId = null;
        this.filePanel.hidden = true;
        this.dropZone.hidden = false;
        this.convertSummary.hidden = true;
        this.progressCard.hidden = true;
        this.resultsCard.hidden = true;
        this.downloadAllBtn.hidden = true;
        this.fileInput.value = '';
        this.fileList.innerHTML = '';
        this.updateConvertButton();
    }

    async loadFormats() {
        try {
            const response = await api.getFormats();
            this.formats = response.formats;
            this.populateUrlFormats();
        } catch (e) {
            console.error('Failed to load formats:', e);
        }
    }

    updateConvertButton() {
        const hasFiles = this.selectedFiles.length > 0;
        const allHaveFormat = hasFiles && this.selectedFiles.every(f => {
            const fmt = this.fileFormats.get(f.name);
            return fmt && fmt.length > 0;
        });
        const disabled = !(hasFiles && allHaveFormat && !this.isConverting);
        const wasDisabled = this.convertBtn.disabled;
        this.convertBtn.disabled = disabled;

        if (!disabled && wasDisabled) {
            this.convertBtn.style.animation = 'none';
            this.convertBtn.offsetHeight;
            this.convertBtn.style.animation = 'celebratePop 0.4s var(--ease-spring)';
        }
    }

    buildFormatMap() {
        const map = {};
        this.selectedFiles.forEach(f => {
            map[f.name] = this.fileFormats.get(f.name) || '.png';
        });
        return map;
    }

    async startConversion() {
        if (!this.selectedFiles.length) return;

        const formatMap = this.buildFormatMap();
        if (Object.values(formatMap).every(v => !v)) {
            showToast('Selecione um formato para cada arquivo', 'error');
            return;
        }

        this.isConverting = true;
        this.updateConvertButton();
        this.conversionResults = [];
        this.resultsList.innerHTML = '';
        this.resultsCard.hidden = true;
        this.downloadAllBtn.hidden = true;

        this.progressCard.hidden = false;
        this.progressCard.style.animation = 'none';
        this.progressCard.offsetHeight;
        this.progressCard.style.animation = 'fadeScale 0.3s var(--ease-base)';
        this.updateProgress(0, 'Enviando arquivos...');

        try {
            const response = await api.uploadFiles(this.selectedFiles, formatMap, {});

            this.currentJobId = response.job_id;
            this.connectWebSocket(response.job_id);
        } catch (e) {
            showToast('Erro ao iniciar conversão', 'error');
            this.isConverting = false;
            this.updateConvertButton();
            this.progressCard.hidden = true;
        }
    }

    connectWebSocket(jobId) {
        const ws = new ProgressWS(jobId, {
            progress: (data) => {
                this.updateProgress(data.percent, `Convertendo ${data.file}...`);
            },
            result: (data) => {
                const originalSize = this.originalSizes[data.file] || 0;
                const outputSize = data.output_size || 0;
                const card = createResultCard(data.file, data.success, outputSize, originalSize, data.error);

                const downloadBtn = card.querySelector('.result-download');
                if (downloadBtn && data.success && data.output) {
                    downloadBtn.addEventListener('click', () => api.downloadFile(this.currentJobId, data.output));
                }

                this.resultsList.appendChild(card);
                this.conversionResults.push(data);
            },
            done: (data) => {
                this.updateProgress(1.0, 'Conversão concluída!');

                setTimeout(() => {
                    this.progressCard.style.animation = 'fadeScale 0.3s var(--ease-base) reverse both';
                    setTimeout(() => {
                        this.progressCard.hidden = true;
                        this.resultsCard.hidden = false;
                        this.resultsCard.style.animation = 'fadeScale 0.35s var(--ease-spring)';
                        this.downloadAllBtn.hidden = data.success_count === 0;

                        if (data.success_count > 0) {
                            this.convertCard.style.animation = 'none';
                            this.convertCard.offsetHeight;
                            this.convertCard.style.animation = 'celebratePop 0.5s var(--ease-spring)';
                        }
                    }, 300);
                }, 600);

                this.isConverting = false;
                this.updateConvertButton();

                const emoji = data.error_count === 0 ? 'Tudo certo!' : `${data.error_count} falha(s)`;
                showToast(`${data.success_count} convertido${data.success_count !== 1 ? 's' : ''} — ${emoji}`, data.error_count === 0 ? 'success' : 'error');
            },
            error: (data) => {
                showToast(`Erro: ${data.message}`, 'error');
                this.progressCard.hidden = true;
                this.isConverting = false;
                this.updateConvertButton();
            },
            onClose: () => {
                this.isConverting = false;
                this.updateConvertButton();
            },
            onError: () => {
                showToast('Erro de conexão', 'error');
                this.progressCard.hidden = true;
                this.isConverting = false;
                this.updateConvertButton();
            }
        });

        ws.connect();
    }

    updateProgress(percent, text) {
        this.progressBar.style.width = `${percent * 100}%`;
        this.progressLabel.textContent = text;
        this.progressPercent.textContent = `${Math.round(percent * 100)}%`;
    }

    downloadAll() {
        this.conversionResults
            .filter(r => r.success && r.output)
            .forEach(r => api.downloadFile(this.currentJobId, r.output));

        this.downloadAllBtn.style.animation = 'none';
        this.downloadAllBtn.offsetHeight;
        this.downloadAllBtn.style.animation = 'celebratePop 0.4s var(--ease-spring)';
    }

    async loadHistory() {
        try {
            const response = await api.getHistory();
            this.historyList.innerHTML = '';

            if (!response.entries || response.entries.length === 0) {
                this.historyEmpty.hidden = false;
                return;
            }

            this.historyEmpty.hidden = true;
            response.entries.forEach(entry => {
                this.historyList.appendChild(createHistoryItem(entry));
            });
        } catch (e) {
            showToast('Erro ao carregar histórico', 'error');
        }
    }

    async clearHistory() {
        try {
            await api.clearHistory();
            this.loadHistory();
            showToast('Histórico limpo', 'success');
        } catch (e) {
            showToast('Erro ao limpar histórico', 'error');
        }
    }

    getPreferredTheme() {
        const stored = localStorage.getItem('swap-theme');
        if (stored) return stored;
        return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }

    toggleTheme() {
        const current = document.documentElement.getAttribute('data-theme');
        const next = current === 'dark' ? 'light' : 'dark';
        this.applyTheme(next);
        localStorage.setItem('swap-theme', next);
    }

    applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);

        const logoLight = document.querySelector('[data-logo="light"]');
        const logoDark = document.querySelector('[data-logo="dark"]');
        if (logoLight && logoDark) {
            if (theme === 'dark') {
                logoLight.hidden = true;
                logoDark.hidden = false;
            } else {
                logoLight.hidden = false;
                logoDark.hidden = true;
            }
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    window.app = new App();
});