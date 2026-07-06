/**
 * Live Futbol - Módulo de Control de Préstamos e Inventario
 * Sincronización automática optimizada con intervalos extendidos para evitar lag en el servidor
 */

let registros = [];
let balonesInventario = []; 
let listaVetados = []; 
let objetoActual = "";
let gradoActual = "";
let letraActual = "";

const ENDPOINTS = {
    obtenerEntregas: "/api/obtener-entregas/",
    guardarEntrega: "/api/guardar-entrega/",
    eliminarEntrega: "/api/eliminar-entrega/",
    editarEntrega: "/api/editar-entrega/",
    borrarAntiguos: "/api/borrar-registros-antiguos/",
    obtenerBajas: "/api/obtener-bajas/", 
    obtenerBalonesAlmacen: "/api/obtener-balones-disponibles/", 
    registrarNuevoBalon: "/api/registrar-nuevo-balon/"
};

// ==========================================================================
// 1. CONTROL DE VISTAS DINÁMICAS (SISTEMA DE PESTAÑAS)
// ==========================================================================
function cambiarVista(modulo) {
    const moduloRenta = document.getElementById("seccion-modulo-renta");
    const moduloAlmacen = document.getElementById("seccion-modulo-almacen");
    const btnRenta = document.getElementById("btn-vista-renta");
    const btnAlmacen = document.getElementById("btn-vista-almacen");

    if (modulo === 'renta') {
        moduloRenta.style.display = "block";
        moduloAlmacen.style.display = "none";
        btnRenta.className = "btn btn-primary";
        btnAlmacen.className = "btn btn-tab-inactivo";
    } else if (modulo === 'almacen') {
        moduloRenta.style.display = "none";
        moduloAlmacen.style.display = "block";
        btnAlmacen.className = "btn btn-primary";
        btnRenta.className = "btn btn-tab-inactivo";
        dibujarPanelInventarioRapido();
    }
}

// ==========================================================================
// 2. ESCANEO NFC DEL CELULAR O TAG DEL ESTUDIANTE (PASO 1)
// ==========================================================================
async function iniciarEscaneoNFCPersona() {
    const estadoTxt = document.getElementById("nfc-persona-estado");
    const inputNombre = document.getElementById("textoVoz");
    
    if (!('NDEFReader' in window)) {
        estadoTxt.innerText = "❌ NFC no soportado en este dispositivo/navegador.";
        estadoTxt.style.color = "var(--danger)";
        return;
    }

    try {
        const ndef = new NDEFReader();
        await ndef.scan();
        estadoTxt.innerText = "📡 Buscando... Acerca la etiqueta o celular del alumno.";
        estadoTxt.style.color = "var(--warning)";

        ndef.onreading = event => {
            const idDigital = event.serialNumber; 
            
            // Asigna el ID único del tag o celular directamente al estudiante
            inputNombre.value = idDigital;
            estadoTxt.innerText = `✅ Alumno Vinculado: ${idDigital}`;
            estadoTxt.style.color = "var(--success)";
            
            console.log("Estudiante detectado mediante NFC con código: " + idDigital);
        };

    } catch (error) {
        estadoTxt.innerText = "❌ Error al activar lector NFC.";
        estadoTxt.style.color = "var(--danger)";
    }
}

// ==========================================================================
// 3. CARGA Y GESTIÓN DINÁMICA DEL INVENTARIO (IDs Y MARCAS)
// ==========================================================================
async function cargarBalonesDesdeAPI() {
    try {
        const res = await fetch(`${ENDPOINTS.obtenerBalonesAlmacen}?t=${Date.now()}`);
        if (!res.ok) return;
        
        balonesInventario = await res.json(); 
        
        actualizarContadoresStock();
        actualizarSelectorBalones();
        dibujarPanelInventarioRapido();
    } catch (e) {
        console.warn("Error al conectar con la API de inventario.");
    }
}
function actualizarSelectorBalones() {
    const selectorID = document.getElementById("idObjetoSelect");
    if (!selectorID) return;

    const valorPrevio = selectorID.value;
    selectorID.innerHTML = '<option value="">-- Selecciona Unidad (ID + Marca) --</option>';

    if (!objetoActual) return;

    // Filtra los balones del inventario por la categoría seleccionada
    const balonesFiltrados = balonesInventario.filter(b => b.tipo === objetoActual);

    balonesFiltrados.forEach(balon => {
        // 1. OBTENER EL ID DEL BALÓN (Soporta id_unico o codigo_nfc)
        const idBalonInventario = balon.id_unico || balon.codigo_nfc;
        
        if (!idBalonInventario) return; // Si no hay ID, saltamos este elemento

        // 2. VERIFICAR SI ESTÁ PRESTADO CON FILTRO PARA EVITAR REGISTROS VACÍOS (TU INTUICIÓN)
        const estaPrestado = registros.some(r => {
            // Evaluamos contra lo que devuelva la API de entregas (id_unico o marca)
            const idRegistro = r.id_unico || r.marca;
            
            // --- REGLA DE EXCLUSIÓN PARA EVITAR FALSOS NEGATIVOS ---
            // Si el registro de la base de datos es viejo o está vacío ("Sin ID", null, ""), 
            // NO permitimos que descuente el balón ni que sume al contador.
            if (!idRegistro || idRegistro === "Sin ID" || String(idRegistro).trim() === "") {
                return false; 
            }

            // Comparamos los IDs válidos limpiando espacios accidentales
            return String(idRegistro).trim() === String(idBalonInventario).trim();
        });
        
        // 3. VERIFICAR EL ESTADO (Soporta 'estado !== Dañado' o 'disponible === true')
        const esValido = (balon.estado !== "Dañado") && (balon.disponible !== false);

        // Solo lo agregamos al selector si NO está prestado y el balón está apto/disponible
        if (!estaPrestado && esValido) {
            let marcaBalon = balon.marca || balon.nombre_balon || 'Sin Marca';
            let textoOpcion = `${idBalonInventario} - (${marcaBalon})`;
            
            let option = new Option(textoOpcion, idBalonInventario);
            selectorID.add(option);
        }
    });

    if (valorPrevio && [...selectorID.options].some(o => o.value === valorPrevio)) {
        selectorID.value = valorPrevio;
    }
}

async function agregarBalonAlInventario() {
    const tipo = document.getElementById("nuevoTipoSelect").value;
    const idUnico = document.getElementById("nuevoIdInput").value.trim();
    const marca = document.getElementById("nuevaMarcaInput").value.trim();

    if (!idUnico || !marca) {
        alert("⚠️ Completa el ID único y la marca/número del elemento.");
        return;
    }

    const tokenCsrf = window.CSRF_TOKEN || document.querySelector('[name=csrfmiddlewaretoken]')?.value;

    try {
        const res = await fetch(ENDPOINTS.registrarNuevoBalon, {
            method: "POST",
            headers: { "Content-Type": "application/json", "X-CSRFToken": tokenCsrf },
            body: JSON.stringify({ tipo, id_unico: idUnico, marca, estado: "Excelente" })
        });

        if (res.ok) {
            document.getElementById("nuevoIdInput").value = "";
            document.getElementById("nuevaMarcaInput").value = "";
            await cargarBalonesDesdeAPI();
            alert("✅ Guardado en el stock del almacén.");
        } else {
            alert("❌ Error al guardar el balón.");
        }
    } catch (e) {
        alert("❌ Error de comunicación.");
    }
}
function dibujarPanelInventarioRapido() {
    const contenedor = document.getElementById("listaInventarioRapido");
    if (!contenedor) return;

    if (balonesInventario.length === 0) {
        contenedor.innerHTML = '<p style="font-size:13px; color:var(--text-soft); text-align:center;">No hay existencias en el inventario.</p>';
        return;
    }

    let html = '<ul style="list-style:none; padding:0; margin:0; font-size:13px;">';
    
    balonesInventario.forEach(b => {
        const prestado = registros.some(r => r.id_unico === b.id_unico) ? "🔴 Prestado" : "🟢 En Bodega";
        
        // Un solo bloque forEach que incluye los botones
        html += `
            <li style="padding:10px 0; border-bottom:1px solid #2a2a3e; display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <strong>${b.id_unico}</strong> - ${b.marca} 
                    <br><small style="color:var(--text-soft)">${b.tipo}</small> | 
                    <span style="font-weight:700; font-size:11px;">${prestado}</span>
                </div>
                
                <div style="display: flex; gap: 8px;">
                    <button type="button" class="btn-accion" onclick="editarBalon(${b.id}, '${b.id_unico}', '${b.marca}')" title="Editar">✏️</button>
                    <button type="button" class="btn-accion" onclick="eliminarBalon(${b.id})" title="Eliminar" style="color:red;">🗑️</button>
                </div>
            </li>
        `;
    });
    
    html += '</ul>';
    contenedor.innerHTML = html;
}
async function eliminarBalon(id) {
    if (!confirm("¿Seguro que deseas eliminar este balón?")) return;
    const res = await fetch(`/api/eliminar-balon/${id}/`, { method: "POST", headers: { "X-CSRFToken": window.CSRF_TOKEN } });
    if (res.ok) cargarBalonesDesdeAPI();
}

async function editarBalon(id) {
    const nuevoId = prompt("Nuevo ID:");
    if (!nuevoId) return;
    
    await fetch(`/api/editar-balon/${id}/`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-CSRFToken": window.CSRF_TOKEN },
        body: JSON.stringify({ id_unico: nuevoId })
    });
    cargarBalonesDesdeAPI();
}



// ==========================================================================
// 4. PROCESAMIENTO Y VALIDACIÓN DE LA RENTA
// ==========================================================================
async function cargarVetadosDesdeAPI() {
    try {
        const res = await fetch(`${ENDPOINTS.obtenerBajas}?t=${Date.now()}`);
        if (!res.ok) return;
        const datos = await res.json();
        listaVetados = datos.map(v => (typeof v === 'string' ? v.toLowerCase() : (v.nombre || v.estudiante || "").toLowerCase()));
    } catch (e) { console.warn("Error al cargar lista de vetados."); }
}

function actualizarContadoresStock() {
    const categorias = ["Balón Fútbol", "Balón Básquet", "Balón Volley"];
    
    // Función para limpiar texto y comparar sin problemas
    const limpiar = (txt) => txt ? txt.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase().trim() : "";

    categorias.forEach(tipo => {
        // Normalizamos el tipo que buscamos
        const tipoLimpio = limpiar(tipo);

        let totalExistencias = balonesInventario.filter(b => 
            limpiar(b.tipo) === tipoLimpio && b.estado !== "Dañado"
        ).length;

        let prestados = registros.filter(r => 
            limpiar(r.objeto || r.balon) === tipoLimpio
        ).length;

        let disponibles = totalExistencias - prestados;
        
        let el = document.getElementById(`stock-${tipo}`);
        if (el) {
            el.innerText = `${disponibles >= 0 ? disponibles : 0} disp`;
        }
    });
}

async function registrarEnNube() {
    const nombreInput = document.getElementById("textoVoz").value.trim();
    const lugarInput = document.getElementById("lugarSelect").value;
    const idUnicoInput = document.getElementById("idObjetoSelect").value;

    // Si el campo contiene un UID numérico largo leído por NFC, el flujo omite la selección de curso obligatorio
    const esIdNfcLargo = nombreInput.length > 6 && !isNaN(nombreInput);
    const cursoCompleto = (gradoActual || letraActual) ? (gradoActual + (letraActual || "")) : "NFC Estudiante";

    if (!nombreInput || !objetoActual || !idUnicoInput) {
        alert("⚠️ Datos incompletos: Faltan campos obligatorios (Estudiante, Tipo de Objeto e ID del Balón).");
        return;
    }

    if (!esIdNfcLargo && !gradoActual) {
        alert("⚠️ Por favor selecciona el Curso Responsable del estudiante.");
        return;
    }

    if (listaVetados.includes(nombreInput.toLowerCase())) {
        alert("❌ El estudiante se encuentra vetado o suspendido en el sistema de bajas.");
        return;
    }

    const tokenCsrf = window.CSRF_TOKEN || document.querySelector('[name=csrfmiddlewaretoken]')?.value;

    const datos = {
        recibido_por: nombreInput,
        curso: cursoCompleto,
        balon: objetoActual,
        id_unico: idUnicoInput, 
        lugar: lugarInput
    };

    try {
        const res = await fetch(ENDPOINTS.guardarEntrega, {
            method: "POST",
            headers: { "Content-Type": "application/json", "X-CSRFToken": tokenCsrf },
            body: JSON.stringify(datos)
        });

        if (res.ok) {
            resetearFormulario();
            await cargarDatos();
            await cargarBalonesDesdeAPI();
        } else {
            alert("❌ No se pudo registrar la renta. Verifica los datos.");
        }
    } catch (error) { alert("❌ Error de red."); }
}

// ==========================================================================
// 5. RENDERIZADO DE TABLAS Y VENCIMIENTOS
// ==========================================================================
function dibujar() {
    let html = "";
    const filter = document.getElementById("buscador").value.toLowerCase();
    document.getElementById("tablaVencidos").innerHTML = "";

    if (!registros || registros.length === 0) {
        document.getElementById("tabla").innerHTML = "<tr><td colspan='7' style='text-align:center;'>No hay préstamos activos.</td></tr>";
        return;
    }

    registros.forEach((r) => {
        const nombre = r.nombre || r.recibido_por || "---";
        const objeto = r.objeto || r.balon || "---";
        const idUnico = r.id_unico || r.marca || "Sin ID";
        const curso = r.curso || "N/A";
        const lugar = r.lugar || "Cancha";
        const id = r.id || r._id;

        if ((nombre + curso + objeto + idUnico).toLowerCase().includes(filter)) {
            let fechaTexto = "Pendiente", venceTexto = "Pendiente", estado = "✅ Activo", isVencido = false, retrasoMinutos = 0;

            if (r.fecha) {
                const d = new Date(r.fecha);
                if (!isNaN(d.getTime())) {
                    fechaTexto = d.toLocaleTimeString("es-CO", { hour: "2-digit", minute: "2-digit" });
                    const vencimiento = obtenerSiguienteDescanso(d);
                    venceTexto = vencimiento.toLocaleTimeString("es-CO", { hour: "2-digit", minute: "2-digit" });
                    const ahora = new Date();

                    if (ahora > vencimiento) {
                        isVencido = true;
                        estado = "⛔ Retrasado";
                        retrasoMinutos = Math.floor((ahora - vencimiento) / (1000 * 60));
                    }
                }
            }

            html += `
            <tr>
                <td><strong>${nombre}</strong><br><small style="color:var(--text-soft)">${curso}</small></td>
                <td><span style="color:var(--primary); font-weight:bold;">${objeto}</span><br><small class="badge-stock" style="background:var(--bg-soft); color:var(--primary); margin-top:2px;">${idUnico}</small></td>
                <td>${lugar}</td>
                <td>${fechaTexto}</td>
                <td>${venceTexto}</td>
                <td style="color:${isVencido ? 'var(--danger)' : 'var(--success)'}; font-weight:bold;">${estado}</td>
                <td>
                    <button class="btn-accion" onclick="editarEntrega('${id}', '${nombre.replace(/'/g, "\\'")}', '${curso}', '${objeto}', '${lugar}')">✏️</button>
                    <button class="btn-accion" onclick="marcarEntregado('${id}')">✅</button>
                </td>
            </tr>`;

            if (isVencido) {
                document.getElementById("tablaVencidos").insertAdjacentHTML("beforeend", `
                    <tr>
                        <td><strong>${nombre}</strong><br><small>${curso}</small></td>
                        <td>${objeto} (${idUnico})</td>
                        <td>${fechaTexto}</td>
                        <td>${venceTexto}</td>
                        <td style="color:var(--danger); font-weight:bold;">${retrasoMinutos} min</td>
                    </tr>`);
            }
        }
    });

    document.getElementById("tabla").innerHTML = html || "<tr><td colspan='7' style='text-align:center;'>Sin resultados</td></tr>";
}

async function cargarDatos() {
    try {
        const url = `${ENDPOINTS.obtenerEntregas}?t=${Date.now()}`;
        const res = await fetch(url);
        
        // Si el servidor responde con un error (404, 500), res.ok será false
        if (!res.ok) {
            console.error("Error en la respuesta del servidor:", res.status, await res.text());
            return;
        }
        
        registros = await res.json();
        dibujar();
        actualizarContadoresStock();
        actualizarSelectorBalones();
        
    } catch (e) {
        // Aquí verás el error real en la consola, no solo el aviso genérico
        console.error("Fallo crítico en cargarDatos:", e);
    }
}

async function marcarEntregado(id) {
    if (!confirm("¿Confirmas la devolución física de la unidad?")) return;
    const tokenCsrf = window.CSRF_TOKEN || document.querySelector('[name=csrfmiddlewaretoken]')?.value;
    try {
        const res = await fetch(`${ENDPOINTS.eliminarEntrega}${id}/`, {
            method: "POST",
            headers: { "X-CSRFToken": tokenCsrf }
        });
        if (res.ok) {
            await cargarDatos();
            await cargarBalonesDesdeAPI();
        }
    } catch (e) { alert("Error al registrar entrega."); }
}

async function editarEntrega(id, nombre, curso, objeto, lugar) {
    const newNombre = prompt("Editar nombre:", nombre);
    if (newNombre === null) return; // Si cancela, salimos
    
    const newCurso = prompt("Editar curso:", curso);
    if (newCurso === null) return;
    
    const newObjeto = prompt("Editar objeto:", objeto);
    if (newObjeto === null) return;
    
    const newLugar = prompt("Editar lugar:", lugar);
    if (newLugar === null) return;

    const tokenCsrf = window.CSRF_TOKEN || document.querySelector('[name=csrfmiddlewaretoken]')?.value;
    
    try {
        const res = await fetch(`${ENDPOINTS.editarEntrega}${id}/`, {
            method: "POST",
            headers: { 
                "Content-Type": "application/json", 
                "X-CSRFToken": tokenCsrf 
            },
            body: JSON.stringify({ 
                nombre: newNombre, 
                curso: newCurso, 
                objeto: newObjeto, 
                lugar: newLugar 
            })
        });

        if (res.ok) {
            console.log("Actualización exitosa");
            await cargarDatos(); // Refrescamos la tabla
        } else {
            const err = await res.json();
            alert("Error al guardar: " + (err.message || "Respuesta del servidor no válida"));
        }
    } catch (e) { 
        console.error("Error en fetch:", e);
        alert("Error de conexión."); 
    }
}

async function borrarNoHoy() {
    if (!confirm("⚠️ ¿Eliminar registros obsoletos de días anteriores?")) return;
    const tokenCsrf = window.CSRF_TOKEN || document.querySelector('[name=csrfmiddlewaretoken]')?.value;
    try {
        const res = await fetch(ENDPOINTS.borrarAntiguos, {
    method: "POST",
    headers: {
        "X-CSRFToken": tokenCsrf
    }
});

console.log(res.status);

const texto = await res.text();
console.log(texto);
        if (res.ok) { await cargarDatos(); await cargarBalonesDesdeAPI(); }
    } catch (e) { alert("Error."); }
}

// ==========================================================================
// 6. CONTROLADORES DE ELEMENTOS DE INTERFAZ E INTERMITENCIAS
// ==========================================================================
function seleccionarObjeto(btn, obj) {
    objetoActual = obj;
    document.querySelectorAll(".btn-objeto").forEach(b => b.classList.remove("activo"));
    btn.classList.add("activo");
    actualizarSelectorBalones(); 
}

function seleccionarGrado(btn, grado) {
    gradoActual = grado;
    document.querySelectorAll("#gradosContenedor .btn-curso").forEach(b => b.classList.remove("activo"));
    btn.classList.add("activo");
    generarLetras(grado);
}

function seleccionarLetra(btn, letra) {
    letraActual = letra;
    // Ahora busca y limpia específicamente los botones con la clase .btn-letra
    document.querySelectorAll("#letrasContenedor .btn-letra").forEach(b => b.classList.remove("activo"));
    btn.classList.add("activo");
}

function generarLetras(grado) {
    let letras = ["A", "B", "C", "D", "E"]; // Lista base por defecto

    // Aplicamos las reglas específicas para cada grupo de grados
    if ([3, 4, 5].includes(grado)) {
        letras = ["A", "B", "C", "D"];       // Hasta la D para 3°, 4° y 5°
    } 
    else if ([6, 7, 8].includes(grado)) {
        letras = ["A", "B", "C", "D", "E"];  // Hasta la E para 6°, 7° y 8°
    } 
    else if ([9, 10].includes(grado)) {
        letras = ["A", "B", "C", "D"];       // Hasta la D para 9° y 10°
    } 
    else if (grado === 11) {
        letras = ["A", "B", "C"];            // Hasta la C para 11°
    }

    let html = "";
    
    // El ciclo recorre exactamente el tamaño de la lista asignada sin romper nada
    for (let i = 0; i < letras.length; i++) {
        html += `<button class="btn-letra" onclick="seleccionarLetra(this, '${letras[i]}')">${letras[i]}</button>`;
    }
    
    document.getElementById("letrasContenedor").innerHTML = html;
    letraActual = "";
}

function obtenerPeriodoActual(fecha) {
    const periodoData = [
        { start: '08:00', end: '09:40', grades: [6,7,8], label: 'Seniors' },
        { start: '10:00', end: '10:50', grades: [3,4,5], label: 'Teens' },
        { start: '10:51', end: '11:45', grades: [9,10,11], label: 'Masters' },
        { start: '11:46', end: '12:40', grades: [6,7,8], label: 'Seniors' },
        { start: '12:41', end: '13:35', grades: [3,4,5], label: 'Teens' },
        { start: '13:36', end: '14:15', grades: [9,10,11], label: 'Masters' }
    ];
    const minutos = fecha.getHours() * 60 + fecha.getMinutes();
    for (const p of periodoData) {
        const [hs, ms] = p.start.split(':').map(Number);
        const [he, me] = p.end.split(':').map(Number);
        if (minutos >= (hs * 60 + ms) && minutos < (he * 60 + me)) return p;
    }
    return null; // Aquí termina la función limpiamente
}

function cargarBotonesCursos() {
    const now = new Date();
    const periodo = obtenerPeriodoActual(now);
    let buttons = [6,7,8,3,4,5,9,10,11];
    let label = "Sin periodo activo (Descanso)";

    if (periodo) {
        label = `${periodo.label} (${periodo.start} - ${periodo.end})`;
        buttons = periodo.grades;
    }

    // 1. Primero se pone el texto del periodo
    document.getElementById("gradosContenedor").innerHTML = `<div style="margin-bottom:8px; color:var(--warning); font-weight:bold; font-size:13px;">${label}</div>`;
    
    // 2. AQUÍ METEMOS EL SALTO DE LÍNEA para que los botones bajen y no queden pegados
    document.getElementById("gradosContenedor").innerHTML += `<br>`;

    // 3. Luego se dibujan todos los botones abajo del salto
    buttons.forEach((g) => {
        document.getElementById("gradosContenedor").innerHTML += `<button class="btn-curso" onclick="seleccionarGrado(this, ${g})">${g}°</button>`;
    });
}

function cargarBotonesCursos() {
    const now = new Date();
    const periodo = obtenerPeriodoActual(now);
    let buttons = [6,7,8,3,4,5,9,10,11];
    let label = "Sin periodo activo (Descanso)";

    if (periodo) {
        label = `${periodo.label} (${periodo.start} - ${periodo.end})`;
        buttons = periodo.grades;
    }

    // Cambiamos el margin-bottom de 8px a 20px para generar el espacio perfecto
    document.getElementById("gradosContenedor").innerHTML = `<div style="margin-bottom: 20px; width: 100%; color: var(--warning); font-weight: bold; font-size: 13px;">${label}</div>`;
    
    buttons.forEach((g) => {
        document.getElementById("gradosContenedor").innerHTML += `<button class="btn-curso" onclick="seleccionarGrado(this, ${g})">${g}°</button>`;
    });
}


function obtenerSiguienteDescanso(f) {
    const next = new Date(f); 
    next.setMinutes(next.getMinutes() + 50); 
    return next; 
}

function resetearFormulario() {
    document.getElementById("textoVoz").value = "";
    document.getElementById("nfc-persona-estado").innerText = "";
    document.querySelectorAll(".btn-objeto, .btn-curso").forEach(b => b.classList.remove("activo"));
    objetoActual = ""; gradoActual = ""; letraActual = "";
    document.getElementById("letrasContenedor").innerHTML = "";
    document.getElementById("idObjetoSelect").innerHTML = '<option value="">-- Selecciona Unidad (ID + Marca) --</option>';
}

// ==========================================================================
// 7. ENLACE AUTOMÁTICO OPTIMIZADO (INTERVALOS AMPLIADOS PARA REDUCIR LAG)
// ==========================================================================
document.addEventListener("DOMContentLoaded", () => {
    cargarBotonesCursos();
    cargarVetadosDesdeAPI(); 
    cargarBalonesDesdeAPI();
    cargarDatos();
    
    // Sincronización en tiempo real (cada 2 segundos)
    setInterval(() => {
        cargarDatos();
        cargarBalonesDesdeAPI();
    }, 4000); 

    // Lista de vetados puede ser más lenta porque no cambia cada segundo
    setInterval(cargarVetadosDesdeAPI, 50000); 
});