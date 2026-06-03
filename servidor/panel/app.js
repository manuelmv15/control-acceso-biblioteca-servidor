let TOKEN = null;
let todosLosDatos = [];
let todosEstudiantes = [];
let refreshInterval = null;
let tabActual = "sesiones";

async function login() {
    const user = document.getElementById("username").value;
    const pass = document.getElementById("password").value;
    const err = document.getElementById("login-error");
    err.textContent = "";
    try {
        const res = await fetch("/auth/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username: user, password: pass }),
        });
        if (!res.ok) throw new Error("Credenciales incorrectas");
        const data = await res.json();
        TOKEN = data.access_token;
        sessionStorage.setItem("token", TOKEN);
        mostrarPanel();
    } catch (e) {
        err.textContent = e.message;
    }
}

function logout() {
    TOKEN = null;
    sessionStorage.removeItem("token");
    clearInterval(refreshInterval);
    document.getElementById("panel-screen").classList.add("hidden");
    document.getElementById("login-screen").classList.remove("hidden");
}

function mostrarPanel() {
    document.getElementById("login-screen").classList.add("hidden");
    document.getElementById("panel-screen").classList.remove("hidden");
    const hoy = new Date().toISOString().split("T")[0];
    document.getElementById("filter-fecha").value = hoy;
    cargarDatos();
    refreshInterval = setInterval(() => {
        cargarDatos();
        if (tabActual === "pcs") cargarEstadoPCs();
    }, 30000);
}

function cambiarTab(tab) {
    tabActual = tab;
    document.querySelectorAll(".tab").forEach(b => b.classList.remove("active"));
    document.querySelectorAll(".tab-content").forEach(c => c.classList.add("hidden"));
    event.target.classList.add("active");
    document.getElementById("tab-" + tab).classList.remove("hidden");

    if (tab === "pcs") cargarEstadoPCs();
    if (tab === "estudiantes") cargarEstudiantes();
}

async function apiFetch(url) {
    const res = await fetch(url, { headers: { Authorization: `Bearer ${TOKEN}` } });
    if (res.status === 401) { logout(); throw new Error("Sesión expirada"); }
    return res.json();
}

// ── SESIONES ────────────────────────────────────────────────────

async function cargarDatos() {
    const fecha = document.getElementById("filter-fecha").value;
    const carrera = document.getElementById("filter-carrera").value;
    const facultad = document.getElementById("filter-facultad").value;
    const pc = document.getElementById("filter-pc").value;

    const params = new URLSearchParams();
    if (fecha) params.set("fecha", fecha);
    if (carrera) params.set("carrera", carrera);
    if (pc) params.set("pc_id", pc);

    try {
        const [sesiones, pcsActivas, resumen] = await Promise.all([
            apiFetch(`/reportes/sesiones?${params}`),
            apiFetch("/reportes/pcs-activas"),
            apiFetch(`/reportes/resumen-dia?fecha=${fecha || ""}`),
        ]);

        todosLosDatos = sesiones;
        actualizarFiltrosDinamicos(sesiones);
        renderTabla(sesiones.filter(s => !facultad || s.facultad === facultad));
        renderPcsActivasBadge(pcsActivas);
        renderResumen(resumen);

        document.getElementById("last-update").textContent =
            "Actualizado: " + new Date().toLocaleTimeString("es-GT");
    } catch (e) {
        console.error(e);
    }
}

function actualizarFiltrosDinamicos(datos) {
    const carreras = [...new Set(datos.map(d => d.carrera).filter(Boolean))].sort();
    const facultades = [...new Set(datos.map(d => d.facultad).filter(Boolean))].sort();
    const pcs = [...new Set(datos.map(d => d.pc_id).filter(Boolean))].sort();
    actualizarSelect("filter-carrera", carreras, "Todas las carreras");
    actualizarSelect("filter-facultad", facultades, "Todas las facultades");
    actualizarSelect("filter-pc", pcs, "Todas las PCs");
}

function actualizarSelect(id, opciones, placeholder) {
    const sel = document.getElementById(id);
    const actual = sel.value;
    sel.innerHTML = `<option value="">${placeholder}</option>`;
    opciones.forEach(o => {
        const opt = document.createElement("option");
        opt.value = o;
        opt.textContent = o;
        if (o === actual) opt.selected = true;
        sel.appendChild(opt);
    });
}

function renderTabla(datos) {
    const tbody = document.getElementById("tabla-body");
    const noData = document.getElementById("no-data");
    tbody.innerHTML = "";
    noData.classList.toggle("hidden", datos.length > 0);

    datos.forEach(s => {
        const duracion = s.minutos != null
            ? `${Math.floor(s.minutos / 60)}h ${s.minutos % 60}m`
            : "—";
        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td>${s.carnet}</td>
            <td>${s.nombre || "—"}</td>
            <td>${s.carrera || "—"}</td>
            <td>${s.pc_id}</td>
            <td>${fmtHora(s.hora_inicio)}</td>
            <td>${s.hora_fin ? fmtHora(s.hora_fin) : "En sesión"}</td>
            <td>${duracion}</td>
        `;
        tbody.appendChild(tr);
    });
}

function fmtHora(iso) {
    if (!iso) return "—";
    const d = new Date(iso.replace(" ", "T") + (iso.includes("T") ? "" : "Z"));
    return d.toLocaleTimeString("es-GT", { hour: "2-digit", minute: "2-digit" });
}

function renderPcsActivasBadge(pcs) {
    document.getElementById("pcs-activas-badge").textContent =
        `● ${pcs.length} PC${pcs.length !== 1 ? "s" : ""} activa${pcs.length !== 1 ? "s" : ""}`;
}

function renderResumen(r) {
    const bar = document.getElementById("resumen-bar");
    bar.innerHTML = [
        { val: r.total_sesiones ?? 0, lbl: "Sesiones hoy" },
        { val: r.estudiantes_unicos ?? 0, lbl: "Estudiantes únicos" },
        { val: r.pcs_usadas ?? 0, lbl: "PCs usadas" },
        { val: r.minutos_promedio ? `${r.minutos_promedio} min` : "—", lbl: "Promedio / sesión" },
    ].map(item => `
        <div class="resumen-item">
            <div class="val">${item.val}</div>
            <div class="lbl">${item.lbl}</div>
        </div>
    `).join("");
}

function filtrarLocal() {
    const carnet = document.getElementById("filter-carnet").value.toLowerCase();
    const facultad = document.getElementById("filter-facultad").value;
    const filtered = todosLosDatos.filter(s =>
        (!carnet || s.carnet.toLowerCase().includes(carnet) || (s.nombre || "").toLowerCase().includes(carnet)) &&
        (!facultad || s.facultad === facultad)
    );
    renderTabla(filtered);
}

function exportarCSV() {
    const fecha = document.getElementById("filter-fecha").value || "hoy";
    const headers = ["Carnet", "Nombre", "Carrera", "Facultad", "PC", "Hora inicio", "Hora fin", "Minutos"];
    const rows = todosLosDatos.map(s => [
        s.carnet, s.nombre || "", s.carrera || "", s.facultad || "",
        s.pc_id, s.hora_inicio, s.hora_fin || "", s.minutos ?? ""
    ]);
    const csv = [headers, ...rows].map(r => r.map(c => `"${c}"`).join(",")).join("\n");
    const blob = new Blob(["﻿" + csv], { type: "text/csv;charset=utf-8;" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `sesiones_${fecha}.csv`;
    a.click();
}

// ── PCs ─────────────────────────────────────────────────────────

async function cargarEstadoPCs() {
    try {
        const pcs = await apiFetch("/estado");
        renderPCsGrid(pcs);
        const activas = pcs.filter(p => p.sesion_activa).length;
        document.getElementById("pcs-activas-badge").textContent =
            `● ${activas} PC${activas !== 1 ? "s" : ""} activa${activas !== 1 ? "s" : ""}`;
    } catch (e) {
        console.error(e);
    }
}

function renderPCsGrid(pcs) {
    const grid = document.getElementById("pcs-grid");
    const noEl = document.getElementById("no-pcs");
    grid.innerHTML = "";
    noEl.classList.toggle("hidden", pcs.length > 0);

    pcs.forEach(pc => {
        const activa = !!pc.sesion_activa;
        const ultimaVez = pc.ultima_actualizacion
            ? new Date(pc.ultima_actualizacion + "Z").toLocaleTimeString("es-GT", { hour: "2-digit", minute: "2-digit" })
            : "—";

        const card = document.createElement("div");
        card.className = "pc-card " + (activa ? "pc-activa" : "pc-libre");
        card.innerHTML = `
            <div class="pc-header">
                <span class="pc-status-dot"></span>
                <span class="pc-nombre">${pc.pc_nombre || pc.pc_id}</span>
                <span class="pc-badge">${activa ? "EN USO" : "LIBRE"}</span>
            </div>
            <div class="pc-id">${pc.pc_id}</div>
            ${activa ? `
                <div class="pc-usuario">
                    <div class="pc-dato"><span>Carnet</span><strong>${pc.carnet || "—"}</strong></div>
                    <div class="pc-dato"><span>Nombre</span><strong>${pc.nombre || "—"}</strong></div>
                    <div class="pc-dato"><span>Desde</span><strong>${pc.hora_inicio ? fmtHora(pc.hora_inicio) : "—"}</strong></div>
                </div>
            ` : `<div class="pc-libre-msg">Disponible</div>`}
            <div class="pc-footer">Última señal: ${ultimaVez}</div>
        `;
        grid.appendChild(card);
    });
}

// ── ESTUDIANTES ─────────────────────────────────────────────────

async function cargarEstudiantes() {
    try {
        todosEstudiantes = await apiFetch("/estudiantes");
        renderEstudiantes(todosEstudiantes);
    } catch (e) {
        console.error(e);
    }
}

function filtrarEstudiantes() {
    const q = document.getElementById("filter-est").value.toLowerCase();
    const filtrados = todosEstudiantes.filter(e =>
        e.carnet.toLowerCase().includes(q) ||
        (e.nombre || "").toLowerCase().includes(q) ||
        (e.carrera || "").toLowerCase().includes(q)
    );
    renderEstudiantes(filtrados);
}

function renderEstudiantes(datos) {
    const tbody = document.getElementById("tabla-est-body");
    const noEl = document.getElementById("no-est");
    tbody.innerHTML = "";
    noEl.classList.toggle("hidden", datos.length > 0);

    datos.forEach(e => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td>${e.carnet}</td>
            <td>${e.nombre}</td>
            <td>${e.carrera || "—"}</td>
            <td>${e.facultad || "—"}</td>
            <td>${e.departamento || "—"}</td>
            <td>${e.sexo || "—"}</td>
            <td>${e.fecha_registro || "—"}</td>
        `;
        tbody.appendChild(tr);
    });
}

// ── Init ────────────────────────────────────────────────────────

window.addEventListener("load", () => {
    const saved = sessionStorage.getItem("token");
    if (saved) { TOKEN = saved; mostrarPanel(); }
});

document.addEventListener("keydown", e => {
    if (e.key === "Enter" && !document.getElementById("login-screen").classList.contains("hidden")) login();
});
