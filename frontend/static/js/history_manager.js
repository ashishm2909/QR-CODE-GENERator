class HistoryManager {
    constructor() {
        this.storageKey = 'qr_history';
        this.maxSize = 10;
        this.history = this.load();
    }

    load() {
        const data = localStorage.getItem(this.storageKey);
        return data ? JSON.parse(data) : [];
    }

    save() {
        localStorage.setItem(this.storageKey, JSON.stringify(this.history));
    }

    add(qrData, type, label) {
        // Remove duplicate if exists
        this.history = this.history.filter(item => item.qrData !== qrData);
        
        // Add to beginning
        this.history.unshift({
            qrData,
            type,
            label,
            timestamp: new Date().toISOString()
        });

        // Limit size
        if (this.history.length > this.maxSize) {
            this.history.pop();
        }

        this.save();
        this.render();
    }

    render() {
        const container = document.getElementById('historyContainer');
        if (!container) return;

        if (this.history.length === 0) {
            container.innerHTML = '<p class="text-muted">No recent history.</p>';
            return;
        }

        container.innerHTML = this.history.map((item, index) => `
            <div class="history-item" onclick="historyManager.restore(${index})">
                <img src="${item.qrData}" alt="QR Mini" class="history-mini">
                <div class="history-info">
                    <span class="history-type">${item.type}</span>
                    <span class="history-label">${item.label || 'Unnamed'}</span>
                </div>
            </div>
        `).join('');
    }

    restore(index) {
        const item = this.history[index];
        const preview = document.getElementById('qrPreview');
        if (preview) {
            preview.innerHTML = `<img src="${item.qrData}" alt="Restored QR Code" style="max-width: 100%; border-radius: 8px;">`;
        }
    }
}

const historyManager = new HistoryManager();
document.addEventListener('DOMContentLoaded', () => historyManager.render());
