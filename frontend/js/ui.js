class UI {
    static showModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.add('open');
            modal.setAttribute('aria-hidden', 'false');
        }
    }

    static hideModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.remove('open');
            modal.setAttribute('aria-hidden', 'true');
        }
    }

    static showToast(message, type = 'info') {
        const container = document.getElementById('toast-container');
        if (!container) return; // Should be in every page

        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `
            <div class="toast-content">
                <span style="font-weight: 600;">${type.toUpperCase()}</span>
                <p>${message}</p>
            </div>
        `;

        container.appendChild(toast);

        // Auto remove after 3s
        setTimeout(() => {
            toast.style.opacity = '0';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    // Helper to populate tables or grids
    static clearElement(elementId) {
        const el = document.getElementById(elementId);
        if (el) el.innerHTML = '';
    }
}

// Global Event Listeners for closing modals
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        document.querySelectorAll('.modal-overlay.open').forEach(modal => {
            modal.classList.remove('open');
        });
    }
});

document.addEventListener('click', (e) => {
    if (e.target.classList.contains('modal-overlay')) {
        e.target.classList.remove('open');
    }
});
