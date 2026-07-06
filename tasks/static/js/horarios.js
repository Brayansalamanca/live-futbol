    /* =========================================
CONFIGURACIÓN
========================================= */

const dias = [
    "Lunes",
    "Martes",
    "Miércoles",
    "Jueves",
    "Viernes",
    "Sábado",
    "Domingo"
];

const horas = [
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
];

/* =========================================
USUARIOS
========================================= */

const usuariosRegistrados = [

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

/* =========================================
VARIABLES
========================================= */

let horarios = JSON.parse(
    localStorage.getItem("horariosGrados")
) || {};

let horarioActual = null;

let celdaActual = null;

let fechaActual = new Date();

/* =========================================
INICIO
========================================= */

document.addEventListener(
    "DOMContentLoaded",
    () => {

        crearGrid();

        cargarProfesores();

        actualizarSemana();

    }
);

/* =========================================
GRID
========================================= */

function crearGrid(){

    const tbody =
    document.getElementById(
        "gridAsignar"
    );

    tbody.innerHTML = "";

    horas.forEach((hora,fila)=>{

        const tr =
        document.createElement("tr");

        let html = `

            <td class="hora-col">
                ${hora}
            </td>

        `;

        dias.forEach((dia,col)=>{

            html += `

                <td>

                    <div
                        class="cell"
                        id="cell-${fila}-${col}"
                        onclick="
                            abrirModal(
                                ${fila},
                                ${col}
                            )
                        "
                    ></div>

                </td>

            `;

        });

        tr.innerHTML = html;

        tbody.appendChild(tr);

    });

}

/* =========================================
PROFESORES
========================================= */

function cargarProfesores(){

    const select =
    document.getElementById(
        "profesorSelect"
    );

    select.innerHTML = `

        <option value="">
            Seleccionar profesor
        </option>

    `;

    usuariosRegistrados.forEach(usuario=>{

        select.innerHTML += `

            <option value="${usuario.nombre}">
                ${usuario.nombre}
            </option>

        `;

    });

}

/* =========================================
GUARDAR
========================================= */

function guardarSistema(){

    localStorage.setItem(
        "horariosGrados",
        JSON.stringify(horarios)
    );

}

/* =========================================
SEMANA
========================================= */

function obtenerLunes(fecha){

    const copia =
    new Date(fecha);

    const dia =
    copia.getDay();

    const diferencia =
    dia === 0
    ? -6
    : 1 - dia;

    copia.setDate(
        copia.getDate()
        + diferencia
    );

    return copia;

}

function actualizarSemana(){

    const lunes =
    obtenerLunes(fechaActual);

    const domingo =
    new Date(lunes);

    domingo.setDate(
        domingo.getDate() + 6
    );

    const opciones = {

        day:"numeric",
        month:"long"

    };

    document.getElementById(
        "tituloSemana"
    ).innerText = `

        ${lunes.toLocaleDateString(
            "es-CO",
            opciones
        )}

        -

        ${domingo.toLocaleDateString(
            "es-CO",
            opciones
        )}

    `;

}

function cambiarSemana(valor){

    fechaActual.setDate(
        fechaActual.getDate()
        + (7 * valor)
    );

    actualizarSemana();

}

/* =========================================
MODAL
========================================= */

function abrirModal(fila,col){

    if(!horarioActual){

        alert(
            "Busca un curso primero"
        );

        return;

    }

    celdaActual = {
        fila,
        col
    };

    document.getElementById(
        "overlay"
    ).style.display = "block";

    document.getElementById(
        "modal"
    ).style.display = "block";

}

function cerrarModal(){

    document.getElementById(
        "overlay"
    ).style.display = "none";

    document.getElementById(
        "modal"
    ).style.display = "none";

}

/* =========================================
GUARDAR BLOQUE
========================================= */

async function guardarBloque(){

    const categoria =
    document.getElementById(
        "categoriaCurso"
    ).value;

    const curso =
    document.getElementById(
        "gradoInput"
    ).value.trim();

    const profesor =
    document.getElementById(
        "profesorSelect"
    ).value;

    const materia =
    document.getElementById(
        "materiaInput"
    ).value.trim();

    const salon =
    document.getElementById(
        "salonInput"
    ).value.trim();

    const tipo =
    document.getElementById(
        "tipoBloque"
    ).value;

    if(!categoria || !curso){

        alert(
            "Completa categoría y curso"
        );

        return;

    }

    const response =
    await fetch(
        "/guardar-bloque/",
        {

            method:"POST",

            headers:{
                "Content-Type":"application/json"
            },

            body:JSON.stringify({

                categoria,
                curso,

                fila:celdaActual.fila,
                col:celdaActual.col,

                profesor:
                tipo === "descanso"
                ? "DESCANSO"
                : profesor,

                materia:
                tipo === "descanso"
                ? "DESCANSO"
                : materia,

                salon:
                tipo === "descanso"
                ? "-"
                : salon,

                tipo

            })

        }
    );

    const data =
    await response.json();

    if(data.success){

        alert(
            "Bloque guardado"
        );

        cargarHorarioDesdeDB();

        cerrarModal();

    }

}

/* =========================================
CARGAR HORARIO DESDE DB
========================================= */

async function cargarHorarioDesdeDB(){

    const categoria =
    document.getElementById(
        "categoriaCurso"
    ).value;

    const curso =
    document.getElementById(
        "gradoInput"
    ).value.trim();

    if(!categoria || !curso){

        return;

    }

    const response =
    await fetch(

        `/obtener-horario/?categoria=${categoria}&curso=${curso}`

    );

    const data =
    await response.json();

    horarioActual = {

        clave:`${categoria}-${curso}`,
        bloques:data.bloques

    };

    document.getElementById(
        "nombreHorarioActual"
    ).innerText =
    `${categoria} - ${curso}`;

    renderizarHorario();

}

/* =========================================
ELIMINAR BLOQUE
========================================= */

async function eliminarBloque(){

    if(!celdaActual){
        return;
    }

    const categoria =
    document.getElementById(
        "categoriaCurso"
    ).value;

    const curso =
    document.getElementById(
        "gradoInput"
    ).value.trim();

    try{

        const response = await fetch(
            "/eliminar-bloque/",
            {
                method:"POST",

                headers:{
                    "Content-Type":"application/json"
                },

                body:JSON.stringify({

                    categoria,
                    curso,

                    fila:celdaActual.fila,
                    col:celdaActual.col

                })
            }
        );

        const texto =
        await response.text();

        console.log(
            "RESPUESTA:",
            texto
        );

        // 🔥 RECARGAR TABLA
        await cargarHorarioDesdeBD();

        cerrarModal();

    }

    catch(error){

        console.error(
            "ERROR:",
            error
        );

    }

}
/* =========================================
ELIMINAR HORARIO
========================================= */

function eliminarHorarioActual(){

    if(!horarioActual){

        alert(
            "No hay horario cargado"
        );

        return;

    }

    const confirmar =
    confirm(
        "¿Eliminar este horario?"
    );

    if(!confirmar) return;

    delete horarios[
        horarioActual.clave
    ];

    guardarSistema();

    horarioActual = null;

    renderizarHorario();

    document.getElementById(
        "nombreHorarioActual"
    ).innerText =
    "Sin horario";

}

/* =========================================
RENDER
========================================= */

function renderizarHorario(){

    document
    .querySelectorAll(".cell")
    .forEach(cell=>{

        cell.innerHTML = "";

        cell.classList.remove(
            "filtro-activo"
        );

    });

    if(!horarioActual) return;

    horarioActual.bloques.forEach(bloque=>{

        const cell =
        document.getElementById(
            `cell-${bloque.fila}-${bloque.col}`
        );

        if(!cell) return;

        if(
            bloque.tipo === "descanso"
        ){

            cell.innerHTML = `

                <div class="card-descanso">
                    ☕ Descanso
                </div>

            `;

        }

        else{

            let claseExtra = "";

            if(
                bloque.tipo === "relevo"
            ){

                claseExtra =
                "card-relevo";

            }

            cell.innerHTML = `

    <div
        class="
            card-horario
            ${claseExtra}
        "
    >

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

    });

}

/* =========================================
BUSCAR PROFESOR
========================================= */

function buscarHorarioInteligente(){

    const texto =
    document.getElementById(
        "busquedaHorario"
    )
    .value
    .toLowerCase()
    .trim();

    const sugerencias =
    document.getElementById(
        "sugerenciasBusqueda"
    );

    sugerencias.innerHTML = "";

    if(texto === ""){

        sugerencias.style.display =
        "none";

        return;

    }

    let resultados = [];

    Object.entries(horarios)
    .forEach(([clave,horario])=>{

        horario.bloques.forEach(bloque=>{

            const combinado = `

                ${bloque.profesor}
                ${bloque.materia}
                ${bloque.salon}

            `
            .toLowerCase();

            if(
                combinado.includes(texto)
            ){

                resultados.push({

                    profesor:
                    bloque.profesor,

                    materia:
                    bloque.materia,

                    salon:
                    bloque.salon,

                    fila:
                    bloque.fila,

                    col:
                    bloque.col,

                    clave

                });

            }

        });

    });

    resultados.forEach(resultado=>{

        const item =
        document.createElement("div");

        item.className =
        "sugerencia-item";

        item.innerHTML = `

            <strong>
                👨‍🏫
                ${resultado.profesor}
            </strong>

            <br>

            📚
            ${resultado.materia}

            <br>

            🏫
            ${resultado.salon}

        `;

        item.onclick = ()=>{

            abrirResultadoBusqueda(
                resultado
            );

            sugerencias.style.display =
            "none";

        };

        sugerencias.appendChild(item);

    });

    sugerencias.style.display =

        resultados.length > 0
        ? "block"
        : "none";

}

/* =========================================
BUSCAR CURSO
========================================= */

function buscarCurso(){

    const texto =
    document.getElementById(
        "busquedaCurso"
    )
    .value
    .toLowerCase()
    .trim();

    const sugerencias =
    document.getElementById(
        "sugerenciasCurso"
    );

    sugerencias.innerHTML = "";

    if(texto === ""){

        sugerencias.style.display =
        "none";

        return;

    }

    let resultados = [];

    Object.entries(horarios)
    .forEach(([clave,horario])=>{

        if(
            clave.toLowerCase()
            .includes(texto)
        ){

            resultados.push({
                clave,
                horario
            });

        }

    });

    resultados.forEach(resultado=>{

        const item =
        document.createElement("div");

        item.className =
        "sugerencia-item";

        item.innerHTML = `

            📚
            ${resultado.clave}

        `;

        item.onclick = ()=>{

            horarioActual =
            resultado.horario;

            horarioActual.clave =
            resultado.clave;

            document.getElementById(
                "nombreHorarioActual"
            ).innerText =
            resultado.clave;

            renderizarHorario();

            sugerencias.style.display =
            "none";

        };

        sugerencias.appendChild(item);

    });

    sugerencias.style.display =

        resultados.length > 0
        ? "block"
        : "none";

}

/* =========================================
ABRIR RESULTADO
========================================= */

function abrirResultadoBusqueda(
    resultado
){

    horarioActual =
    horarios[resultado.clave];

    horarioActual.clave =
    resultado.clave;

    document.getElementById(
        "nombreHorarioActual"
    ).innerText =
    resultado.clave;

    renderizarHorario();

    setTimeout(()=>{

        const cell =
        document.getElementById(
            `cell-${resultado.fila}-${resultado.col}`
        );

        if(cell){

            cell.classList.add(
                "filtro-activo"
            );

            cell.scrollIntoView({

                behavior:"smooth",

                block:"center",

                inline:"center"

            });

        }

    },100);

}

/* =========================================
VER PROFESOR ACTUAL
========================================= */

function verProfesorActual(){

    const texto =
    document.getElementById(
        "busquedaHorario"
    )
    .value
    .trim()
    .toLowerCase();

    if(texto === ""){

        alert(
            "Escribe un profesor"
        );

        return;

    }

    const ahora =
    new Date();

    let diaActual =
    ahora.getDay();

    if(diaActual === 0){

        diaActual = 6;

    }

    else{

        diaActual--;

    }

    const horaActual =
    ahora.getHours();

    let filaActual = -1;

    horas.forEach((hora,index)=>{

        const partes =
        hora.split(" - ");

        const inicio =
        parseInt(
            partes[0]
            .split(":")[0]
        );

        const fin =
        parseInt(
            partes[1]
            .split(":")[0]
        );

        if(
            horaActual >= inicio
            &&
            horaActual < fin
        ){

            filaActual = index;

        }

    });

    if(filaActual === -1){

        alert(
            "No hay clases ahora"
        );

        return;

    }

    let encontrado = null;

    Object.entries(horarios)
    .forEach(([clave,horario])=>{

        horario.bloques.forEach(bloque=>{

            if(

                bloque.profesor
                .toLowerCase()
                .includes(texto)

                &&

                bloque.fila === filaActual

                &&

                bloque.col === diaActual

            ){

                encontrado = {

                    bloque,
                    horario,
                    clave

                };

            }

        });

    });

    if(!encontrado){

        alert(
            "No encontrado"
        );

        return;

    }

    horarioActual =
    encontrado.horario;

    horarioActual.clave =
    encontrado.clave;

    document.getElementById(
        "nombreHorarioActual"
    ).innerText =
    encontrado.clave;

    renderizarHorario();

    setTimeout(()=>{

        const cell =
        document.getElementById(
            `cell-${encontrado.bloque.fila}-${encontrado.bloque.col}`
        );

        if(cell){

            cell.classList.add(
                "filtro-activo"
            );

            cell.scrollIntoView({

                behavior:"smooth",

                block:"center"

            });

        }

    },100);

}

/* =========================================
LIMPIAR TODO
========================================= */

function limpiarTodo(){

    const confirmar =
    confirm(
        "¿Eliminar todos los horarios?"
    );

    if(!confirmar) return;

    localStorage.removeItem(
        "horariosGrados"
    );
    document.getElementById(
    "gradoInput"
).addEventListener(
    "change",
    cargarHorarioDesdeDB
);

document.getElementById(
    "categoriaCurso"
).addEventListener(
    "change",
    cargarHorarioDesdeDB
);
    horarios = {};

    horarioActual = null;

    renderizarHorario();

    document.getElementById(
        "nombreHorarioActual"
    ).innerText =
    "Sin horario";


}