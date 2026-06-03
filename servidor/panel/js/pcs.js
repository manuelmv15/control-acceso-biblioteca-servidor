const PCs = {
    async cargar() {
        try {
            const pcs = await API.fetch('/estado');
            this._renderGrid(pcs);
            const n = pcs.filter(p => p.sesion_activa).length;
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
                        <div class="pc-dato"><span>Carnet</span><strong>${pc.carnet||'—'}</strong></div>
                        <div class="pc-dato"><span>Nombre</span><strong>${pc.nombre||'—'}</strong></div>
                        <div class="pc-dato"><span>Desde</span><strong>${pc.hora_inicio ? fmtHora(pc.hora_inicio) : '—'}</strong></div>
                    </div>
                ` : '<div class="pc-libre-msg">Disponible</div>'}
                <div class="pc-footer">Última señal: ${ultima}</div>
            `;
            grid.appendChild(card);
        });
    },

    init() {
        document.getElementById('btn-refresh-pcs')?.addEventListener('click', () => this.cargar());
        this.cargar();
    }
};
