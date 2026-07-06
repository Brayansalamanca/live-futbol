 function previsualizar(input) {
        if (input.files && input.files[0]) {
            const reader = new FileReader();
            reader.onload = function(e) {
                document.getElementById('preview-img').src = e.target.result;
                document.getElementById('preview-img').style.display = 'block';
                document.getElementById('preview-placeholder').style.display = 'none';
            }
            reader.readAsDataURL(input.files[0]);
        }
    }

    document.getElementById('btnGuardar').addEventListener('click', async () => {
        const nombre = document.getElementById('nombre').value;
        const cantidad = document.getElementById('cantidad').value;
        const talla = document.getElementById('talla').value;
        const archivo = document.getElementById('imagenInput').files[0];

        if (!nombre || !archivo || !talla) {
            alert("⚠️ Por favor completa los campos y sube una foto.");
            return;
        }

        const btn = document.getElementById('btnGuardar');
        btn.disabled = true;
        btn.innerHTML = "<span>⏳ PROCESANDO...</span>";

        const reader = new FileReader();
        reader.readAsDataURL(archivo);
        reader.onload = async () => {
            try {
                const res = await fetch("{% url 'api_guardar_prenda' %}", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "X-CSRFToken": "{{ csrf_token }}"
                    },
                    body: JSON.stringify({
                        nombre: nombre,
                        cantidad: cantidad,
                        talla: talla,
                        imagen: reader.result
                    })
                });

                const data = await res.json();
                if (data.status === 'ok') {
                    window.location.href = "{% url 'tipos' %}";
                } else {
                    alert("❌ Error: " + data.message);
                    btn.disabled = false;
                    btn.innerHTML = "<span>🚀 SUBIR AL CATÁLOGO</span>";
                }
            } catch (e) {
                console.error(e);
                btn.disabled = false;
            }
        };
    });