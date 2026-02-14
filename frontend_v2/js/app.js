import * as api from './api.js';
import * as auth from './auth.js';
import { showToast, showModal, confirmDialog, showSpinner } from './components.js';

// State
let currentUser = null;
let currentRole = null;

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    checkAuth();
    setupEventListeners();
    handleRouting();
});

function checkAuth() {
    if (auth.isAuthenticated()) {
        currentRole = auth.getUserRole();
        currentUser = auth.getUserData();
        showSidebar(true);
        loadViewBasedOnRole();
    } else {
        showSidebar(false);
        loadPublicHome();
    }
}

function showSidebar(show) {
    const sidebar = document.getElementById('sidebar');
    const content = document.getElementById('content-area');
    sidebar.style.display = show ? 'block' : 'none';
    if (show) {
        content.classList.remove('col-md-12');
        content.classList.add('col-md-9', 'col-lg-10');
        renderSidebarMenu();
    } else {
        content.classList.remove('col-md-9', 'col-lg-10');
        content.classList.add('col-md-12');
    }
}

function renderSidebarMenu() {
    const menu = document.getElementById('sidebar-menu');
    if (currentRole === 'CHC_ADMIN') {
        menu.innerHTML = `
            <a class="list-group-item list-group-item-action" data-view="dashboard"><i class="fas fa-tachometer-alt me-2"></i>Dashboard</a>
            <a class="list-group-item list-group-item-action" data-view="machines"><i class="fas fa-tractor me-2"></i>Machines</a>
            <a class="list-group-item list-group-item-action" data-view="bookings"><i class="fas fa-calendar-check me-2"></i>Bookings</a>
            <a class="list-group-item list-group-item-action" data-view="usage"><i class="fas fa-chart-line me-2"></i>Usage Records</a>
            <a class="list-group-item list-group-item-action" data-view="profile"><i class="fas fa-user me-2"></i>Profile</a>
        `;
    } else if (currentRole === 'GOVT_ADMIN') {
        menu.innerHTML = `
            <a class="list-group-item list-group-item-action" data-view="govt-dashboard"><i class="fas fa-tachometer-alt me-2"></i>Dashboard</a>
            <a class="list-group-item list-group-item-action" data-view="chcs"><i class="fas fa-building me-2"></i>CHCs</a>
            <a class="list-group-item list-group-item-action" data-view="all-machines"><i class="fas fa-tractor me-2"></i>Machines</a>
            <a class="list-group-item list-group-item-action" data-view="all-bookings"><i class="fas fa-calendar-check me-2"></i>Bookings</a>
            <a class="list-group-item list-group-item-action" data-view="analytics"><i class="fas fa-chart-pie me-2"></i>Analytics</a>
        `;
    }
    // Add click handlers
    document.querySelectorAll('#sidebar-menu .list-group-item').forEach(item => {
        item.addEventListener('click', (e) => {
            document.querySelectorAll('#sidebar-menu .list-group-item').forEach(i => i.classList.remove('active'));
            e.target.classList.add('active');
            const view = e.target.dataset.view;
            loadView(view);
        });
    });
}

function setupEventListeners() {
    // Navbar links (login/register/logout)
    document.getElementById('home-link').addEventListener('click', (e) => {
        e.preventDefault();
        window.location.hash = '#';
        checkAuth();
    });
    window.addEventListener('hashchange', handleRouting);
}

function handleRouting() {
    const hash = window.location.hash.slice(1) || 'home';
    if (!auth.isAuthenticated()) {
        if (hash === 'login') showLoginForm();
        else if (hash === 'register') showRegisterForm();
        else if (hash === 'booking-status') showBookingStatusForm();
        else if (hash === 'create-booking') showPublicBookingForm();
        else loadPublicHome();
    } else {
        // Logged in, load view based on hash or default dashboard
        if (hash.startsWith('view=')) {
            const view = hash.split('=')[1];
            loadView(view);
        } else {
            loadViewBasedOnRole();
        }
    }
}

function loadViewBasedOnRole() {
    if (currentRole === 'CHC_ADMIN') loadView('dashboard');
    else if (currentRole === 'GOVT_ADMIN') loadView('govt-dashboard');
}

async function loadView(view) {
    const content = document.getElementById('content-area');
    showSpinner(content);
    try {
        switch (view) {
            case 'dashboard':
                await renderCHCDashboard(content);
                break;
            case 'machines':
                await renderMachines(content);
                break;
            case 'bookings':
                await renderBookings(content);
                break;
            case 'usage':
                await renderUsage(content);
                break;
            case 'profile':
                renderProfile(content);
                break;
            case 'govt-dashboard':
                await renderGovtDashboard(content);
                break;
            case 'chcs':
                await renderCHCs(content);
                break;
            case 'all-machines':
                await renderAllMachines(content);
                break;
            case 'all-bookings':
                await renderAllBookings(content);
                break;
            case 'analytics':
                await renderAnalytics(content);
                break;
            default:
                loadPublicHome();
        }
    } catch (error) {
        content.innerHTML = `<div class="alert alert-danger">Error loading view: ${error.message}</div>`;
    }
}

// ---------- Public Views ----------
function loadPublicHome() {
    const content = document.getElementById('content-area');
    content.innerHTML = `
        <div class="jumbotron bg-light p-5 rounded">
            <h1 class="display-4">Welcome to Crop Residue Management System</h1>
            <p class="lead">Find Custom Hiring Centers, check machine availability, and book equipment easily.</p>
            <hr class="my-4">
            <div class="row">
                <div class="col-md-4">
                    <div class="card">
                        <div class="card-body">
                            <h5 class="card-title"><i class="fas fa-search text-success"></i> Search CHCs</h5>
                            <p class="card-text">Find CHCs by pincode, district, or state.</p>
                            <button class="btn btn-outline-success" onclick="window.location.hash='#search-chc'">Search</button>
                        </div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card">
                        <div class="card-body">
                            <h5 class="card-title"><i class="fas fa-calendar-plus text-success"></i> Book a Machine</h5>
                            <p class="card-text">Create a new booking request.</p>
                            <button class="btn btn-outline-success" onclick="window.location.hash='#create-booking'">Book Now</button>
                        </div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card">
                        <div class="card-body">
                            <h5 class="card-title"><i class="fas fa-info-circle text-success"></i> Check Booking Status</h5>
                            <p class="card-text">Check the status of your existing booking.</p>
                            <button class="btn btn-outline-success" onclick="window.location.hash='#booking-status'">Check Status</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
    renderNavbarPublic();
}

function renderNavbarPublic() {
    const nav = document.getElementById('nav-links');
    nav.innerHTML = `
        <li class="nav-item"><a class="nav-link" href="#login">Login</a></li>
        <li class="nav-item"><a class="nav-link" href="#register">Register</a></li>
    `;
}

function showLoginForm() {
    const content = document.getElementById('content-area');
    content.innerHTML = `
        <div class="row justify-content-center">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header bg-success text-white">Login</div>
                    <div class="card-body">
                        <form id="login-form">
                            <div class="mb-3">
                                <label for="username" class="form-label">Username</label>
                                <input type="text" class="form-control" id="username" required>
                            </div>
                            <div class="mb-3">
                                <label for="password" class="form-label">Password</label>
                                <input type="password" class="form-control" id="password" required>
                            </div>
                            <button type="submit" class="btn btn-success w-100">Login</button>
                        </form>
                        <p class="mt-3 text-center">Don't have an account? <a href="#register">Register</a></p>
                    </div>
                </div>
            </div>
        </div>
    `;
    document.getElementById('login-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;
        const result = await auth.handleLogin(username, password);
        if (result.success) {
            showToast('Login successful');
            currentRole = result.role;
            currentUser = auth.getUserData();
            showSidebar(true);
            loadViewBasedOnRole();
        } else {
            showToast(result.error, 'error');
        }
    });
    renderNavbarPublic();
}

function showRegisterForm() {
    const content = document.getElementById('content-area');
    content.innerHTML = `
        <div class="row justify-content-center">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header bg-success text-white">Register</div>
                    <div class="card-body">
                        <form id="register-form">
                            <div class="mb-3">
                                <label for="reg-username" class="form-label">Username</label>
                                <input type="text" class="form-control" id="reg-username" required>
                            </div>
                            <div class="mb-3">
                                <label for="reg-email" class="form-label">Email</label>
                                <input type="email" class="form-control" id="reg-email" required>
                            </div>
                            <div class="mb-3">
                                <label for="reg-firstname" class="form-label">First Name</label>
                                <input type="text" class="form-control" id="reg-firstname" required>
                            </div>
                            <div class="mb-3">
                                <label for="reg-lastname" class="form-label">Last Name</label>
                                <input type="text" class="form-control" id="reg-lastname">
                            </div>
                            <div class="mb-3">
                                <label for="reg-phone" class="form-label">Phone No</label>
                                <input type="text" class="form-control" id="reg-phone">
                            </div>
                            <div class="mb-3">
                                <label for="reg-password" class="form-label">Password</label>
                                <input type="password" class="form-control" id="reg-password" required>
                            </div>
                            <button type="submit" class="btn btn-success w-100">Register</button>
                        </form>
                        <p class="mt-3 text-center">Already have an account? <a href="#login">Login</a></p>
                    </div>
                </div>
            </div>
        </div>
    `;
    document.getElementById('register-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const userData = {
            username: document.getElementById('reg-username').value,
            email: document.getElementById('reg-email').value,
            first_name: document.getElementById('reg-firstname').value,
            last_name: document.getElementById('reg-lastname').value,
            phone_no: document.getElementById('reg-phone').value,
            password: document.getElementById('reg-password').value
        };
        const result = await auth.handleRegister(userData);
        if (result.success) {
            showToast('Registration successful. Please login.');
            window.location.hash = '#login';
        } else {
            showToast(result.error, 'error');
        }
    });
    renderNavbarPublic();
}

function showBookingStatusForm() {
    const content = document.getElementById('content-area');
    content.innerHTML = `
        <div class="row justify-content-center">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header bg-success text-white">Check Booking Status</div>
                    <div class="card-body">
                        <form id="status-form">
                            <div class="mb-3">
                                <label for="booking-id" class="form-label">Booking ID</label>
                                <input type="number" class="form-control" id="booking-id" required>
                            </div>
                            <button type="submit" class="btn btn-success w-100">Check Status</button>
                        </form>
                        <div id="status-result" class="mt-3"></div>
                    </div>
                </div>
            </div>
        </div>
    `;
    document.getElementById('status-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const id = document.getElementById('booking-id').value;
        try {
            const booking = await api.publicGetBookingStatus(id);
            document.getElementById('status-result').innerHTML = `
                <div class="alert alert-info">
                    <strong>Status:</strong> ${booking.status}<br>
                    <strong>Farmer:</strong> ${booking.farmer_name}<br>
                    <strong>Machine:</strong> ${booking.machine_details.machine_name}<br>
                    <strong>Dates:</strong> ${booking.start_date} to ${booking.end_date}
                </div>
            `;
        } catch (error) {
            showToast(error.message, 'error');
        }
    });
    renderNavbarPublic();
}

function showPublicBookingForm() {
    // First show machine selection (simplified: list machines)
    const content = document.getElementById('content-area');
    content.innerHTML = `
        <div class="card">
            <div class="card-header bg-success text-white">Create Booking</div>
            <div class="card-body">
                <div id="machine-select-step">
                    <h5>Select Machine</h5>
                    <div class="mb-3">
                        <label for="chc-filter" class="form-label">Filter by CHC (optional)</label>
                        <input type="text" class="form-control" id="chc-filter" placeholder="CHC ID">
                    </div>
                    <div id="machine-list"></div>
                </div>
                <div id="booking-form-step" style="display:none;"></div>
            </div>
        </div>
    `;
    loadPublicMachines();
}

async function loadPublicMachines() {
    const container = document.getElementById('machine-list');
    showSpinner(container);
    try {
        const machines = await api.publicListMachines({});
        let html = '<div class="list-group">';
        machines.forEach(m => {
            html += `
                <a href="#" class="list-group-item list-group-item-action machine-item" data-id="${m.id}">
                    <div class="d-flex w-100 justify-content-between">
                        <h5 class="mb-1">${m.machine_name}</h5>
                        <small><span class="badge bg-${m.status === 'Idle' ? 'success' : 'primary'}">${m.status}</span></small>
                    </div>
                    <p class="mb-1">${m.machine_type} - ${m.chc_details.name}</p>
                    ${m.status !== 'Idle' ? '<small class="text-muted">Available for future booking</small>' : ''}
                </a>
            `;
        });
        html += '</div>';
        container.innerHTML = html;
        document.querySelectorAll('.machine-item').forEach(el => {
            el.addEventListener('click', (e) => {
                e.preventDefault();
                const machineId = e.currentTarget.dataset.id;
                showBookingFormForMachine(machineId);
            });
        });
    } catch (error) {
        container.innerHTML = `<div class="alert alert-danger">${error.message}</div>`;
    }
}

function showBookingFormForMachine(machineId) {
    document.getElementById('machine-select-step').style.display = 'none';
    const formStep = document.getElementById('booking-form-step');
    formStep.style.display = 'block';
    formStep.innerHTML = `
        <h5>Booking Details</h5>
        <form id="booking-detail-form">
            <input type="hidden" id="machine-id" value="${machineId}">
            <div class="mb-3">
                <label for="start-date" class="form-label">Start Date</label>
                <input type="date" class="form-control" id="start-date" required>
            </div>
            <div class="mb-3">
                <label for="end-date" class="form-label">End Date</label>
                <input type="date" class="form-control" id="end-date" required>
            </div>
            <div class="mb-3">
                <label for="farmer-name" class="form-label">Farmer Name</label>
                <input type="text" class="form-control" id="farmer-name" required>
            </div>
            <div class="mb-3">
                <label for="farmer-contact" class="form-label">Contact No</label>
                <input type="text" class="form-control" id="farmer-contact" required>
            </div>
            <div class="mb-3">
                <label for="farmer-email" class="form-label">Email</label>
                <input type="email" class="form-control" id="farmer-email" required>
            </div>
            <div class="mb-3">
                <label for="farmer-aadhar" class="form-label">Aadhar Number</label>
                <input type="text" class="form-control" id="farmer-aadhar" required>
            </div>
            <div class="mb-3">
                <label for="purpose" class="form-label">Purpose (optional)</label>
                <textarea class="form-control" id="purpose"></textarea>
            </div>
            <div class="mb-3">
                <label for="field-area" class="form-label">Field Area (acres)</label>
                <input type="number" step="0.01" class="form-control" id="field-area">
            </div>
            <button type="submit" class="btn btn-success">Submit Booking</button>
            <button type="button" class="btn btn-secondary" onclick="window.location.hash='#create-booking'">Back</button>
        </form>
    `;
    document.getElementById('booking-detail-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const data = {
            machine: parseInt(document.getElementById('machine-id').value),
            start_date: document.getElementById('start-date').value,
            end_date: document.getElementById('end-date').value,
            farmer_name: document.getElementById('farmer-name').value,
            farmer_contact: document.getElementById('farmer-contact').value,
            farmer_email: document.getElementById('farmer-email').value,
            farmer_aadhar: document.getElementById('farmer-aadhar').value,
            purpose: document.getElementById('purpose').value,
            field_area: parseFloat(document.getElementById('field-area').value) || null
        };
        try {
            const result = await api.publicCreateBooking(data);
            showToast(`Booking created successfully! ID: ${result.id}`);
            window.location.hash = '#booking-status';
        } catch (error) {
            showToast(error.message, 'error');
        }
    });
}

// ---------- CHC Admin Views ----------
async function renderCHCDashboard(container) {
    try {
        const data = await api.getCHCDashboard();
        container.innerHTML = `
            <h2>CHC Dashboard</h2>
            <div class="row mt-4">
                <div class="col-md-3">
                    <div class="card text-white bg-primary mb-3">
                        <div class="card-body">
                            <h5 class="card-title">Total Machines</h5>
                            <p class="card-text display-6">${data.total_machines}</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card text-white bg-success mb-3">
                        <div class="card-body">
                            <h5 class="card-title">Available</h5>
                            <p class="card-text display-6">${data.machines_available}</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card text-white bg-warning mb-3">
                        <div class="card-body">
                            <h5 class="card-title">In Use</h5>
                            <p class="card-text display-6">${data.machines_in_use}</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card text-white bg-danger mb-3">
                        <div class="card-body">
                            <h5 class="card-title">Pending Bookings</h5>
                            <p class="card-text display-6">${data.pending_bookings}</p>
                        </div>
                    </div>
                </div>
            </div>
            <div class="row mt-3">
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">Recent Bookings</div>
                        <div class="card-body" id="recent-bookings"></div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">Machine Status</div>
                        <div class="card-body" id="machine-status"></div>
                    </div>
                </div>
            </div>
        `;
        // Load recent bookings
        const bookings = await api.listBookings({ ordering: '-booking_date', limit: 5 });
        const bookingsHtml = bookings.length ? bookings.map(b => `
            <div class="border-bottom pb-2 mb-2">
                <strong>${b.farmer_name}</strong> - ${b.machine_details.machine_name}<br>
                <span class="badge bg-${b.status === 'Pending' ? 'warning' : b.status === 'Approved' ? 'info' : b.status === 'Active' ? 'primary' : 'secondary'}">${b.status}</span>
            </div>
        `).join('') : '<p>No recent bookings</p>';
        document.getElementById('recent-bookings').innerHTML = bookingsHtml;

        // Machine status breakdown
        const machines = await api.listMachines();
        const statusCounts = machines.reduce((acc, m) => {
            acc[m.status] = (acc[m.status] || 0) + 1;
            return acc;
        }, {});
        const statusHtml = Object.entries(statusCounts).map(([status, count]) => `
            <div class="d-flex justify-content-between">
                <span>${status}</span>
                <span class="badge bg-secondary">${count}</span>
            </div>
        `).join('');
        document.getElementById('machine-status').innerHTML = statusHtml || '<p>No machines</p>';
    } catch (error) {
        container.innerHTML = `<div class="alert alert-danger">${error.message}</div>`;
    }
}

async function renderMachines(container) {
    container.innerHTML = `
        <h2>Machines</h2>
        <button class="btn btn-success mb-3" id="add-machine-btn"><i class="fas fa-plus"></i> Add Machine</button>
        <div id="machines-table-container"></div>
    `;
    document.getElementById('add-machine-btn').addEventListener('click', () => showMachineModal());
    await loadMachinesTable();
}

async function loadMachinesTable() {
    const container = document.getElementById('machines-table-container');
    showSpinner(container);
    try {
        const machines = await api.listMachines();
        let html = `
            <table class="table table-striped">
                <thead>
                    <tr>
                        <th>Code</th><th>Name</th><th>Type</th><th>Status</th><th>Actions</th>
                    </tr>
                </thead>
                <tbody>
        `;
        machines.forEach(m => {
            html += `
                <tr>
                    <td>${m.machine_code}</td>
                    <td>${m.machine_name}</td>
                    <td>${m.machine_type}</td>
                    <td><span class="badge bg-${m.status === 'Idle' ? 'success' : m.status === 'In Use' ? 'primary' : 'warning'}">${m.status}</span></td>
                    <td>
                        <button class="btn btn-sm btn-outline-primary edit-machine" data-id="${m.id}"><i class="fas fa-edit"></i></button>
                        <button class="btn btn-sm btn-outline-danger delete-machine" data-id="${m.id}"><i class="fas fa-trash"></i></button>
                    </td>
                </tr>
            `;
        });
        html += '</tbody></table>';
        container.innerHTML = html;

        document.querySelectorAll('.edit-machine').forEach(btn => {
            btn.addEventListener('click', () => showMachineModal(btn.dataset.id));
        });
        document.querySelectorAll('.delete-machine').forEach(btn => {
            btn.addEventListener('click', () => deleteMachine(btn.dataset.id));
        });
    } catch (error) {
        container.innerHTML = `<div class="alert alert-danger">${error.message}</div>`;
    }
}

function showMachineModal(machineId = null) {
    const title = machineId ? 'Edit Machine' : 'Add Machine';
    let formHtml = `
        <form id="machine-form">
            <div class="mb-3">
                <label for="machine-name" class="form-label">Machine Name</label>
                <input type="text" class="form-control" id="machine-name" required>
            </div>
            <div class="mb-3">
                <label for="machine-type" class="form-label">Machine Type</label>
                <select class="form-control" id="machine-type" required>
                    <option value="">Select Type</option>
                    <option value="Happy Seeder">Happy Seeder</option>
                    <option value="Super Seeder">Super Seeder</option>
                    <option value="Smart Seeder">Smart Seeder</option>
                    <!-- Add all types from backend -->
                </select>
            </div>
            <div class="mb-3">
                <label for="purchase-year" class="form-label">Purchase Year</label>
                <input type="number" class="form-control" id="purchase-year" required>
            </div>
            <div class="mb-3">
                <label for="funding-source" class="form-label">Funding Source</label>
                <input type="text" class="form-control" id="funding-source">
            </div>
            <div class="mb-3">
                <label for="status" class="form-label">Status</label>
                <select class="form-control" id="status" required>
                    <option value="Idle">Idle</option>
                    <option value="In Use">In Use</option>
                    <option value="Maintenance">Maintenance</option>
                    <option value="Out of Service">Out of Service</option>
                </select>
            </div>
        </form>
    `;

    showModal(title, formHtml, async () => {
        const form = document.getElementById('machine-form');
        const data = {
            machine_name: form['machine-name'].value,
            machine_type: form['machine-type'].value,
            purchase_year: parseInt(form['purchase-year'].value),
            funding_source: form['funding-source'].value,
            status: form['status'].value,
        };
        try {
            if (machineId) {
                await api.updateMachine(machineId, data);
                showToast('Machine updated');
            } else {
                await api.createMachine(data);
                showToast('Machine created');
            }
            loadMachinesTable();
        } catch (error) {
            showToast(error.message, 'error');
        }
    }, machineId ? 'Update' : 'Create');

    // If editing, fetch and populate
    if (machineId) {
        api.getMachine(machineId).then(m => {
            document.getElementById('machine-name').value = m.machine_name;
            document.getElementById('machine-type').value = m.machine_type;
            document.getElementById('purchase-year').value = m.purchase_year;
            document.getElementById('funding-source').value = m.funding_source || '';
            document.getElementById('status').value = m.status;
        });
    }
}

async function deleteMachine(id) {
    confirmDialog('Are you sure you want to delete this machine?', async () => {
        try {
            await api.deleteMachine(id);
            showToast('Machine deleted');
            loadMachinesTable();
        } catch (error) {
            showToast(error.message, 'error');
        }
    });
}

async function renderBookings(container) {
    container.innerHTML = `
        <h2>Bookings</h2>
        <div class="row mb-3">
            <div class="col-md-4">
                <select class="form-control" id="status-filter">
                    <option value="">All Status</option>
                    <option value="Pending">Pending</option>
                    <option value="Approved">Approved</option>
                    <option value="Active">Active</option>
                    <option value="Completed">Completed</option>
                    <option value="Rejected">Rejected</option>
                    <option value="Cancelled">Cancelled</option>
                </select>
            </div>
        </div>
        <div id="bookings-table-container"></div>
    `;
    document.getElementById('status-filter').addEventListener('change', loadBookingsTable);
    await loadBookingsTable();
}

async function loadBookingsTable() {
    const container = document.getElementById('bookings-table-container');
    showSpinner(container);
    try {
        const status = document.getElementById('status-filter').value;
        const params = status ? { status } : {};
        const bookings = await api.listBookings(params);
        let html = `
            <table class="table table-striped">
                <thead>
                    <tr>
                        <th>ID</th><th>Farmer</th><th>Machine</th><th>Dates</th><th>Status</th><th>Actions</th>
                    </tr>
                </thead>
                <tbody>
        `;
        bookings.forEach(b => {
            html += `
                <tr>
                    <td>${b.id}</td>
                    <td>${b.farmer_name}</td>
                    <td>${b.machine_details.machine_name}</td>
                    <td>${b.start_date} to ${b.end_date}</td>
                    <td><span class="badge bg-${b.status === 'Pending' ? 'warning' : b.status === 'Approved' ? 'info' : b.status === 'Active' ? 'primary' : b.status === 'Completed' ? 'success' : 'secondary'}">${b.status}</span></td>
                    <td>
                        ${b.status === 'Pending' ? `<button class="btn btn-sm btn-success approve-booking" data-id="${b.id}">Approve</button>
                        <button class="btn btn-sm btn-danger reject-booking" data-id="${b.id}">Reject</button>` : ''}
                        ${b.status === 'Approved' ? `<button class="btn btn-sm btn-primary handover-booking" data-id="${b.id}">Handover</button>` : ''}
                        ${b.status === 'Active' ? `<button class="btn btn-sm btn-success complete-booking" data-id="${b.id}">Complete</button>` : ''}
                        ${b.status === 'Pending' || b.status === 'Approved' || b.status === 'Active' ? `<button class="btn btn-sm btn-secondary cancel-booking" data-id="${b.id}">Cancel</button>` : ''}
                    </td>
                </tr>
            `;
        });
        html += '</tbody></table>';
        container.innerHTML = html;

        // Attach event listeners
        document.querySelectorAll('.approve-booking').forEach(btn => {
            btn.addEventListener('click', () => bookingAction(btn.dataset.id, 'approve'));
        });
        document.querySelectorAll('.reject-booking').forEach(btn => {
            btn.addEventListener('click', () => bookingAction(btn.dataset.id, 'reject', prompt('Reason for rejection:')));
        });
        document.querySelectorAll('.handover-booking').forEach(btn => {
            btn.addEventListener('click', () => bookingAction(btn.dataset.id, 'handover'));
        });
        document.querySelectorAll('.complete-booking').forEach(btn => {
            btn.addEventListener('click', () => bookingAction(btn.dataset.id, 'complete'));
        });
        document.querySelectorAll('.cancel-booking').forEach(btn => {
            btn.addEventListener('click', () => bookingAction(btn.dataset.id, 'cancel', prompt('Reason for cancellation:')));
        });
    } catch (error) {
        container.innerHTML = `<div class="alert alert-danger">${error.message}</div>`;
    }
}

async function bookingAction(id, action, notes = '') {
    try {
        const result = await api.bookingAction(id, action, notes);
        showToast(`Booking ${action}d successfully`);
        loadBookingsTable();
    } catch (error) {
        showToast(error.message, 'error');
    }
}

async function renderUsage(container) {
    container.innerHTML = `
        <h2>Usage Records</h2>
        <button class="btn btn-success mb-3" id="add-usage-btn"><i class="fas fa-plus"></i> Record Usage</button>
        <div id="usage-table-container"></div>
    `;
    document.getElementById('add-usage-btn').addEventListener('click', showUsageModal);
    await loadUsageTable();
}

async function loadUsageTable() {
    const container = document.getElementById('usage-table-container');
    showSpinner(container);
    try {
        const usage = await api.listUsage();
        let html = `
            <table class="table table-striped">
                <thead>
                    <tr>
                        <th>Date</th><th>Machine</th><th>Farmer</th><th>Hours</th><th>Area</th>
                    </tr>
                </thead>
                <tbody>
        `;
        usage.forEach(u => {
            html += `
                <tr>
                    <td>${u.usage_date}</td>
                    <td>${u.machine.machine_name}</td>
                    <td>${u.farmer_name}</td>
                    <td>${u.total_hours_used || 'N/A'}</td>
                    <td>${u.area_covered || 'N/A'}</td>
                </tr>
            `;
        });
        html += '</tbody></table>';
        container.innerHTML = html;
    } catch (error) {
        container.innerHTML = `<div class="alert alert-danger">${error.message}</div>`;
    }
}

function showUsageModal() {
    const formHtml = `
        <form id="usage-form">
            <div class="mb-3">
                <label for="usage-machine" class="form-label">Machine</label>
                <select class="form-control" id="usage-machine" required>
                    <option value="">Select Machine</option>
                </select>
            </div>
            <div class="mb-3">
                <label for="usage-farmer" class="form-label">Farmer Name</label>
                <input type="text" class="form-control" id="usage-farmer" required>
            </div>
            <div class="mb-3">
                <label for="usage-contact" class="form-label">Contact</label>
                <input type="text" class="form-control" id="usage-contact" required>
            </div>
            <div class="mb-3">
                <label for="usage-aadhar" class="form-label">Aadhar</label>
                <input type="text" class="form-control" id="usage-aadhar">
            </div>
            <div class="mb-3">
                <label for="usage-date" class="form-label">Usage Date</label>
                <input type="date" class="form-control" id="usage-date" required>
            </div>
            <div class="row">
                <div class="col">
                    <label for="start-time" class="form-label">Start Time</label>
                    <input type="time" class="form-control" id="start-time" required>
                </div>
                <div class="col">
                    <label for="end-time" class="form-label">End Time</label>
                    <input type="time" class="form-control" id="end-time" required>
                </div>
            </div>
            <div class="mb-3">
                <label for="area" class="form-label">Area Covered (acres)</label>
                <input type="number" step="0.01" class="form-control" id="area">
            </div>
            <div class="mb-3">
                <label for="residue" class="form-label">Residue Managed (tons)</label>
                <input type="number" step="0.01" class="form-control" id="residue">
            </div>
        </form>
    `;
    showModal('Record Usage', formHtml, async () => {
        const form = document.getElementById('usage-form');
        const data = {
            machine: parseInt(form['usage-machine'].value),
            farmer_name: form['usage-farmer'].value,
            farmer_contact: form['usage-contact'].value,
            farmer_aadhar: form['usage-aadhar'].value,
            usage_date: form['usage-date'].value,
            start_time: form['start-time'].value,
            end_time: form['end-time'].value,
            area_covered: parseFloat(form['area'].value) || null,
            residue_managed: parseFloat(form['residue'].value) || null,
        };
        try {
            await api.createUsage(data);
            showToast('Usage recorded');
            loadUsageTable();
        } catch (error) {
            showToast(error.message, 'error');
        }
    });

    // Populate machine dropdown
    api.listMachines().then(machines => {
        const select = document.getElementById('usage-machine');
        machines.forEach(m => {
            select.innerHTML += `<option value="${m.id}">${m.machine_name} (${m.machine_code})</option>`;
        });
    });
}

function renderProfile(container) {
    const user = auth.getUserData();
    container.innerHTML = `
        <h2>Profile</h2>
        <div class="card">
            <div class="card-body">
                <p><strong>Username:</strong> ${user.username}</p>
                <p><strong>Email:</strong> ${user.email}</p>
                <p><strong>First Name:</strong> ${user.first_name}</p>
                <p><strong>Last Name:</strong> ${user.last_name}</p>
                <p><strong>Phone:</strong> ${user.phone_no || 'N/A'}</p>
                <p><strong>Role:</strong> ${user.role}</p>
                <p><strong>CHC:</strong> ${user.chc ? user.chc.chc_name : 'N/A'}</p>
                <button class="btn btn-danger" id="logout-btn">Logout</button>
            </div>
        </div>
    `;
    document.getElementById('logout-btn').addEventListener('click', auth.logout);
}

// ---------- Govt Admin Views ----------
async function renderGovtDashboard(container) {
    try {
        const data = await api.getGovtDashboard();
        container.innerHTML = `
            <h2>Government Dashboard</h2>
            <div class="row mt-4">
                <div class="col-md-4">
                    <div class="card text-white bg-primary mb-3">
                        <div class="card-body">
                            <h5 class="card-title">Total CHCs</h5>
                            <p class="card-text display-6">${data.total_chcs}</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card text-white bg-success mb-3">
                        <div class="card-body">
                            <h5 class="card-title">Total Machines</h5>
                            <p class="card-text display-6">${data.total_machines}</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card text-white bg-info mb-3">
                        <div class="card-body">
                            <h5 class="card-title">Total Bookings</h5>
                            <p class="card-text display-6">${data.total_bookings}</p>
                        </div>
                    </div>
                </div>
            </div>
            <div class="row">
                <div class="col-md-4">
                    <div class="card">
                        <div class="card-body">
                            <h5 class="card-title">Total Usage Hours</h5>
                            <p class="card-text display-6">${data.total_usage_hours}</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card">
                        <div class="card-body">
                            <h5 class="card-title">Residue Managed (tons)</h5>
                            <p class="card-text display-6">${data.total_residue_managed}</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card">
                        <div class="card-body">
                            <h5 class="card-title">Area Covered (acres)</h5>
                            <p class="card-text display-6">${data.total_area_covered}</p>
                        </div>
                    </div>
                </div>
            </div>
        `;
    } catch (error) {
        container.innerHTML = `<div class="alert alert-danger">${error.message}</div>`;
    }
}

async function renderCHCs(container) {
    container.innerHTML = `
        <h2>CHCs</h2>
        <button class="btn btn-success mb-3" id="add-chc-btn"><i class="fas fa-plus"></i> Add CHC</button>
        <div id="chcs-table-container"></div>
    `;
    document.getElementById('add-chc-btn').addEventListener('click', () => showCHCModal());
    await loadCHCsTable();
}

async function loadCHCsTable() {
    const container = document.getElementById('chcs-table-container');
    showSpinner(container);
    try {
        const chcs = await api.listCHCs();
        let html = `
            <table class="table table-striped">
                <thead>
                    <tr>
                        <th>Name</th><th>District</th><th>State</th><th>Contact</th><th>Machines</th><th>Actions</th>
                    </tr>
                </thead>
                <tbody>
        `;
        chcs.forEach(c => {
            html += `
                <tr>
                    <td>${c.chc_name}</td>
                    <td>${c.district}</td>
                    <td>${c.state}</td>
                    <td>${c.contact_number}</td>
                    <td>${c.total_machines}</td>
                    <td>
                        <button class="btn btn-sm btn-outline-primary edit-chc" data-id="${c.id}"><i class="fas fa-edit"></i></button>
                        <button class="btn btn-sm btn-outline-danger delete-chc" data-id="${c.id}"><i class="fas fa-trash"></i></button>
                    </td>
                </tr>
            `;
        });
        html += '</tbody></table>';
        container.innerHTML = html;

        document.querySelectorAll('.edit-chc').forEach(btn => {
            btn.addEventListener('click', () => showCHCModal(btn.dataset.id));
        });
        document.querySelectorAll('.delete-chc').forEach(btn => {
            btn.addEventListener('click', () => deleteCHC(btn.dataset.id));
        });
    } catch (error) {
        container.innerHTML = `<div class="alert alert-danger">${error.message}</div>`;
    }
}

function showCHCModal(chcId = null) {
    const title = chcId ? 'Edit CHC' : 'Add CHC';
    const formHtml = `
        <form id="chc-form">
            <div class="mb-3">
                <label for="chc-name" class="form-label">CHC Name</label>
                <input type="text" class="form-control" id="chc-name" required>
            </div>
            <div class="mb-3">
                <label for="state" class="form-label">State</label>
                <input type="text" class="form-control" id="state" required>
            </div>
            <div class="mb-3">
                <label for="district" class="form-label">District</label>
                <input type="text" class="form-control" id="district" required>
            </div>
            <div class="mb-3">
                <label for="location" class="form-label">Location</label>
                <input type="text" class="form-control" id="location" required>
            </div>
            <div class="mb-3">
                <label for="pincode" class="form-label">Pincode</label>
                <input type="text" class="form-control" id="pincode" required>
            </div>
            <div class="mb-3">
                <label for="admin-name" class="form-label">Admin Name</label>
                <input type="text" class="form-control" id="admin-name" required>
            </div>
            <div class="mb-3">
                <label for="contact-number" class="form-label">Contact Number</label>
                <input type="text" class="form-control" id="contact-number" required>
            </div>
            <div class="mb-3">
                <label for="chc-email" class="form-label">Email</label>
                <input type="email" class="form-control" id="chc-email" required>
            </div>
        </form>
    `;
    showModal(title, formHtml, async () => {
        const form = document.getElementById('chc-form');
        const data = {
            chc_name: form['chc-name'].value,
            state: form['state'].value,
            district: form['district'].value,
            location: form['location'].value,
            pincode: form['pincode'].value,
            admin_name: form['admin-name'].value,
            contact_number: form['contact-number'].value,
            email: form['chc-email'].value,
        };
        try {
            if (chcId) {
                await api.updateCHC(chcId, data);
                showToast('CHC updated');
            } else {
                await api.createCHC(data);
                showToast('CHC created');
            }
            loadCHCsTable();
        } catch (error) {
            showToast(error.message, 'error');
        }
    }, chcId ? 'Update' : 'Create');

    if (chcId) {
        api.getCHC(chcId).then(c => {
            document.getElementById('chc-name').value = c.chc_name;
            document.getElementById('state').value = c.state;
            document.getElementById('district').value = c.district;
            document.getElementById('location').value = c.location;
            document.getElementById('pincode').value = c.pincode;
            document.getElementById('admin-name').value = c.admin_name;
            document.getElementById('contact-number').value = c.contact_number;
            document.getElementById('chc-email').value = c.email;
        });
    }
}

async function deleteCHC(id) {
    confirmDialog('Are you sure you want to delete this CHC?', async () => {
        try {
            await api.deleteCHC(id);
            showToast('CHC deleted');
            loadCHCsTable();
        } catch (error) {
            showToast(error.message, 'error');
        }
    });
}

async function renderAllMachines(container) {
    container.innerHTML = `
        <h2>All Machines</h2>
        <div class="row mb-3">
            <div class="col-md-4">
                <input type="text" class="form-control" id="search-machine" placeholder="Search by name">
            </div>
            <div class="col-md-4">
                <select class="form-control" id="filter-chc">
                    <option value="">All CHCs</option>
                </select>
            </div>
        </div>
        <div id="all-machines-table"></div>
    `;
    // Populate CHC filter
    const chcs = await api.listCHCs();
    const chcSelect = document.getElementById('filter-chc');
    chcs.forEach(c => {
        chcSelect.innerHTML += `<option value="${c.id}">${c.chc_name}</option>`;
    });
    document.getElementById('search-machine').addEventListener('input', loadAllMachines);
    document.getElementById('filter-chc').addEventListener('change', loadAllMachines);
    await loadAllMachines();
}

async function loadAllMachines() {
    const container = document.getElementById('all-machines-table');
    showSpinner(container);
    try {
        const search = document.getElementById('search-machine').value;
        const chc = document.getElementById('filter-chc').value;
        const params = {};
        if (search) params.search = search;
        if (chc) params.chc = chc;
        const machines = await api.listMachines(params);
        let html = `
            <table class="table table-striped">
                <thead>
                    <tr>
                        <th>Code</th><th>Name</th><th>Type</th><th>CHC</th><th>Status</th>
                    </tr>
                </thead>
                <tbody>
        `;
        machines.forEach(m => {
            html += `
                <tr>
                    <td>${m.machine_code}</td>
                    <td>${m.machine_name}</td>
                    <td>${m.machine_type}</td>
                    <td>${m.chc_details.name}</td>
                    <td><span class="badge bg-${m.status === 'Idle' ? 'success' : m.status === 'In Use' ? 'primary' : 'warning'}">${m.status}</span></td>
                </tr>
            `;
        });
        html += '</tbody></table>';
        container.innerHTML = html;
    } catch (error) {
        container.innerHTML = `<div class="alert alert-danger">${error.message}</div>`;
    }
}

async function renderAllBookings(container) {
    container.innerHTML = `
        <h2>All Bookings</h2>
        <div class="row mb-3">
            <div class="col-md-4">
                <select class="form-control" id="all-status-filter">
                    <option value="">All Status</option>
                    <option value="Pending">Pending</option>
                    <option value="Approved">Approved</option>
                    <option value="Active">Active</option>
                    <option value="Completed">Completed</option>
                    <option value="Rejected">Rejected</option>
                    <option value="Cancelled">Cancelled</option>
                </select>
            </div>
        </div>
        <div id="all-bookings-table"></div>
    `;
    document.getElementById('all-status-filter').addEventListener('change', loadAllBookings);
    await loadAllBookings();
}

async function loadAllBookings() {
    const container = document.getElementById('all-bookings-table');
    showSpinner(container);
    try {
        const status = document.getElementById('all-status-filter').value;
        const params = status ? { status } : {};
        const bookings = await api.listBookings(params);
        let html = `
            <table class="table table-striped">
                <thead>
                    <tr>
                        <th>ID</th><th>Farmer</th><th>CHC</th><th>Machine</th><th>Dates</th><th>Status</th>
                    </tr>
                </thead>
                <tbody>
        `;
        bookings.forEach(b => {
            html += `
                <tr>
                    <td>${b.id}</td>
                    <td>${b.farmer_name}</td>
                    <td>${b.chc_details.chc_name}</td>
                    <td>${b.machine_details.machine_name}</td>
                    <td>${b.start_date} to ${b.end_date}</td>
                    <td><span class="badge bg-${b.status === 'Pending' ? 'warning' : b.status === 'Approved' ? 'info' : b.status === 'Active' ? 'primary' : b.status === 'Completed' ? 'success' : 'secondary'}">${b.status}</span></td>
                </tr>
            `;
        });
        html += '</tbody></table>';
        container.innerHTML = html;
    } catch (error) {
        container.innerHTML = `<div class="alert alert-danger">${error.message}</div>`;
    }
}

async function renderAnalytics(container) {
    container.innerHTML = `<h2>Machine Analytics</h2><div id="analytics-charts"></div>`;
    try {
        const data = await api.getMachineAnalytics();
        const chartsDiv = document.getElementById('analytics-charts');
        // Machine types
        let typeHtml = '<h4>Machine Types</h4><ul>';
        data.machine_types.forEach(t => {
            typeHtml += `<li>${t.machine_type}: ${t.count}</li>`;
        });
        typeHtml += '</ul>';
        // Status breakdown
        let statusHtml = '<h4>Status Breakdown</h4><ul>';
        data.status_breakdown.forEach(s => {
            statusHtml += `<li>${s.status}: ${s.count}</li>`;
        });
        statusHtml += '</ul>';
        chartsDiv.innerHTML = typeHtml + statusHtml;
    } catch (error) {
        container.innerHTML += `<div class="alert alert-danger">${error.message}</div>`;
    }
}