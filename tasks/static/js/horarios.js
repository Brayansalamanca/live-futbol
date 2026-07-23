/* ==========================================================
   HORARIOS MKS PLATFORM
   ==========================================================
   PARTE 1
   ----------------------------------------------------------
   ✓ Configuración
   ✓ Estado global
   ✓ Helpers
   ✓ Inicialización
   ✓ Registro de eventos
==========================================================*/

/* ==========================================================
CONFIGURACIÓN
========================================================== */

const CONFIG = {

    dias: [

        "Lunes",
        "Martes",
        "Miércoles",
        "Jueves",
        "Viernes",
        "Sábado",
        "Domingo"

    ],

    horas: [

        "06:00 - 07:00",
        "07:00 - 08:00",
        "08:00 - 09:00",
        "09:00 - 10:00",
        "10:00 - 11:00",
        "11:00 - 12:00",
        "12:00 - 13:00",
        "13:00 - 14:00",
        "14:00 - 15:00",
        "15:00 - 16:00"

    ],

    endpoints: {

        guardar : "/guardar-bloque/",

        obtener : "/obtener-horario/",

        eliminar : "/eliminar-bloque/"

    }

};

/* ==========================================================
PROFESORES
========================================================== */

const profesores = [

    {

        nombre: "Salamanca Lopez",

        tipo: "Seniors"

    },

    {

        nombre: "Carlos Perez",

        tipo: "Teens"

    },

    {

        nombre: "Andrea Ruiz",

        tipo: "Masters"

    },

    {

        nombre: "Fernanda Gomez",

        tipo: "Seniors"

    },

    {

        nombre: "Mateo Ramirez",

        tipo: "Teens"

    },

    {

        nombre: "Mateo Torres",

        tipo: "Masters"

    }

];

/* ==========================================================
ESTADO GLOBAL
========================================================== */

const state = {

    horario: null,

    celda: null,

    fecha: new Date(),

    horarios: {}

};

/* ==========================================================
HELPERS DOM
========================================================== */

const $ = id => document.getElementById(id);

const $$ = selector => document.querySelectorAll(selector);

const crear = etiqueta => document.createElement(etiqueta);

const texto = (id, valor) => {

    $(id).textContent = valor;

};

const html = (id, valor) => {

    $(id).innerHTML = valor;

};

const mostrar = id => {

    $(id).style.display = "block";

};

const ocultar = id => {

    $(id).style.display = "none";

};

const limpiar = id => {

    html(id, "");

};

/* ==========================================================
HELPERS GENERALES
========================================================== */

function obtenerCursoActual() {

    return {

        categoria: $("categoriaCurso")?.value || "",

        curso: $("gradoInput")?.value.trim() || ""

    };

}

function obtenerCelda(fila, col) {

    return $(`cell-${fila}-${col}`);

}

function obtenerJSONFormulario() {

    const {

        categoria,

        curso

    } = obtenerCursoActual();

    return {

        categoria,

        curso,

        profesor: $("profesorSelect").value,

        materia: $("materiaInput").value.trim(),

        salon: $("salonInput").value.trim(),

        tipo: $("tipoBloque").value

    };

}

/* ==========================================================
INICIALIZACIÓN
========================================================== */

document.addEventListener(

    "DOMContentLoaded",

    iniciarAplicacion

);

function iniciarAplicacion() {

    registrarEventos();

    crearGrid();

    cargarProfesores();

    actualizarSemana();

}

/* ==========================================================
EVENTOS
========================================================== */

function registrarEventos() {

    $("gradoInput")?.addEventListener(

        "change",

        cargarHorarioDesdeDB

    );

    $("categoriaCurso")?.addEventListener(

        "change",

        cargarHorarioDesdeDB

    );

}

/* ==========================================================
VALIDACIONES
========================================================== */

function validarCurso() {

    const {

        categoria,

        curso

    } = obtenerCursoActual();

    if (!categoria || !curso) {

        alert(

            "Selecciona una categoría y un curso."

        );

        return false;

    }

    return true;

}

function validarCeldaSeleccionada() {

    if (state.celda) {

        return true;

    }

    alert(

        "Selecciona una celda del horario."

    );

    return false;

}
/* ==========================================================
   PARTE 2
   ----------------------------------------------------------
   ✓ Grid del horario
   ✓ Eventos de las celdas
   ✓ Profesores
   ✓ Semana
==========================================================*/

/* ==========================================================
GRID
========================================================== */

function crearGrid() {

    const tbody = $("gridAsignar");

    if (!tbody) return;

    tbody.innerHTML = "";

    CONFIG.horas.forEach((hora, fila) => {

        const tr = crear("tr");

        tr.innerHTML = `

            <td class="hora-col">

                ${hora}

            </td>

            ${CONFIG.dias.map((dia, col) => `

                <td>

                    <div
                        class="cell"
                        id="cell-${fila}-${col}"
                        data-fila="${fila}"
                        data-col="${col}"
                    ></div>

                </td>

            `).join("")}

        `;

        tbody.appendChild(tr);

    });

    registrarEventosGrid();

}

/* ==========================================================
EVENTOS DEL GRID
========================================================== */

function registrarEventosGrid() {

    $$(".cell").forEach(cell => {

        cell.addEventListener(

            "click",

            () => {

                abrirModal(

                    Number(cell.dataset.fila),

                    Number(cell.dataset.col)

                );

            }

        );

    });

}

/* ==========================================================
PROFESORES
========================================================== */

function cargarProfesores() {

    const select = $("profesorSelect");

    if (!select) return;

    select.innerHTML = `

        <option value="">

            Seleccionar profesor

        </option>

    `;

    profesores.forEach(({ nombre }) => {

        select.insertAdjacentHTML(

            "beforeend",

            `

                <option value="${nombre}">

                    ${nombre}

                </option>

            `

        );

    });

}

/* ==========================================================
SEMANA
========================================================== */

function obtenerLunes(fecha) {

    const lunes = new Date(fecha);

    const diferencia =

        lunes.getDay() === 0

            ? -6

            : 1 - lunes.getDay();

    lunes.setDate(

        lunes.getDate() + diferencia

    );

    return lunes;

}

function obtenerDomingo(lunes) {

    const domingo = new Date(lunes);

    domingo.setDate(

        domingo.getDate() + 6

    );

    return domingo;

}

function actualizarSemana() {

    const lunes = obtenerLunes(

        state.fecha

    );

    const domingo = obtenerDomingo(

        lunes

    );

    const formato = {

        day: "numeric",

        month: "long"

    };

    texto(

        "tituloSemana",

        `${lunes.toLocaleDateString(

            "es-CO",

            formato

        )} - ${domingo.toLocaleDateString(

            "es-CO",

            formato

        )}`

    );

}

function cambiarSemana(direccion) {

    state.fecha.setDate(

        state.fecha.getDate()

        + (direccion * 7)

    );

    actualizarSemana();

}

/* ==========================================================
FECHA Y HORA ACTUAL
========================================================== */

function obtenerDiaActual() {

    let dia = new Date().getDay();

    return dia === 0

        ? 6

        : dia - 1;

}

function obtenerFilaActual() {

    const hora = new Date().getHours();

    return CONFIG.horas.findIndex(rango => {

        const [inicio, fin] = rango.split(" - ");

        const horaInicio = parseInt(inicio);

        const horaFin = parseInt(fin);

        return hora >= horaInicio && hora < horaFin;

    });

}
/* ==========================================================
   PARTE 3
   ----------------------------------------------------------
   ✓ API
   ✓ Curso actual
   ✓ Modal
   ✓ Validaciones
   ✓ Guardar bloque
   ✓ Cargar horario
   ✓ Eliminar bloque
==========================================================*/

/* ==========================================================
API
========================================================== */

async function api(url, datos = null) {

    const opciones = {

        method: datos ? "POST" : "GET",

        headers: {
            "Content-Type": "application/json"
        }

    };

    if (datos) {

        opciones.body = JSON.stringify(datos);

    }

    const response = await fetch(url, opciones);

    return await response.json();

}

/* ==========================================================
CURSO ACTUAL
========================================================== */

function obtenerCursoActual() {

    return {

        categoria: $("categoriaCurso").value,

        curso: $("gradoInput").value.trim()

    };

}

function obtenerDatosFormulario() {

    const curso = obtenerCursoActual();

    return {

        ...curso,

        profesor: $("profesorSelect").value,

        materia: $("materiaInput").value.trim(),

        salon: $("salonInput").value.trim(),

        tipo: $("tipoBloque").value

    };

}

/* ==========================================================
VALIDACIONES
========================================================== */

function validarCurso() {

    const { categoria, curso } = obtenerCursoActual();

    if (!categoria || !curso) {

        alert("Completa la categoría y el curso.");

        return false;

    }

    return true;

}

/* ==========================================================
MODAL
========================================================== */

function abrirModal(fila, col) {

    if (!state.horario) {

        alert("Busca un curso primero.");

        return;

    }

    state.celda = {

        fila,

        col

    };

    mostrar("overlay");

    mostrar("modal");

}

function cerrarModal() {

    ocultar("overlay");

    ocultar("modal");

}

/* ==========================================================
GUARDAR BLOQUE
========================================================== */

async function guardarBloque() {

    if (!validarCurso()) return;

    const datos = obtenerDatosFormulario();

    const payload = {

        categoria: datos.categoria,

        curso: datos.curso,

        fila: state.celda.fila,

        col: state.celda.col,

        profesor:

            datos.tipo === "descanso"

                ? "DESCANSO"

                : datos.profesor,

        materia:

            datos.tipo === "descanso"

                ? "DESCANSO"

                : datos.materia,

        salon:

            datos.tipo === "descanso"

                ? "-"

                : datos.salon,

        tipo: datos.tipo

    };

    try {

        const respuesta = await api(

            "/guardar-bloque/",

            payload

        );

        if (!respuesta.success) {

            alert("No fue posible guardar el bloque.");

            return;

        }

        await cargarHorarioDesdeDB();

        cerrarModal();

        alert("Bloque guardado correctamente.");

    }

    catch (error) {

        console.error(error);

        alert("Error al guardar el bloque.");

    }

}

/* ==========================================================
CARGAR HORARIO
========================================================== */

async function cargarHorarioDesdeDB() {

    if (!validarCurso()) return;

    const {

        categoria,

        curso

    } = obtenerCursoActual();

    try {

        const data = await api(

            `/obtener-horario/?categoria=${categoria}&curso=${curso}`

        );

        state.horario = {

            clave: `${categoria}-${curso}`,

            bloques: data.bloques || []

        };

        texto(

            "nombreHorarioActual",

            state.horario.clave

        );

        renderizarHorario();

    }

    catch (error) {

        console.error(error);

        alert("No fue posible cargar el horario.");

    }

}

/* ==========================================================
ELIMINAR BLOQUE
========================================================== */

async function eliminarBloque() {

    if (!state.celda) return;

    const {

        categoria,

        curso

    } = obtenerCursoActual();

    try {

        await api(

            "/eliminar-bloque/",

            {

                categoria,

                curso,

                fila: state.celda.fila,

                col: state.celda.col

            }

        );

        await cargarHorarioDesdeDB();

        cerrarModal();

    }

    catch (error) {

        console.error(error);

        alert("Error eliminando el bloque.");

    }

}
/* ==========================================================
   PARTE 3
   ----------------------------------------------------------
   ✓ API
   ✓ Curso actual
   ✓ Modal
   ✓ Validaciones
   ✓ Guardar bloque
   ✓ Cargar horario
   ✓ Eliminar bloque
==========================================================*/

/* ==========================================================
API
========================================================== */

async function api(url, datos = null) {

    const opciones = {

        method: datos ? "POST" : "GET",

        headers: {
            "Content-Type": "application/json"
        }

    };

    if (datos) {

        opciones.body = JSON.stringify(datos);

    }

    const response = await fetch(url, opciones);

    return await response.json();

}

/* ==========================================================
CURSO ACTUAL
========================================================== */

function obtenerCursoActual() {

    return {

        categoria: $("categoriaCurso").value,

        curso: $("gradoInput").value.trim()

    };

}

function obtenerDatosFormulario() {

    const curso = obtenerCursoActual();

    return {

        ...curso,

        profesor: $("profesorSelect").value,

        materia: $("materiaInput").value.trim(),

        salon: $("salonInput").value.trim(),

        tipo: $("tipoBloque").value

    };

}

/* ==========================================================
VALIDACIONES
========================================================== */

function validarCurso() {

    const { categoria, curso } = obtenerCursoActual();

    if (!categoria || !curso) {

        alert("Completa la categoría y el curso.");

        return false;

    }

    return true;

}

/* ==========================================================
MODAL
========================================================== */

function abrirModal(fila, col) {

    if (!state.horario) {

        alert("Busca un curso primero.");

        return;

    }

    state.celda = {

        fila,

        col

    };

    mostrar("overlay");

    mostrar("modal");

}

function cerrarModal() {

    ocultar("overlay");

    ocultar("modal");

}

/* ==========================================================
GUARDAR BLOQUE
========================================================== */

async function guardarBloque() {

    if (!validarCurso()) return;

    const datos = obtenerDatosFormulario();

    const payload = {

        categoria: datos.categoria,

        curso: datos.curso,

        fila: state.celda.fila,

        col: state.celda.col,

        profesor:

            datos.tipo === "descanso"

                ? "DESCANSO"

                : datos.profesor,

        materia:

            datos.tipo === "descanso"

                ? "DESCANSO"

                : datos.materia,

        salon:

            datos.tipo === "descanso"

                ? "-"

                : datos.salon,

        tipo: datos.tipo

    };

    try {

        const respuesta = await api(

            "/guardar-bloque/",

            payload

        );

        if (!respuesta.success) {

            alert("No fue posible guardar el bloque.");

            return;

        }

        await cargarHorarioDesdeDB();

        cerrarModal();

        alert("Bloque guardado correctamente.");

    }

    catch (error) {

        console.error(error);

        alert("Error al guardar el bloque.");

    }

}

/* ==========================================================
CARGAR HORARIO
========================================================== */

async function cargarHorarioDesdeDB() {

    if (!validarCurso()) return;

    const {

        categoria,

        curso

    } = obtenerCursoActual();

    try {

        const data = await api(

            `/obtener-horario/?categoria=${categoria}&curso=${curso}`

        );

        state.horario = {

            clave: `${categoria}-${curso}`,

            bloques: data.bloques || []

        };

        texto(

            "nombreHorarioActual",

            state.horario.clave

        );

        renderizarHorario();

    }

    catch (error) {

        console.error(error);

        alert("No fue posible cargar el horario.");

    }

}

/* ==========================================================
ELIMINAR BLOQUE
========================================================== */

async function eliminarBloque() {

    if (!state.celda) return;

    const {

        categoria,

        curso

    } = obtenerCursoActual();

    try {

        await api(

            "/eliminar-bloque/",

            {

                categoria,

                curso,

                fila: state.celda.fila,

                col: state.celda.col

            }

        );

        await cargarHorarioDesdeDB();

        cerrarModal();

    }

    catch (error) {

        console.error(error);

        alert("Error eliminando el bloque.");

    }

}
/* ==========================================================
   PARTE 4
   ----------------------------------------------------------
   ✓ Render del horario
   ✓ Tarjetas
   ✓ Resaltado de celdas
   ✓ Eliminar horario
==========================================================*/

/* ==========================================================
LIMPIAR GRID
========================================================== */

function limpiarGrid() {

    $$(".cell").forEach(cell => {

        cell.innerHTML = "";

        cell.classList.remove(

            "filtro-activo"

        );

    });

}

/* ==========================================================
OBTENER CELDA
========================================================== */

function obtenerCelda(fila, col) {

    return $(`cell-${fila}-${col}`);

}

/* ==========================================================
TARJETAS
========================================================== */

function crearCardDescanso() {

    return `

        <div class="card-descanso">

            ☕ Descanso

        </div>

    `;

}

function crearCardHorario(bloque) {

    return `

        <div class="card-horario ${bloque.tipo === "relevo" ? "card-relevo" : ""}">

            <div class="card-title">

                ${bloque.materia}

            </div>

            <div class="card-mini">

                👨‍🏫 ${bloque.profesor}

            </div>

            <div class="card-mini">

                🏫 ${bloque.salon}

            </div>

            <div class="card-mini">

                🔖 ${bloque.tipo}

            </div>

        </div>

    `;

}

/* ==========================================================
RENDER DE BLOQUE
========================================================== */

function renderizarBloque(bloque) {

    const cell = obtenerCelda(

        bloque.fila,

        bloque.col

    );

    if (!cell) return;

    cell.innerHTML =

        bloque.tipo === "descanso"

            ? crearCardDescanso()

            : crearCardHorario(bloque);

}

/* ==========================================================
RENDER GENERAL
========================================================== */

function renderizarHorario() {

    limpiarGrid();

    if (!state.horario) return;

    state.horario.bloques.forEach(

        renderizarBloque

    );

}

/* ==========================================================
RESALTAR CELDAS
========================================================== */

function limpiarResaltados() {

    $$(".cell").forEach(cell =>

        cell.classList.remove(

            "filtro-activo"

        )

    );

}

function resaltarCelda(fila, col) {

    limpiarResaltados();

    const cell = obtenerCelda(

        fila,

        col

    );

    if (!cell) return;

    cell.classList.add(

        "filtro-activo"

    );

    cell.scrollIntoView({

        behavior: "smooth",

        block: "center",

        inline: "center"

    });

}

/* ==========================================================
ELIMINAR HORARIO
========================================================== */

function eliminarHorarioActual() {

    if (!state.horario) {

        alert(

            "No hay horario cargado."

        );

        return;

    }

    if (

        !confirm(

            "¿Eliminar este horario?"

        )

    ) {

        return;

    }

    delete horarios[

        state.horario.clave

    ];

    state.horario = null;

    renderizarHorario();

    texto(

        "nombreHorarioActual",

        "Sin horario"

    );

}