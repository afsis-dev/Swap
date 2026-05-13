// Histórico de Alterações:
//   Data       | Desenvolvedor  | Ticket | Observação
//   -----------|----------------|--------|-------------------
//   2026-05-13 | AFSIS Dev      | #001   | Implementação v1.1.0


export const ICONS = {
    check: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>`,
    x: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>`,
    download: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>`,
    chevronDown: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"/></svg>`,
};

export function createFileItem(file, index, availableFormats, selectedFormat) {
    const ext = file.name.split('.').pop().toLowerCase();
    const div = document.createElement('div');
    div.className = 'file-item';
    div.dataset.index = index;

    const fmtOptions = (availableFormats || []).map(fmt => {
        const clean = fmt.replace('.', '').toUpperCase();
        const sel = clean.toLowerCase() === (selectedFormat || '').toLowerCase() ? ' selected' : '';
        return `<option value="${clean.toLowerCase()}"${sel}>${clean}</option>`;
    }).join('');

    div.innerHTML = `
        <div class="file-icon">${ext.substring(0, 4)}</div>
        <div class="file-info">
            <div class="file-name">${file.name}</div>
            <div class="file-size">${formatSize(file.size)}</div>
        </div>
        <div class="file-format-selector">
            <select class="fmt-select" data-index="${index}">
                ${fmtOptions}
            </select>
        </div>
        <button class="file-remove" data-index="${index}" title="Remover">${ICONS.x}</button>
    `;

    return div;
}

export function createFormatCategory(category, formats, activeFormat) {
    const div = document.createElement('div');
    div.className = 'format-category';
    div.dataset.category = category.id;

    const count = formats.length;
    div.innerHTML = `
        <div class="format-category-header">
            <span class="format-cat-icon">${category.icon}</span>
            <span class="format-cat-name">${category.name}</span>
            <span class="format-cat-count">${count}</span>
            <span class="format-cat-chevron">${ICONS.chevronDown}</span>
        </div>
        <div class="format-options">
            ${formats.map(fmt => `
                <button class="format-chip${fmt === activeFormat ? ' active' : ''}" data-format="${fmt}">
                    ${fmt.toUpperCase()}
                </button>
            `).join('')}
        </div>
    `;

    const header = div.querySelector('.format-category-header');
    header.addEventListener('click', () => {
        const wasOpen = div.classList.contains('open');
        div.closest('.format-categories').querySelectorAll('.format-category').forEach(c => c.classList.remove('open'));
        if (!wasOpen) div.classList.add('open');
    });

    return div;
}

export function createResultCard(name, success, outputSize, originalSize, error) {
    const div = document.createElement('div');
    div.className = `result-card ${success ? 'success' : 'error'}`;

    let sizeInfo = '';
    if (success && originalSize && outputSize !== null && outputSize !== undefined) {
        const diff = outputSize - originalSize;
        const pct = originalSize > 0 ? Math.round((diff / originalSize) * 100) : 0;
        const sizeClass = diff <= 0 ? 'smaller' : 'larger';
        const sign = diff <= 0 ? '' : '+';
        sizeInfo = `<span class="size-change ${sizeClass}">${sign}${pct}%</span>`;
    }

    const meta = success
        ? `<div class="result-meta">
               <span>${formatSize(originalSize)} → ${formatSize(outputSize)}</span>
               ${sizeInfo}
           </div>`
        : `<div class="result-meta">${error || 'Erro na conversão'}</div>`;

    div.innerHTML = `
        <div class="result-icon">${success ? ICONS.check : ICONS.x}</div>
        <div class="result-info">
            <div class="result-name">${name}</div>
            ${meta}
        </div>
        ${success ? `<button class="result-download" title="Baixar">${ICONS.download}</button>` : ''}
    `;

    return div;
}

export function createHistoryItem(entry) {
    const div = document.createElement('div');
    div.className = 'history-item';

    const statusClass = entry.status === 'success' ? 'success' : 'error';
    const fileName = entry.input_file ? entry.input_file.split('/').pop() : 'Arquivo';
    const fmt = entry.format ? entry.format.replace('.', '').toUpperCase() : '';
    const duration = formatDuration(entry.duration_ms);
    const date = formatDate(entry.timestamp);

    div.innerHTML = `
        <div class="history-status ${statusClass}">${statusClass === 'success' ? ICONS.check : ICONS.x}</div>
        <div class="history-info">
            <div class="history-file">${fileName}</div>
            <div class="history-detail">
                <span>${fmt}</span>
                <span>·</span>
                <span>${duration}</span>
            </div>
        </div>
        <div class="history-date">${date}</div>
    `;

    return div;
}

function formatSize(bytes) {
    if (bytes === 0 || bytes == null) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

function formatDuration(ms) {
    if (!ms) return '—';
    if (ms < 1000) return `${Math.round(ms)}ms`;
    return `${(ms / 1000).toFixed(1)}s`;
}

function formatDate(isoString) {
    if (!isoString) return '—';
    return new Date(isoString).toLocaleString('pt-BR', {
        day: '2-digit', month: '2-digit', year: 'numeric',
        hour: '2-digit', minute: '2-digit',
    });
}