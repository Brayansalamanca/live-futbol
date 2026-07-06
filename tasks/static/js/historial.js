
const API_OBTENER_ENTREGAS = "/api/obtener-historial/"; 

function togglePanel(id){
    const panel = document.getElementById(id);
    panel.style.display = (panel.style.display === "none" || panel.style.display === "") ? "block" : "none";
}

// Clasificación de ciclos dinámica basada en el curso numérico
function obtenerCiclo(curso){
    if(!curso) return "Sin ciclo";
    const grado = parseInt(curso);
    if([6, 7, 8].includes(grado)) return "Seniors";
    if([3, 4, 5].includes(grado)) return "Teens";
    if([9, 10, 11].includes(grado)) return "Masters";
    return "Sin ciclo";
}

// Construye la fila inyectando de forma persistente la copia del ID de la base de datos
function crearFila(entrega){
    const fecha = new Date(entrega.fecha);
    const fechaFormateada = fecha.toLocaleDateString() + " " + fecha.toLocaleTimeString();

    let emoji = "⚽";
    const objeto = entrega.objeto || "";
    if(objeto.toLowerCase().includes("basket")) emoji = "🏀";
    if(objeto.toLowerCase().includes("volley")) emoji = "🏐";

    const estadoBadge = entrega.eliminado 
    ? `<span style="background:#fee2e2;  padding:6px 12px; border-radius:999px; font-size:12px; font-weight:bold;">Respaldado en BD</span>`
    : `<span style="background:#dcfce7;  padding:6px 12px; border-radius:999px; font-size:12px; font-weight:bold;">Activo</span>`;

    return `
        <tr style="border-bottom:1px solid #e2e8f0;">
            <td style="padding:15px; font-family: monospace;  font-weight: bold;">
                #${entrega.id_prestamo_original || 'S/N'}
            </td>
            <td style="padding:15px;">
                <div style="display:flex; align-items:center; gap:10px;">
                    <div style="width:40px; height:40px; border-radius:10px; background:#f1f5f9; display:flex; align-items:center; justify-content:center; font-size:22px;">
                        ${emoji}
                    </div>
                    <strong>${entrega.objeto}</strong>
                </div>
            </td>
            <td style="padding:15px;">${entrega.nombre}</strong></td>
            <td style="padding:15px;">${entrega.curso}</td>
            <td style="padding:15px; ">${entrega.lugar || 'N/A'}</td>
            <td style="padding:15px;  ">${fechaFormateada}</td>
            <td style="padding:15px;">${estadoBadge}</td>
        </tr>
    `;
}

// Reparte los datos de la BD en cada una de las tres tablas
function renderizarTablas(entregas){
    const tablaSeniors = document.getElementById("tablaSeniors");
    const tablaTeens = document.getElementById("tablaTeens");
    const tablaMasters = document.getElementById("tablaMasters");

    tablaSeniors.innerHTML = "";
    tablaTeens.innerHTML = "";
    tablaMasters.innerHTML = "";

    let totalSeniors = 0, totalTeens = 0, totalMasters = 0;
    
    // Obtenemos la fecha actual
    const ahora = new Date();

    entregas.forEach(entrega => {
        // --- LÓGICA DE ELIMINACIÓN AUTOMÁTICA ---
        const fechaEntrega = new Date(entrega.fecha);
        const diferenciaTiempo = ahora - fechaEntrega;
        const diferenciaDias = diferenciaTiempo / (1000 * 60 * 60 * 24);

        // Si han pasado 14 días o más, no renderizamos esta fila (la "eliminamos" de la vista)
        if (diferenciaDias >= 14) {
            return; 
        }
        // ----------------------------------------

        const ciclo = obtenerCiclo(entrega.curso);
        if(ciclo === "Seniors") { tablaSeniors.innerHTML += crearFila(entrega); totalSeniors++; }
        if(ciclo === "Teens") { tablaTeens.innerHTML += crearFila(entrega); totalTeens++; }
        if(ciclo === "Masters") { tablaMasters.innerHTML += crearFila(entrega); totalMasters++; }
    });

    document.getElementById("contadorSeniors").innerText = `${totalSeniors} registros`;
    document.getElementById("contadorTeens").innerText = `${totalTeens} registros`;
    document.getElementById("contadorMasters").innerText = `${totalMasters} registros`;
}

// Consume los datos del servidor de manera asíncrona (MongoDB Centralized)
async function cargarEntregas(){
    try{
        const response = await fetch(API_OBTENER_ENTREGAS);
        if(response.ok) {
            const entregas = await response.json();
            renderizarTablas(entregas);
        }
    }catch(error){
        console.error("Error al sincronizar con el servidor MongoDB:", error);
    }
}

// Filtro de búsqueda reactivo en tiempo de ejecución
document.getElementById('inputBusqueda').addEventListener('keyup', function(){
    const texto = this.value.toLowerCase();
    document.querySelectorAll('tbody tr').forEach(fila => {
        fila.style.display = fila.innerText.toLowerCase().includes(texto) ? '' : 'none';
    });
});

// POLLING AUTOMÁTICO EN TIEMPO REAL (Frecuencia de alta prioridad: Cada 2 segundos)
setInterval(cargarEntregas, 2000);

// Ejecución inicial al cargar el archivo en el DOM
cargarEntregas();