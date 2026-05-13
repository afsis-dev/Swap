// Histórico de Alterações:
//   Data       | Desenvolvedor  | Ticket | Observação
//   -----------|----------------|--------|-------------------
//   2026-05-13 | AFSIS Dev      | #001   | Implementação v1.1.0


const API_BASE = window.location.origin;

export async function api(path, options = {}) {
    const response = await fetch(`${API_BASE}${path}`, {
        headers: { 'Content-Type': 'application/json', ...options.headers },
        ...options,
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return response.json();
}

export async function uploadFiles(files, formatMap, options = {}) {
    const formData = new FormData();
    files.forEach(f => formData.append('files', f));
    formData.append('format_map', JSON.stringify(formatMap));
    formData.append('options', JSON.stringify(options));

    const response = await fetch(`${API_BASE}/api/convert`, {
        method: 'POST',
        body: formData,
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return response.json();
}

export async function getJobStatus(jobId) {
    return api(`/api/convert/${jobId}`);
}

export async function getHistory(limit = 50, offset = 0) {
    return api(`/api/history?limit=${limit}&offset=${offset}`);
}

export async function clearHistory() {
    return api('/api/history/clear', { method: 'POST' });
}

export async function getSettings() {
    return api('/api/settings');
}

export async function saveSettings(settings) {
    return api('/api/settings', {
        method: 'PUT',
        body: JSON.stringify(settings),
    });
}

export async function getFormats() {
    return api('/api/formats');
}

export async function getFormat(ext) {
    return api(`/api/formats/${ext}`);
}

export function downloadFile(jobId, filename) {
    const a = document.createElement('a');
    a.href = `${API_BASE}/api/download/${jobId}/${filename}`;
    a.download = filename;
    a.click();
}

export async function convertUrl(url, targetFormat, options = {}) {
    const response = await fetch(`${API_BASE}/api/convert/url`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            url: url,
            target_format: targetFormat,
            options: options,
        }),
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return response.json();
}