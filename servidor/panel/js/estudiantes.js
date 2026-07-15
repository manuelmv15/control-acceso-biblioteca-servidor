const Estudiantes = {
    datos: [],
    _editCarnet: null,

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
                <td>${e.nombre||'—'}</td>
                <td>${e.carrera||'—'}</td>
                <td>${e.facultad||'—'}</td>
                <td>${e.sexo||'—'}</td>
                <td>${e.fecha_registro||'—'}</td>
                <td><button class="btn-edit-est" data-carnet="${e.carnet}">Editar</button></td>
            `;
            tbody.appendChild(tr);
        });
        tbody.querySelectorAll('.btn-edit-est').forEach(btn =>
            btn.addEventListener('click', () => this._abrirEditar(btn.dataset.carnet))
        );
    },

    _abrirModal(titulo, datos = {}) {
        document.getElementById('modal-est-titulo').textContent = titulo;
        document.getElementById('est-carnet').value       = datos.carnet      || '';
        document.getElementById('est-carnet').disabled    = !!datos.carnet;
        document.getElementById('est-nombre').value       = datos.nombre      || '';
        document.getElementById('est-carrera').value      = datos.carrera     || '';
        document.getElementById('est-facultad').value     = datos.facultad    || '';
        document.getElementById('est-fecha-nac').value    = datos.fecha_nacimiento || '';
        document.getElementById('est-sexo').value         = datos.sexo        || '';
        document.getElementById('modal-est-error').textContent = '';
        document.getElementById('modal-est').classList.remove('hidden');
    },

    _cerrarModal() {
        document.getElementById('modal-est').classList.add('hidden');
        this._editCarnet = null;
    },

    _abrirNuevo() {
        this._editCarnet = null;
        this._abrirModal('Nuevo estudiante');
    },

    _abrirEditar(carnet) {
        const est = this.datos.find(e => e.carnet === carnet);
        if (!est) return;
        this._editCarnet = carnet;
        this._abrirModal('Editar estudiante', est);
    },

    async _guardar() {
        const carnet      = document.getElementById('est-carnet').value.trim();
        const nombre      = document.getElementById('est-nombre').value.trim();
        const carrera     = document.getElementById('est-carrera').value.trim();
        const facultad    = document.getElementById('est-facultad').value.trim();
        const fecha_nac   = document.getElementById('est-fecha-nac').value;
        const sexo        = document.getElementById('est-sexo').value;
        const errEl       = document.getElementById('modal-est-error');

        if (!carnet || !nombre) { errEl.textContent = 'Carnet y nombre son requeridos.'; return; }

        const body = { carnet, nombre, carrera: carrera||null, facultad: facultad||null,
                       fecha_nacimiento: fecha_nac||null, sexo: sexo||null };
        try {
            if (this._editCarnet) {
                await API.fetchRaw(`/estudiantes/${this._editCarnet}`, { method: 'PUT', body });
            } else {
                await API.fetchRaw('/estudiantes', { method: 'POST', body });
            }
            this._cerrarModal();
            await this.cargar();
        } catch (e) {
            errEl.textContent = e.message || 'Error al guardar.';
        }
    },

    init() {
        document.getElementById('filter-est')?.addEventListener('input', () => this.filtrar());
        document.getElementById('btn-nuevo-est')?.addEventListener('click', () => this._abrirNuevo());
        document.getElementById('btn-est-guardar')?.addEventListener('click', () => this._guardar());
        document.getElementById('btn-est-cancelar')?.addEventListener('click', () => this._cerrarModal());
        document.getElementById('modal-est')?.addEventListener('click', e => {
            if (e.target.id === 'modal-est') this._cerrarModal();
        });
        this.cargar();
    }
};
