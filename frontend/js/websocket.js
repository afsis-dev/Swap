// Histórico de Alterações:
//   Data       | Desenvolvedor  | Ticket | Observação
//   -----------|----------------|--------|-------------------
//   2026-05-13 | AFSIS Dev      | #001   | Implementação v1.1.0


export class ProgressWS {
    constructor(jobId, handlers) {
        this.jobId = jobId;
        this.handlers = handlers;
        this.ws = null;
    }

    connect() {
        const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = window.location.host;
        this.ws = new WebSocket(`${proto}//${host}/ws/progress/${this.jobId}`);

        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (this.handlers[data.type]) {
                this.handlers[data.type](data);
            }
        };

        this.ws.onclose = () => {
            if (this.handlers.onClose) {
                this.handlers.onClose();
            }
        };

        this.ws.onerror = () => {
            if (this.handlers.onError) {
                this.handlers.onError();
            }
        };
    }

    close() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    }
}
