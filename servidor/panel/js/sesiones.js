const Sesiones = {
    datos: [],
    _ticker: null,

    async cargar() {
        const fecha    = document.getElementById('filter-fecha')?.value   || '';
        const carrera  = document.getElementById('filter-carrera')?.value || '';
        const pc       = document.getElementById('filter-pc')?.value      || '';

        const params = new URLSearchParams();
        if (fecha)   params.set('fecha',   fecha);
        if (carrera) params.set('carrera', carrera);
        if (pc)      params.set('pc_id',   pc);

        try {
            const [sesiones, pcsActivas, resumen] = await Promise.all([
                API.fetch(`/reportes/sesiones?${params}`),
                API.fetch('/reportes/pcs-activas'),
                API.fetch(`/reportes/resumen-dia?fecha=${fecha}`),
            ]);

            this.datos = sesiones;
            this._renderResumen(resumen);
            this._actualizarPcsBadge(pcsActivas.length);
            this._actualizarFiltros(sesiones);
            this.filtrarLocal();

            document.getElementById('last-update').textContent =
                'Actualizado: ' + new Date().toLocaleTimeString('es-GT');
        } catch (e) { console.error(e); }
    },

    filtrarLocal() {
        const q       = document.getElementById('filter-carnet')?.value.toLowerCase() || '';
        const facultad = document.getElementById('filter-facultad')?.value || '';
        const filtered = this.datos.filter(s =>
            (!q       || s.carnet.toLowerCase().includes(q) || (s.nombre||'').toLowerCase().includes(q)) &&
            (!facultad || s.facultad === facultad)
        );
        this._renderTabla(filtered);
    },

    exportarCSV() {
        const fecha = document.getElementById('filter-fecha')?.value || 'hoy';
        const headers = ['Carnet','Nombre','Carrera','Facultad','PC','Hora inicio','Hora fin','Minutos'];
        const rows = this.datos.map(s => [
            s.carnet, s.nombre||'', s.carrera||'', s.facultad||'',
            s.pc_id, s.hora_inicio, s.hora_fin||'', s.minutos??''
        ]);
        const csv = [headers, ...rows].map(r => r.map(c => `"${c}"`).join(',')).join('\n');
        const blob = new Blob(['﻿' + csv], { type: 'text/csv;charset=utf-8;' });
        const a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = `sesiones_${fecha}.csv`;
        a.click();
    },

    _elapsed(hora_inicio) {
        const start = new Date(hora_inicio.replace(' ', 'T') + (hora_inicio.includes('T') ? '' : 'Z'));
        const diff = Math.floor((Date.now() - start) / 60000);
        if (diff < 0) return null;
        const h = Math.floor(diff / 60), m = diff % 60;
        return h > 0 ? `${h}h ${m}m` : `${m}m`;
    },

    _renderTabla(datos) {
        const tbody = document.getElementById('tabla-body');
        const noData = document.getElementById('no-data');
        if (!tbody) return;
        tbody.innerHTML = '';
        noData?.classList.toggle('hidden', datos.length > 0);
        datos.forEach(s => {
            const activa = !s.hora_fin;
            let dur;
            if (s.minutos != null) {
                dur = `${Math.floor(s.minutos/60)}h ${s.minutos%60}m`;
            } else if (activa) {
                dur = this._elapsed(s.hora_inicio) ?? '—';
            } else {
                dur = '—';
            }
            const tr = document.createElement('tr');
            if (activa) tr.classList.add('fila-activa');
            tr.innerHTML = `
                <td>${s.carnet}</td>
                <td>${s.nombre||'—'}</td>
                <td>${s.carrera||'—'}</td>
                <td>${s.pc_id}</td>
                <td>${fmtHora(s.hora_inicio)}</td>
                <td>${activa ? '<span class="badge-en-sesion">● En sesión</span>' : fmtHora(s.hora_fin)}</td>
                <td ${activa ? `class="dur-activa" data-hora-inicio="${s.hora_inicio}"` : ''}>${dur}</td>
            `;
            tbody.appendChild(tr);
        });
        this._iniciarTicker();
    },

    _iniciarTicker() {
        clearInterval(this._ticker);
        this._ticker = setInterval(() => {
            document.querySelectorAll('td.dur-activa[data-hora-inicio]').forEach(td => {
                td.textContent = this._elapsed(td.dataset.horaInicio) ?? '—';
            });
        }, 60000);
    },

    _renderResumen(r) {
        const bar = document.getElementById('resumen-bar');
        if (!bar) return;
        bar.innerHTML = [
            { val: r.total_sesiones??0,   lbl: 'Sesiones hoy' },
            { val: r.estudiantes_unicos??0, lbl: 'Estudiantes únicos' },
            { val: r.pcs_usadas??0,        lbl: 'PCs usadas' },
            { val: r.minutos_promedio ? `${r.minutos_promedio} min` : '—', lbl: 'Promedio / sesión' },
        ].map(i => `<div class="resumen-item"><div class="val">${i.val}</div><div class="lbl">${i.lbl}</div></div>`).join('');
    },

    _actualizarPcsBadge(n) {
        document.getElementById('pcs-activas-badge').textContent =
            `● ${n} PC${n!==1?'s':''} activa${n!==1?'s':''}`;
    },

    _actualizarFiltros(datos) {
        const uniq = (key) => [...new Set(datos.map(d => d[key]).filter(Boolean))].sort();
        actualizarSelect('filter-carrera', uniq('carrera'), 'Todas las carreras');
        actualizarSelect('filter-facultad', uniq('facultad'), 'Todas las facultades');
        actualizarSelect('filter-pc', uniq('pc_id'), 'Todas las PCs');
    },

    init() {
        const hoy = new Date().toISOString().split('T')[0];
        const el = document.getElementById('filter-fecha');
        if (el && !el.value) el.value = hoy;

        document.getElementById('filter-fecha')?.addEventListener('change', () => this.cargar());
        document.getElementById('filter-carrera')?.addEventListener('change', () => this.cargar());
        document.getElementById('filter-facultad')?.addEventListener('change', () => this.filtrarLocal());
        document.getElementById('filter-pc')?.addEventListener('change', () => this.cargar());
        document.getElementById('filter-carnet')?.addEventListener('input', () => this.filtrarLocal());
        document.getElementById('btn-export')?.addEventListener('click', () => this.exportarCSV());

        this.cargar();
    }
};
