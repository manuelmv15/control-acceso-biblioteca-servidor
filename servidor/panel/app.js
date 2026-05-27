let TOKEN = null;
let todosLosDatos = [];
let refreshInterval = null;

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
    refreshInterval = setInterval(cargarDatos, 30000);
}

async function apiFetch(url) {
    const res = await fetch(url, { headers: { Authorization: `Bearer ${TOKEN}` } });
    if (res.status === 401) { logout(); throw new Error("Sesión expirada"); }
    return res.json();
}

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
        renderPcsActivas(pcsActivas);
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
        const abierta = !s.hora_fin;
        const duracion = s.minutos != null
            ? `${Math.floor(s.minutos / 60)}h ${s.minutos % 60}m`
            : "—";
        const tr = document.createElement("tr");
        if (abierta) tr.classList.add("sesion-abierta");
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

function renderPcsActivas(pcs) {
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

// Auto-login si hay token en sesión
window.addEventListener("load", () => {
    const saved = sessionStorage.getItem("token");
    if (saved) { TOKEN = saved; mostrarPanel(); }
});

document.addEventListener("keydown", e => {
    if (e.key === "Enter" && document.getElementById("login-screen").style.display !== "none") login();
});
