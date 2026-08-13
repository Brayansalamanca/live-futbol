// =====================================================
// ELEMENTOS PRINCIPALES
// =====================================================

const sidebar = document.getElementById("sidebar");
const main = document.getElementById("main");
const toggleBtn = document.getElementById("toggleSidebar");


// =====================================================
// ESTADO DEL SIDEBAR
// =====================================================

const estadoSidebar = localStorage.getItem("sidebar-estado");

if (estadoSidebar === "cerrado") {

    sidebar.classList.add("closed");
    main.classList.add("expanded");

} else if (estadoSidebar === "abierto") {

    sidebar.classList.remove("closed");
    main.classList.remove("expanded");

} else {

    if (window.innerWidth <= 900) {

        sidebar.classList.add("closed");
        main.classList.add("expanded");

    }

}


// =====================================================
// BOTÓN DEL SIDEBAR
// =====================================================

if (toggleBtn) {

    toggleBtn.addEventListener("click", (e) => {

        // Evita que el click se propague al document
        e.stopPropagation();

        if (window.innerWidth <= 900) {

            sidebar.classList.toggle("active");

        } else {

            sidebar.classList.toggle("closed");
            main.classList.toggle("expanded");

            // Guardar estado
            if (sidebar.classList.contains("closed")) {

                localStorage.setItem(
                    "sidebar-estado",
                    "cerrado"
                );

            } else {

                localStorage.setItem(
                    "sidebar-estado",
                    "abierto"
                );

            }

        }

    });

}


// =====================================================
// CERRAR SIDEBAR AL HACER CLICK AFUERA
// =====================================================

document.addEventListener("click", (e) => {

    if (!sidebar || !toggleBtn) {
        return;
    }

    if (
        window.innerWidth <= 900 &&
        sidebar.classList.contains("active") &&
        !sidebar.contains(e.target) &&
        !toggleBtn.contains(e.target)
    ) {

        sidebar.classList.remove("active");

    }

});


// =====================================================
// DARK MODE
// =====================================================

const themeBtn = document.getElementById("theme-toggle");

if (themeBtn) {

    if (localStorage.getItem("theme") === "light") {

        document.body.classList.add("light-mode");
        themeBtn.textContent = "☀️";

    } else {

        themeBtn.textContent = "🌙";

    }


    themeBtn.addEventListener("click", (e) => {

        e.stopPropagation();

        document.body.classList.toggle("light-mode");

        if (
            document.body.classList.contains("light-mode")
        ) {

            localStorage.setItem("theme", "light");
            themeBtn.textContent = "☀️";

        } else {

            localStorage.setItem("theme", "dark");
            themeBtn.textContent = "🌙";

        }

    });

}


// =====================================================
// RESPONSIVE
// =====================================================

function ajustarSidebar() {

    if (window.innerWidth <= 900) {

        sidebar.classList.add("closed");
        main.classList.add("expanded");

    } else {

        sidebar.classList.remove("active");

        const estado =
            localStorage.getItem("sidebar-estado");

        if (estado === "cerrado") {

            sidebar.classList.add("closed");
            main.classList.add("expanded");

        } else if (estado === "abierto") {

            sidebar.classList.remove("closed");
            main.classList.remove("expanded");

        }

    }

}

window.addEventListener(
    "resize",
    ajustarSidebar
);


// =====================================================
// DEBUG
// =====================================================

console.log("Base JS cargado correctamente");
console.log("Sidebar:", sidebar);
console.log("Main:", main);
console.log("Botón sidebar:", toggleBtn);
console.log("Botón tema:", themeBtn);