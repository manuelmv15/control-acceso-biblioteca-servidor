const PCs = {
    async cargar() {
        try {
            const [estados, mantenimiento] = await Promise.all([
                API.fetch('/estado'),
                API.fetch('/pcs'),
            ]);
            this._renderGrid(estados);
            this._renderMantenimiento(mantenimiento);
            const n = estados.filter(p => p.sesion_activa).length;
            document.getElementById('pcs-activas-badge').textContent =
                `● ${n} PC${n!==1?'s':''} activa${n!==1?'s':''}`;
        } catch (e) { console.error(e); }
    },

    _renderGrid(pcs) {
        const grid = document.getElementById('pcs-grid');
        const noEl = document.getElementById('no-pcs');
        if (!grid) return;
        grid.innerHTML = '';
        noEl?.classList.toggle('hidden', pcs.length > 0);

        pcs.forEach(pc => {
            const activa = !!pc.sesion_activa;
            const ultima = pc.ultima_actualizacion
                ? new Date(pc.ultima_actualizacion + 'Z').toLocaleTimeString('es-GT', { hour: '2-digit', minute: '2-digit' })
                : '—';

            const card = document.createElement('div');
            card.className = 'pc-card ' + (activa ? 'pc-activa' : 'pc-libre');
            card.innerHTML = `
                <div class="pc-header">
                    <span class="pc-status-dot"></span>
                    <span class="pc-nombre">${pc.pc_nombre || pc.pc_id}</span>
                    <span class="pc-badge">${activa ? 'EN USO' : 'LIBRE'}</span>
                </div>
                <div class="pc-id">${pc.pc_id}</div>
                ${activa ? `
                    <div class="pc-usuario">
                        <div class="pc-dato"><span>Carnet</span><strong>${pc.carnet||'Invitado'}</strong></div>
                        <div class="pc-dato"><span>Nombre</span><strong>${pc.nombre||'—'}</strong></div>
                        <div class="pc-dato"><span>Desde</span><strong>${pc.hora_inicio ? fmtHora(pc.hora_inicio) : '—'}</strong></div>
                    </div>
                ` : '<div class="pc-libre-msg">Disponible</div>'}
                <div class="pc-footer">Última señal: ${ultima}</div>
            `;
            grid.appendChild(card);
        });
    },

    _fmtDuracion(minutos) {
        const h = Math.floor(minutos / 60), m = minutos % 60;
        return h > 0 ? `${h}h ${m}m` : `${m}m`;
    },

    _renderMantenimiento(pcs) {
        const tbody = document.getElementById('mantenimiento-body');
        const noEl = document.getElementById('no-mantenimiento');
        if (!tbody) return;
        tbody.innerHTML = '';
        noEl?.classList.toggle('hidden', pcs.length > 0);

        pcs.forEach(pc => {
            const ultimo = pc.ultimo_mantenimiento
                ? new Date(pc.ultimo_mantenimiento.replace(' ', 'T')).toLocaleDateString('es-GT', { day: '2-digit', month: '2-digit', year: 'numeric' })
                : 'Nunca';
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${pc.nombre || pc.pc_id}</td>
                <td>${ultimo}</td>
                <td>${this._fmtDuracion(pc.minutos_uso_desde_mantenimiento)}</td>
                <td><button class="btn-secondary btn-mantenimiento" data-pc="${pc.pc_id}">Registrar mantenimiento</button></td>
            `;
            tbody.appendChild(tr);
        });

        tbody.querySelectorAll('.btn-mantenimiento').forEach(btn =>
            btn.addEventListener('click', () => this._registrarMantenimiento(btn.dataset.pc))
        );
    },

    async _registrarMantenimiento(pcId) {
        if (!confirm(`¿Confirmar que se realizó mantenimiento en ${pcId}?`)) return;
        try {
            await API.fetchRaw(`/pcs/${pcId}/mantenimiento`, { method: 'POST' });
            this.cargar();
        } catch (e) { alert(e.message); }
    },

    init() {
        document.getElementById('btn-refresh-pcs')?.addEventListener('click', () => this.cargar());
        this.cargar();
    }
};
