const PCs = {
    async cargar() {
        try {
            const [estados, mantenimiento] = await Promise.all([
                API.fetch('/estado'),
                API.fetch('/pcs'),
            ]);
            this._renderGrid(estados);
            this._renderMantenimiento(mantenimiento);
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
                    <span class="pc-nombre">${escapeHtml(pc.pc_nombre) || escapeHtml(pc.pc_id)}</span>
                    <span class="pc-badge">${activa ? 'EN USO' : 'LIBRE'}</span>
                    <button class="pc-card-toggle" type="button" aria-expanded="false" aria-label="Ver detalles de ${escapeHtml(pc.pc_nombre) || escapeHtml(pc.pc_id)}">+</button>
                </div>
                <div class="pc-card-details">
                    <div class="pc-id">${escapeHtml(pc.pc_id)}</div>
                    ${activa ? `
                        <div class="pc-usuario">
                            <div class="pc-dato"><span>Carnet</span><strong>${escapeHtml(pc.carnet) || 'Invitado'}</strong></div>
                            <div class="pc-dato"><span>Nombre</span><strong>${escapeHtml(pc.nombre) || '—'}</strong></div>
                            <div class="pc-dato"><span>Desde</span><strong>${pc.hora_inicio ? fmtHora(pc.hora_inicio) : '—'}</strong></div>
                        </div>
                    ` : '<div class="pc-libre-msg">Disponible</div>'}
                    <div class="pc-footer">Última señal: ${ultima}</div>
                </div>
            `;
            grid.appendChild(card);
        });
        grid.querySelectorAll('.pc-card-toggle').forEach(btn =>
            btn.addEventListener('click', () => this._toggleCard(btn))
        );
    },

    _toggleCard(btn) {
        if (!window.matchMedia('(max-width: 1024px)').matches) return;
        const card = btn.closest('.pc-card');
        const abierta = card.classList.toggle('is-open');
        btn.setAttribute('aria-expanded', String(abierta));
    },

    _fmtDuracion(minutos) {
        const h = Math.floor(minutos / 60), m = minutos % 60;
        return h > 0 ? `${h}h ${m}m` : `${m}m`;
    },

    _badgeEstado(estado) {
        const etiquetas = { optimo: 'Óptimo', pendiente: 'Pendiente', critico: 'Crítico' };
        if (!estado) return '<span class="specs-resumen">Sin datos</span>';
        return `<span class="badge-${estado}">${etiquetas[estado] || estado}</span>`;
    },

    _specsResumen(pc) {
        if (!pc.cpu && !pc.ram_total_mb && !pc.almacenamiento_total_gb) {
            return '<span class="specs-resumen">Sin reportar</span>';
        }
        const ram = pc.ram_total_mb ? `${Math.round(pc.ram_total_mb / 1024)}GB RAM` : null;
        const disco = pc.almacenamiento_total_gb ? `${pc.almacenamiento_total_gb}GB disco` : null;
        const partes = [pc.cpu ? escapeHtml(pc.cpu) : null, ram, disco].filter(Boolean).join(' · ');
        const salud = [];
        if (pc.temperatura_cpu_c != null) salud.push(`${pc.temperatura_cpu_c}°C`);
        if (pc.disco_smart_ok === 0) salud.push('SMART: FALLA');
        const lineaSalud = salud.length ? `<br>${salud.join(' · ')}` : '';
        return `<span class="specs-resumen">${partes}${lineaSalud}</span>`;
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
            const horas = pc.horas_uso_acumuladas != null ? `${Number(pc.horas_uso_acumuladas).toFixed(1)}h` : '—';
            const tr = document.createElement('tr');
            const pcId = escapeHtml(pc.pc_id);
            const nombre = escapeHtml(pc.nombre) || pcId;
            tr.className = `compact-row${pc.estado_mantenimiento === 'critico' ? ' fila-critica' : ''}`;
            tr.innerHTML = `
                <td class="compact-summary" data-label="PC">
                    <button class="table-row-toggle" type="button" aria-expanded="false" aria-label="Ver detalles de ${nombre}">
                        <span class="compact-summary-kicker">${pcId}</span>
                        <span class="compact-summary-title">${nombre}</span>
                        <span class="table-toggle-indicator" aria-hidden="true">+</span>
                    </button>
                </td>
                <td data-label="Último mantenimiento">${ultimo}</td>
                <td data-label="Uso en sesiones">${this._fmtDuracion(pc.minutos_uso_desde_mantenimiento)}</td>
                <td data-label="Horas encendida">${horas}</td>
                <td data-label="Estado">${this._badgeEstado(pc.estado_mantenimiento)}</td>
                <td data-label="Especificaciones">${this._specsResumen(pc)}</td>
                <td class="compact-action" data-label="Acciones"><button class="btn-secondary btn-mantenimiento" data-pc="${pcId}">Registrar mantenimiento</button></td>
            `;
            tbody.appendChild(tr);
        });

        tbody.querySelectorAll('.table-row-toggle').forEach(btn =>
            btn.addEventListener('click', () => this._toggleTableRow(btn))
        );
        tbody.querySelectorAll('.btn-mantenimiento').forEach(btn =>
            btn.addEventListener('click', () => this._registrarMantenimiento(btn.dataset.pc))
        );
    },

    _toggleTableRow(btn) {
        if (!window.matchMedia('(max-width: 1024px)').matches) return;
        const fila = btn.closest('.compact-row');
        const abierta = fila.classList.toggle('is-open');
        btn.setAttribute('aria-expanded', String(abierta));
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
