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

    async login(username, password) {
        const res = await fetch('/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password }),
        });
        if (!res.ok) throw new Error('Credenciales incorrectas');
        return res.json();
    }
};
