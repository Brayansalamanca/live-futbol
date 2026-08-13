
   const USUARIO_ACTUAL = "{{ request.user.username }}";
let DATOS_PRENDAS = [];

// ===============================
// FECHA MÍNIMA
// ===============================
function obtenerFechaMinima() {
    let d = new Date();
    d.setDate(d.getDate() + 10);
    return d.toISOString().split('T')[0];
}

// ===============================
// VISOR IMÁGENES
// ===============================
function ampliarImagen(src) {
    document.getElementById('imgGrande').src = src;
    document.getElementById('visorImagen').style.display = 'flex';
}

function cerrarVisor() {
    document.getElementById('visorImagen').style.display = 'none';
}

// ===============================
// CARGAR DATOS
// ===============================
async function cargar() {

    try {

        const res = await fetch(URL_OBTENER_PRENDAS);

        DATOS_PRENDAS = await res.json();

        filtrarCatalogo();

    } catch (e) {

        console.error("Error al cargar datos:", e);

    }
}

// ===============================
// FILTRAR
// ===============================
function filtrarCatalogo() {

    const busqueda = document
        .getElementById('busquedaNombre')
        .value
        .toLowerCase();

    const tallaSel = document
        .getElementById('filtroTalla')
        .value;

    const filtradas = DATOS_PRENDAS.filter(p =>
        p.nombre.toLowerCase().includes(busqueda) &&
        (tallaSel === "" || p.talla === tallaSel)
    );

    renderizarTablas(filtradas);
}

// ===============================
// RENDER TABLAS
// ===============================
function renderizarTablas(prendas) {

    let htmlCat = "";
    let htmlDev = "";
    let htmlAtrasados = "";

    const fechaMinima = obtenerFechaMinima();

    const hoyObj = new Date();
    hoyObj.setHours(0, 0, 0, 0);

    prendas.forEach(p => {

        const hayStock = p.cantidad > 0;
        const estaReservado = p.cantidad_apartada > 0;

        // ===============================
        // BADGES
        // ===============================
        let badgeHtml = "";

        if (hayStock && !estaReservado) {

            badgeHtml = `
                <span class="badge badge-ok">
                    ✅ Disponible
                </span>
            `;

        } else if (hayStock && estaReservado) {

            badgeHtml = `
                <span class="badge badge-warn">
                    ⚠️ Quedan ${p.cantidad}
                </span>
            `;

        } else {

            badgeHtml = `
                <span class="badge badge-fail">
                    🚫 Agotado
                </span>
            `;
        }

        // ===============================
        // TABLA CATÁLOGO
        // ===============================
        htmlCat += `
            <tr>

                <td>
                    <img
                        src="${p.imagen}"
                        onclick="ampliarImagen('${p.imagen}')"
                        class="img-tabla"
                    >
                </td>

                <td style="font-weight:bold;">
                    ${p.nombre}
                </td>

                <td>
                    ${p.talla || '-'}
                </td>

                <td class="stock-ok">
                    ${p.cantidad}
                </td>

                <td class="stock-wait">
                    ${p.cantidad_apartada || 0}
                </td>

                <td class="fecha-info">

                    ${p.reservas.length > 0
                        ? p.reservas.map(r => `
                            <div>
                                ${r.fecha_uso || 'Sin fecha'}
                                (${r.cantidad})
                            </div>
                        `).join('')
                        : '---'
                    }

                </td>

                <td>
                    ${badgeHtml}
                </td>

                <td>

                    <div style="
                        display:flex;
                        gap:5px;
                        justify-content:center;
                    ">

                        ${hayStock
                            ? `
                                <button
                                    onclick="toggleForm('${p.id}')"
                                    style="
                                        background:var(--primary);
                                        color:white;
                                        border:none;
                                        padding:6px 12px;
                                        border-radius:4px;
                                        cursor:pointer;
                                    "
                                >
                                    Apartar
                                </button>
                            `
                            : `
                                <button
                                    disabled
                                    style="
                                        background:#ccc;
                                        color:#666;
                                        border:none;
                                        padding:6px 12px;
                                        border-radius:4px;
                                    "
                                >
                                    Agotado
                                </button>
                            `
                        }

                        ${USUARIO_ACTUAL === 'rosita'
                            ? `
                                <button
                                    onclick="eliminarPrenda('${p.id}')"
                                    style="
                                        background:#e74c3c;
                                        color:white;
                                        border:none;
                                        padding:6px 8px;
                                        border-radius:4px;
                                    "
                                >
                                    🗑️
                                </button>
                            `
                            : ''
                        }

                    </div>

                </td>

            </tr>

            <tr
                id="form-${p.id}"
                class="form-row"
                style="display:none;"
            >

                <td colspan="8">

                    <div class="grid-form">

                        <div>
                            <label>CURSO</label>

                            <input
                                type="text"
                                id="curso-${p.id}"
                                class="input-hibrido"
                            >
                        </div>

                        <div>
                            <label>EVENTO</label>

                            <input
                                type="text"
                                id="evento-${p.id}"
                                class="input-hibrido"
                            >
                        </div>

                        <div>
                            <label>
                                FECHA USO (Min 10 días)
                            </label>

                            <input
                                type="date"
                                id="fecha-${p.id}"
                                min="${fechaMinima}"
                                class="input-hibrido"
                                required
                            >
                        </div>

                        <div>
                            <label>
                                CANT. (Máx ${p.cantidad})
                            </label>

                            <input
                                type="number"
                                id="cant-${p.id}"
                                value="1"
                                min="1"
                                max="${p.cantidad}"
                                class="input-hibrido"
                            >
                        </div>

                        <div style="
                            display:flex;
                            gap:5px;
                            align-items:flex-end;
                        ">

                            <button
                                onclick="confirmar('${p.id}')"
                                style="
                                    background:#27ae60;
                                    color:white;
                                    border:none;
                                    height:35px;
                                    border-radius:4px;
                                    flex:1;
                                "
                            >
                                OK
                            </button>

                            <button
                                onclick="toggleForm('${p.id}')"
                                style="
                                    background:#95a5a6;
                                    color:white;
                                    border:none;
                                    height:35px;
                                    border-radius:4px;
                                    padding:0 10px;
                                "
                            >
                                X
                            </button>

                        </div>

                    </div>

                </td>

            </tr>
        `;

        // ===============================
        // DEVOLUCIONES ADMIN
        // ===============================
        if (
            USUARIO_ACTUAL === 'rosita' &&
            p.reservas.length > 0
        ) {

            p.reservas.forEach(r => {

                let esAtrasado = false;

                if (r.fecha_uso) {

                    const partes = r.fecha_uso.split('/');

                    if (partes.length === 3) {

                        const fechaUsoObj = new Date(
                            partes[2],
                            partes[1] - 1,
                            partes[0]
                        );

                        const fechaLimite = new Date(fechaUsoObj);

                        fechaLimite.setDate(
                            fechaLimite.getDate() + 2
                        );

                        if (hoyObj > fechaLimite) {
                            esAtrasado = true;
                        }
                    }
                }

                const filaDev = `
                    <tr>

                        <td>

                            <img
                                src="${p.imagen}"
                                onclick="ampliarImagen('${p.imagen}')"
                                class="img-tabla"
                                style="
                                    width:40px;
                                    height:40px;
                                "
                            >

                        </td>

                        <td>
                            ${p.nombre}
                        </td>

                        <td style="
                            color:#d35400;
                            font-weight:bold;
                        ">
                            ${r.nombre}
                        </td>

                        <td>
                            ${r.cantidad}
                        </td>

                        <td>
                            ${r.curso || '-'}
                            /
                            ${r.evento || '-'}
                        </td>

                        <td style="
                            color:${esAtrasado ? '#e74c3c' : 'inherit'};
                            font-weight:bold;
                        ">
                            ${r.fecha_uso || 'Sin fecha'}
                        </td>

                        <td>

                            <button
                                onclick="liberarReserva('${r.id}')"
                                style="
                                    background:#27ae60;
                                    color:white;
                                    border:none;
                                    padding:6px 12px;
                                    border-radius:4px;
                                    cursor:pointer;
                                "
                            >
                                Devuelto
                            </button>

                        </td>

                    </tr>
                `;

                if (esAtrasado) {
                    htmlAtrasados += filaDev;
                } else {
                    htmlDev += filaDev;
                }

            });
        }

    });

    // ===============================
    // INSERTAR HTML
    // ===============================
    document.getElementById('tablaCuerpo').innerHTML =
        htmlCat ||
        "<tr><td colspan='8'>No hay prendas disponibles</td></tr>";

    if (USUARIO_ACTUAL === 'rosita') {

        document.getElementById('tablaDevoluciones').innerHTML =
            htmlDev ||
            "<tr><td colspan='7'>Sin entregas pendientes</td></tr>";

        document.getElementById('tablaAtrasados').innerHTML =
            htmlAtrasados ||
            "<tr><td colspan='7'>No hay devoluciones atrasadas 🎉</td></tr>";
    }
}

// ===============================
// TOGGLE FORM
// ===============================
function toggleForm(id) {

    const row = document.getElementById(`form-${id}`);

    row.style.display =
        row.style.display === 'none'
            ? 'table-row'
            : 'none';
}

// ===============================
// APARTAR
// ===============================
async function confirmar(id) {

    const fechaVal =
        document.getElementById(`fecha-${id}`).value;

    const cantVal =
        parseInt(document.getElementById(`cant-${id}`).value);

    const cantMax =
        parseInt(document.getElementById(`cant-${id}`).max);

    if (!fechaVal) {
        return alert("La fecha es obligatoria.");
    }

    const fechaSel = new Date(fechaVal + "T00:00:00");

    const limite = new Date();

    limite.setDate(limite.getDate() + 9);

    limite.setHours(0, 0, 0, 0);

    if (fechaSel <= limite) {

        return alert(
            "Debes apartar con 10 días de anticipación."
        );
    }

    if (cantVal < 1 || cantVal > cantMax) {

        return alert("Cantidad inválida.");
    }

    const payload = {

        nombre: USUARIO_ACTUAL,

        curso:
            document.getElementById(`curso-${id}`).value,

        evento:
            document.getElementById(`evento-${id}`).value,

        fecha: fechaVal,

        cantidad_alquilada: cantVal,

        accion: 'apartar'
    };

    const res = await fetch(`/api/apartar-prenda/${id}/`, {

        method: "POST",

        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": "{{ csrf_token }}"
        },

        body: JSON.stringify(payload)
    });

    if (res.ok) {

        cargar();

        alert("Apartado con éxito.");

    } else {

        const errorData = await res.json();

        alert(errorData.message || "Error");
    }
}

// ===============================
// DEVOLVER RESERVA INDIVIDUAL
// ===============================
async function liberarReserva(reservaId) {

    if (
        !confirm(
            "¿Confirmar devolución de esta reserva?"
        )
    ) {
        return;
    }

    const res = await fetch(
        `/liberar-reserva/${reservaId}/`,
        {
            method: "POST",

            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": "{{ csrf_token }}"
            }
        }
    );

    const data = await res.json();

    if (res.ok) {

        cargar();

    } else {

        alert(data.message || "Error");
    }
}

// ===============================
// ELIMINAR PRENDA
// ===============================
async function eliminarPrenda(id) {

    if (
        !confirm("¿Eliminar prenda definitivamente?")
    ) {
        return;
    }

    const res = await fetch(
        `/api/eliminar-prenda/${id}/`,
        {
            method: "POST",

            headers: {
                "X-CSRFToken": "{{ csrf_token }}"
            }
        }
    );

    if (res.ok) {
        cargar();
    }
}

// ===============================
// INIT
// ===============================
document.addEventListener(
    "DOMContentLoaded",
    cargar
);