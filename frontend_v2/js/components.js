// Toast notification
export function showToast(message, type = 'success') {
    const toastContainer = document.getElementById('toast-container');
    const toastEl = document.createElement('div');
    toastEl.className = `toast align-items-center text-white bg-${type === 'success' ? 'success' : 'danger'} border-0`;
    toastEl.setAttribute('role', 'alert');
    toastEl.setAttribute('aria-live', 'assertive');
    toastEl.setAttribute('aria-atomic', 'true');
    toastEl.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">${message}</div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    toastContainer.appendChild(toastEl);
    const toast = new bootstrap.Toast(toastEl);
    toast.show();
    toastEl.addEventListener('hidden.bs.toast', () => toastEl.remove());
}

// Modal helper
export function showModal(title, bodyContent, onConfirm = null, confirmText = 'Save', cancelText = 'Cancel') {
    const modalContainer = document.getElementById('modal-container');
    const modalId = 'dynamicModal' + Date.now();
    const modalHtml = `
        <div class="modal fade" id="${modalId}" tabindex="-1">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">${title}</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">${bodyContent}</div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">${cancelText}</button>
                        ${onConfirm ? `<button type="button" class="btn btn-success" id="modalConfirmBtn">${confirmText}</button>` : ''}
                    </div>
                </div>
            </div>
        </div>
    `;
    modalContainer.innerHTML = modalHtml;
    const modalEl = document.getElementById(modalId);
    const modal = new bootstrap.Modal(modalEl);
    if (onConfirm) {
        document.getElementById('modalConfirmBtn').addEventListener('click', () => {
            onConfirm();
            modal.hide();
        });
    }
    modal.show();
    modalEl.addEventListener('hidden.bs.modal', () => modalEl.remove());
}

// Confirmation dialog
export function confirmDialog(message, onYes) {
    showModal('Confirm', `<p>${message}</p>`, onYes, 'Yes', 'No');
}

// Spinner
export function showSpinner(container) {
    container.innerHTML = '<div class="text-center"><i class="fas fa-spinner fa-spin fa-2x text-success"></i></div>';
}