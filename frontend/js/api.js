const API_BASE_URL = 'http://127.0.0.1:8000/api/v1';

class API {
    // No longer a static getHeaders – we build headers dynamically in request()
    static async refreshToken() {
        const refresh = localStorage.getItem('refresh_token');
        if (!refresh) throw new Error('No refresh token');
        try {
            const response = await fetch(`${API_BASE_URL}/auth/refresh/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ refresh })
            });
            if (!response.ok) throw new Error('Refresh failed');
            const data = await response.json();
            localStorage.setItem('access_token', data.access);
            return data.access;
        } catch (e) {
            this.logout();
            throw e;
        }
    }

    static async request(endpoint, method = 'GET', body = null, auth = false, retry = true) {
        const url = `${API_BASE_URL}${endpoint}`;
        
        // Build headers dynamically
        const headers = {};
        if (auth) {
            const token = localStorage.getItem('access_token');
            if (token) {
                headers['Authorization'] = `Bearer ${token}`;
            }
        }
        // Only set Content-Type if there is a body (POST, PUT, PATCH)
        if (body) {
            headers['Content-Type'] = 'application/json';
        }

        const options = {
            method,
            headers,
        };

        if (body) {
            options.body = JSON.stringify(body);
        }

        try {
            const response = await fetch(url, options);

            // Handle 401 Unauthorized – attempt refresh once
            if (response.status === 401 && auth && retry) {
                console.warn('Access token expired, attempting refresh...');
                try {
                    await this.refreshToken();
                    // Retry the original request with new token
                    return this.request(endpoint, method, body, auth, false);
                } catch (refreshError) {
                    console.error('Refresh failed, logging out.', refreshError);
                    this.logout();
                    return null;
                }
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
            throw error;
        }
    }

    // Auth
    static async login(username, password) {
        const data = await this.request('/auth/login/', 'POST', { username, password });
        if (data.access) {
            localStorage.setItem('access_token', data.access);
            localStorage.setItem('refresh_token', data.refresh);
            try {
                const profile = await this.getProfile();
                localStorage.setItem('user_role', profile.role);
                return profile;
            } catch (error) {
                // Profile fetch failed – clean up and throw
                this.logout();
                throw new Error('Failed to fetch user profile');
            }
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

    // Get single machine detail (for CHC admin)
    static async getMachineDetail(id) {
        return await this.request(`/machines/${id}/`, 'GET', null, true);
    }

    // Bookings
    static async createBooking(data) {
        return await this.request('/bookings/public/create/', 'POST', data, false);
    }

    // CHC Search
    static async searchCHCs(query) {
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