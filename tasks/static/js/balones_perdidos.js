
let datosGlobales = [];
const IMG_DEFAULT = "{% static 'sin evidencia.webp' %}";

async function sincronizar() {
    try {
        const res = await fetch("{% url 'api_obtener_bajas' %}");
        const data = await res.json();
        datosGlobales = data;
        dibujarTabla(data);
    } catch (e) { console.error("Error al sincronizar:", e); }
}

function dibujarTabla(data) {
    const tbody = document.getElementById('tablaCuerpo');
    if (!data || data.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" style="padding:30px; color:var(--text-soft);">No hay reportes registrados.</td></tr>';
        return;
    }

    tbody.innerHTML = data.map(b => {
        const responsable = b.responsable || b.usuario || 'Anónimo';
        const alquilo = b.alquilado_por || '---';
        const material = b.tipo_balon || b.tipo || '---';
        const lugar = b.lugar || 'No especificada';
        const causa = b.causa || 'Reportado';
        const img = b.imagen || IMG_DEFAULT;
        
        let fechaMostrada = 'Reciente';
        if (b.fecha) {
            const date = new Date(b.fecha);
            if (!isNaN(date.getTime())) {
                fechaMostrada = date.toLocaleString('es-CO');
            } else {
                fechaMostrada = b.fecha;
            }
        }

        return `
            <tr>
                <td><img src="${img}" class="img-celda" onclick="verImg('${img}')" onerror="this.src='${IMG_DEFAULT}'"></td>
                <td style="font-size: 11px; color:var(--text-soft);">${fechaMostrada}</td>
                <td style="text-align: left;">
                    <div style="font-size: 11px; color: var(--primary);">ALQUILÓ: <span style="color: var(--text); font-weight: bold;">${alquilo}</span></div>
                    <div style="font-size: 11px; color: #ff4444;">BOTÓ: <span style="color: var(--text); font-weight: bold;">${responsable}</span></div>
                </td>
                <td style="font-size: 13px;">${material}<br><small style="color:var(--primary)">${lugar}</small></td>
                <td><span style="background:var(--bg-soft); padding:4px 8px; border-radius:4px; font-size:10px; border: 1px solid var(--border);">${causa.toUpperCase()}</span></td>
                <td>
                    <button onclick="eliminar('${b.id}')" class="btn-eliminar">Eliminar</button>
                </td>
            </tr>
        `;
    }).join('');
}

async function guardarBaja() {
    const btn = document.getElementById('btnGuardar');
    const user = document.getElementById('usuario').value.trim();
    if (!user) return alert("Escribe el nombre del responsable.");

    btn.disabled = true;
    btn.innerText = "⏳ REGISTRANDO...";

    const file = document.getElementById('imagen_file').files[0];
    const enviar = async (imgData) => {
        const payload = {
            usuario: user,
            alquilado_por: document.getElementById('alquilado_por').value,
            tipo: document.getElementById('tipo').value,
            lugar: document.getElementById('lugar').value,
            causa: document.getElementById('causa').value,
            imagen: imgData
        };

        try {
            const res = await fetch("{% url 'api_guardar_baja' %}", {
                method: "POST",
                headers: { "Content-Type": "application/json", "X-CSRFToken": "{{ csrf_token }}" },
                body: JSON.stringify(payload)
            });
            if (res.ok) {
                document.getElementById('formBalones').reset();
                sincronizar();
            }
        } catch (e) { alert("Error al guardar."); }
        finally {
            btn.disabled = false;
            btn.innerText = "🚀 Registrar Novedad";
        }
    };

    if (file) {
        const reader = new FileReader();
        reader.onload = (e) => enviar(e.target.result);
        reader.readAsDataURL(file);
    } else {
        enviar(null);
    }
}

async function eliminar(id) {
    if (confirm("¿Eliminar este registro?")) {
        const res = await fetch(`/api/eliminar-baja/${id}/`, { 
            method: "POST", 
            headers: { "X-CSRFToken": "{{ csrf_token }}" } 
        });
        if (res.ok) sincronizar();
    }
}

function verImg(src) {
    document.getElementById('img_visor_inv').src = src;
    document.getElementById('visor_inv').style.display = 'flex';
}

function exportarExcel() {
    if (datosGlobales.length === 0) return alert("No hay datos.");
    const ws = XLSX.utils.json_to_sheet(datosGlobales);
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, "Bajas");
    XLSX.writeFile(wb, "Reporte_Bajas.xlsx");
}

window.onload = sincronizar;