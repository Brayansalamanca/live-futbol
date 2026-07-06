

    const sidebar = document.getElementById("sidebar");
    const main = document.getElementById("main");
    const toggleBtn = document.getElementById("toggleSidebar");

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

    toggleBtn.addEventListener("click", () => {
        sidebar.classList.toggle("closed");
        main.classList.toggle("expanded");

        if (sidebar.classList.contains("closed")) {
            localStorage.setItem("sidebar-estado", "cerrado");
        } else {
            localStorage.setItem("sidebar-estado", "abierto");
        }
    });

    // ==========================================================================
    // DARK MODE
    // ==========================================================================

    const themeBtn = document.getElementById("theme-toggle");

    if(localStorage.getItem("theme") === "light"){
        document.body.classList.add("light-mode");
        themeBtn.textContent = "☀️";
    }else{
        themeBtn.textContent = "🌙";
    }

    themeBtn.addEventListener("click", () => {
        document.body.classList.toggle("light-mode");
        if(document.body.classList.contains("light-mode")){
            localStorage.setItem("theme", "light");
            themeBtn.textContent = "☀️";
        }else{
            localStorage.setItem("theme", "dark");
            themeBtn.textContent = "🌙";
        }
    });

    // ==========================================================================
    // RESPONSIVE SIDEBAR
    // ==========================================================================

    if(window.innerWidth <= 900){
        sidebar.classList.add("closed");
        main.classList.add("expanded");
    }
