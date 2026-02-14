const API_BASE_URL = 'http://127.0.0.1:8000/api/v1';

class API {
    static getHeaders(auth = false) {
        const headers = {
            'Content-Type': 'application/json'
        };
        if (auth) {
            const token = localStorage.getItem('access_token');
            if (token) {
                headers['Authorization'] = `Bearer ${token}`;
            }
        }
        return headers;
    }

    static async request(endpoint, method = 'GET', body = null, auth = false) {
        const url = `${API_BASE_URL}${endpoint}`;
        const options = {
            method,
            headers: this.getHeaders(auth),
        };

        if (body) {
            options.body = JSON.stringify(body);
        }

        try {
            const response = await fetch(url, options);

            // Handle 401 Unauthorized (Token expiry logic implies re-login for now)
            if (response.status === 401 && auth) {
                // Ideally refresh token here, but for simplicity redirection:
                console.warn("Unauthorized access. Redirecting to login.");
                this.logout();
                return null;
            }

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || data.error || 'Something went wrong');
            }

            // Handle DRF Pagination
            if (data.results && Array.isArray(data.results)) {
                return data.results;
            }

            return data;
        } catch (error) {
            console.error(`API Error (${endpoint}):`, error);
            throw error; // Re-throw to be handled by UI
        }
    }

    // Auth
    static async login(username, password) {
        const data = await this.request('/auth/login/', 'POST', { username, password });
        if (data.access) {
            localStorage.setItem('access_token', data.access);
            localStorage.setItem('refresh_token', data.refresh);
            // Fetch profile to know role
            const profile = await this.getProfile();
            localStorage.setItem('user_role', profile.role);
            return profile;
        }
    }

    static async getProfile() {
        return await this.request('/auth/profile/', 'GET', null, true);
    }

    static logout() {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user_role');
        window.location.href = 'index.html';
    }

    // Analytics (Govt)
    static async getGovtDashboard() {
        return await this.request('/analytics/govt/dashboard/', 'GET', null, true);
    }

    // Analytics (CHC)
    static async getCHCDashboard() {
        return await this.request('/analytics/chc/dashboard/', 'GET', null, true);
    }

    // Machines
    static async getMachines(publicView = false, chcId = null) {
        let endpoint = publicView ? '/machines/public/' : '/machines/';
        if (chcId) {
            endpoint += `?chc=${chcId}`;
        }
        return await this.request(endpoint, 'GET', null, !publicView);
    }

    // Bookings
    static async createBooking(data) {
        return await this.request('/bookings/public/create/', 'POST', data, false);
    }

    // CHC Search
    static async searchCHCs(query) {
        // Construct query string
        const params = new URLSearchParams(query).toString();
        return await this.request(`/chc/public/search/?${params}`, 'GET', null, false);
    }

    // CHC Admin Bookings
    static async getCHCBookings() {
        return await this.request('/bookings/chc/', 'GET', null, true);
    }

    static async updateBookingStatus(id, action, notes = '') {
        return await this.request(`/bookings/chc/${id}/action/`, 'PATCH', { action, notes }, true);
    }
}
