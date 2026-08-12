const API = {
    token: null,

    setToken(t)   { this.token = t; sessionStorage.setItem('token', t); },
    clearToken()  { this.token = null; sessionStorage.removeItem('token'); },
    loadToken()   { this.token = sessionStorage.getItem('token'); return this.token; },

    async fetch(url) {
        const res = await fetch(url, {
            headers: { Authorization: `Bearer ${this.token}` }
        });
        if (res.status === 401) { App.logout(); throw new Error('Sesión expirada'); }
        return res.json();
    },

    async fetchRaw(url, { method = 'GET', body } = {}) {
        const opts = {
            method,
            headers: { Authorization: `Bearer ${this.token}`, 'Content-Type': 'application/json' },
        };
        if (body) opts.body = JSON.stringify(body);
        const res = await fetch(url, opts);
        if (res.status === 401) { App.logout(); throw new Error('Sesión expirada'); }
        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.detail || `Error ${res.status}`);
        }
        return res.status === 204 ? null : res.json();
    },

    async cambiarPassword(passwordActual, passwordNueva) {
        return this.fetchRaw('/auth/password', {
            method: 'PUT',
            body: { password_actual: passwordActual, password_nueva: passwordNueva },
        });
    },

    async login(username, password) {
        const res = await fetch('/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password }),
        });
        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.detail || 'Credenciales incorrectas');
        }
        return res.json();
    }
};
