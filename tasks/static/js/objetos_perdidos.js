const API_URLS = {

    hallazgos: '/api/obtener-objetos/',
    solicitudes: '/api/obtener-solicitudes/',

    guardarH: '/api/guardar-objeto/',
    guardarS: '/api/guardar-solicitud/',

    eliminarObjeto: '/api/eliminar-objeto/',
    eliminarSolicitud: '/api/eliminar-solicitud/'
};

// =========================================
// CARGAR DATOS
// =========================================

async function fetchDataTable() {

    try {

        const [resH, resS] = await Promise.all([

            fetch(API_URLS.hallazgos + '?t=' + Date.now()),
            fetch(API_URLS.solicitudes + '?t=' + Date.now())

        ]);

        const hallazgos = await resH.json();
        const solicitudes = await resS.json();

        renderHallazgos(hallazgos);
        renderSolicitudes(solicitudes);

        document.getElementById('countH').innerText = hallazgos.length;
        document.getElementById('countS').innerText = solicitudes.length;

    } catch(error) {

        console.error(error);
    }
}

// =========================================
// RENDER HALLAZGOS
// =========================================

function renderHallazgos(data) {

    const tabla = document.getElementById('tablaHallazgos');

    if(!data.length){

        tabla.innerHTML = `
            <tr>
                <td colspan="4" style="
                    padding:40px;
                    text-align:center;
                    color:#94a3b8;
                ">
                    No hay objetos registrados
                </td>
            </tr>
        `;

        return;
    }

    tabla.innerHTML = '';

    data.forEach(h => {

        tabla.innerHTML += `

            <tr style="
                border-bottom:1px solid #e2e8f0;
            ">

                <td style="padding:15px;">
                    <strong>${h.tipo}</strong>
                </td>

                <td style="padding:15px;">
                    ${h.descripcion}
                </td>

                <td style="padding:15px;">
                    📍 ${h.nombre}
                </td>

                <td style="padding:15px;">

                    <button
                        onclick="resolverItem('${h.id}', 'hallazgo')"
                        style="
                            background:#10b981;
                            color:white;
                            border:none;
                            padding:10px 15px;
                            border-radius:10px;
                            cursor:pointer;
                            font-weight:bold;
                        "
                    >
                        ✅ Entregar
                    </button>

                </td>

            </tr>
        `;
    });
}
// =========================================
// RENDER SOLICITUDES
// =========================================

function renderSolicitudes(data) {

    const tabla = document.getElementById('tablaSolicitudes');

    if(!data.length){

        tabla.innerHTML = `
            <tr>
                <td colspan="4" style="
                    padding:40px;
                    text-align:center;
                    color:#94a3b8;
                ">
                    No hay solicitudes activas
                </td>
            </tr>
        `;

        return;
    }

    tabla.innerHTML = '';

    data.forEach(s => {

        tabla.innerHTML += `

            <tr style="
                border-bottom:1px solid #e2e8f0;
            ">

                <td style="padding:15px;">
                    <strong>${s.nombre}</strong>
                </td>

                <td style="padding:15px;">
                    ${s.curso}
                </td>

                <td style="padding:15px;">
                    ${s.descripcion}
                </td>

                <td style="padding:15px;">

                    <button
                        onclick="resolverItem('${s.id}', 'solicitud')"
                        style="
                            background:#9333ea;
                            color:white;
                            border:none;
                            padding:10px 15px;
                            border-radius:10px;
                            cursor:pointer;
                            font-weight:bold;
                        "
                    >
                        ❌ Cerrar
                    </button>

                </td>

            </tr>
        `;
    });
}

// =========================================
// GUARDAR HALLAZGO
// =========================================

async function guardarHallazgo() {

    const data = {

    nombre: document.getElementById('h_lugar').value,
    tipo: document.getElementById('h_tipo').value,
    dif: document.getElementById('h_color').value
};

    try {

        await fetch(API_URLS.guardarH, {

            method:'POST',

            headers:{
                'Content-Type':'application/json',
                'X-CSRFToken':'{{ csrf_token }}'
            },

            body: JSON.stringify(data)
        });

        document.getElementById('formHallazgo').reset();

        fetchDataTable();

    } catch(error){

        console.error(error);
    }
}

// =========================================
// GUARDAR SOLICITUD
// =========================================

async function guardarSolicitud() {

    const data = {

    nombre: document.getElementById('s_nombre').value,
    curso: document.getElementById('s_curso').value,
    descripcion: document.getElementById('s_prenda').value
};

    try {

        await fetch(API_URLS.guardarS, {

            method:'POST',

            headers:{
                'Content-Type':'application/json',
                'X-CSRFToken':'{{ csrf_token }}'
            },

            body: JSON.stringify(data)
        });

        document.getElementById('formSolicitud').reset();

        fetchDataTable();

    } catch(error){

        console.error(error);
    }
}

// =========================================
// ELIMINAR
// =========================================

async function resolverItem(id, tipo) {

    if(!confirm('¿Seguro que deseas eliminar este registro?')) return;

    let url = '';

    if(tipo === 'hallazgo'){

        url = API_URLS.eliminarObjeto + id + '/';

    } else {

        url = API_URLS.eliminarSolicitud + id + '/';
    }

    try {

        const response = await fetch(url, {

            method:'DELETE',

            headers:{
                'X-CSRFToken':'{{ csrf_token }}'
            }
        });

        if(response.ok){

            fetchDataTable();

        } else {

            alert('No se pudo eliminar.');
        }

    } catch(error){

        console.error(error);
    }
}

// =========================================
// FILTRO
// =========================================

function filtrarTablas() {

    const texto = document
        .getElementById('inputBusqueda')
        .value
        .toLowerCase();

    const filas = document.querySelectorAll('tbody tr');

    filas.forEach(fila => {

        fila.style.display =
            fila.innerText.toLowerCase().includes(texto)
            ? ''
            : 'none';
    });
}

// =========================================
// AUTO REFRESH
// =========================================

setInterval(fetchDataTable, 3000);

// =========================================
// INICIO
// =========================================

fetchDataTable();
