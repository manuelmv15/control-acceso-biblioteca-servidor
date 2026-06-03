const Estudiantes = {
    datos: [],

    async cargar() {
        try {
            this.datos = await API.fetch('/estudiantes');
            this.filtrar();
        } catch (e) { console.error(e); }
    },

    filtrar() {
        const q = document.getElementById('filter-est')?.value.toLowerCase() || '';
        const filtrados = this.datos.filter(e =>
            e.carnet.toLowerCase().includes(q) ||
            (e.nombre||'').toLowerCase().includes(q) ||
            (e.carrera||'').toLowerCase().includes(q)
        );
        this._render(filtrados);
    },

    _render(datos) {
        const tbody = document.getElementById('tabla-est-body');
        const noEl  = document.getElementById('no-est');
        if (!tbody) return;
        tbody.innerHTML = '';
        noEl?.classList.toggle('hidden', datos.length > 0);
        datos.forEach(e => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${e.carnet}</td>
                <td>${e.nombre}</td>
                <td>${e.carrera||'—'}</td>
                <td>${e.facultad||'—'}</td>
                <td>${e.departamento||'—'}</td>
                <td>${e.sexo||'—'}</td>
                <td>${e.fecha_registro||'—'}</td>
            `;
            tbody.appendChild(tr);
        });
    },

    init() {
        document.getElementById('filter-est')?.addEventListener('input', () => this.filtrar());
        this.cargar();
    }
};
