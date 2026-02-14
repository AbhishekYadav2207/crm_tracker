import { loginUser, registerUser, getUserProfile } from './api.js';

// Store tokens
export function setTokens(access, refresh) {
    localStorage.setItem('access_token', access);
    localStorage.setItem('refresh_token', refresh);
}

export function clearTokens() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user_role');
    localStorage.removeItem('user_data');
}

export function isAuthenticated() {
    return !!localStorage.getItem('access_token');
}

export function getUserRole() {
    return localStorage.getItem('user_role');
}

export function setUserRole(role) {
    localStorage.setItem('user_role', role);
}

export function setUserData(data) {
    localStorage.setItem('user_data', JSON.stringify(data));
}

export function getUserData() {
    const data = localStorage.getItem('user_data');
    return data ? JSON.parse(data) : null;
}

// Login form handler
export async function handleLogin(username, password) {
    try {
        const data = await loginUser({ username, password });
        setTokens(data.access, data.refresh);
        // Fetch profile to get role
        const profile = await getUserProfile();
        setUserRole(profile.role);
        setUserData(profile);
        return { success: true, role: profile.role };
    } catch (error) {
        return { success: false, error: error.message };
    }
}

// Register handler
export async function handleRegister(userData) {
    try {
        await registerUser(userData);
        return { success: true };
    } catch (error) {
        return { success: false, error: error.message };
    }
}

// Logout
export function logout() {
    clearTokens();
    window.location.hash = '#';
    window.location.reload(); // simple refresh to reset state
}