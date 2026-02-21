class UI {
    static showModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.add('open');
            modal.classList.remove('hidden');
            modal.classList.add('flex');
            modal.setAttribute('aria-hidden', 'false');
        }
    }

    static hideModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.remove('open');
            modal.classList.add('hidden');
            modal.classList.remove('flex');
            modal.setAttribute('aria-hidden', 'true');
        }
    }

    static showToast(message, type = 'info') {
        const container = document.getElementById('toast-container');
        if (!container) return;

        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `
            <div class="toast-content">
                <span style="font-weight: 600;">${type.toUpperCase()}</span>
                <p>${message}</p>
            </div>
        `;

        container.appendChild(toast);

        setTimeout(() => {
            toast.style.opacity = '0';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    static clearElement(elementId) {
        const el = document.getElementById(elementId);
        if (el) el.innerHTML = '';
    }

    // Helper to show/hide loading spinner (can be used in tables)
    static setLoading(elementId, isLoading) {
        const el = document.getElementById(elementId);
        if (!el) return;
        if (isLoading) {
            el.innerHTML = `<tr><td colspan="10" class="p-4 text-center text-muted">Loading...</td></tr>`;
        }
    }
}

// Global Event Listeners for closing modals
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        document.querySelectorAll('.modal-overlay.open, .tw-modal:not(.hidden)').forEach(modal => {
            UI.hideModal(modal.id);
        });
    }
});

document.addEventListener('click', (e) => {
    if (e.target.classList.contains('modal-overlay') || e.target.classList.contains('tw-modal')) {
        UI.hideModal(e.target.id);
    }
});