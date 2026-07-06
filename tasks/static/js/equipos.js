// ===== ESTADO =====
let torneos={}, torneoActual=null, faseActual="config", editIndex=null, archivoExcel=null;
let config={type:'liga_finales',n:10,pass:4,jornadas:3};
let equipos=[], torneo={ligaMatches:[],bracket:[]}, statsEquipos={}, datosDisciplina={};

const LOGO_DEFAULT="https://cdn-icons-png.flaticon.com/512/33/33736.png";

document.getElementById("excel-file").addEventListener("change",e=>archivoExcel=e.target.files[0]);

// ===== UTILS =====
function letraAIndice(l){let r=0;l=l.trim().toUpperCase();for(let i=0;i<l.length;i++)r=r*26+(l.charCodeAt(i)-64);return r-1}

function $id(id){return document.getElementById(id)}

// ===== PERSISTENCIA CORREGIDA =====

async function cargarBaseDatos(){
    try {
        const r = await fetch("/api/torneos/listar/");
        if (!r.ok) throw new Error("No se pudo listar");
        
        // CORRECCIÓN 1: Django devuelve un Objeto, así que lo asignamos directamente
        const data = await r.json(); 
        torneos = data; 
        
        const nombres = Object.keys(torneos);
        
        // Evitar reiniciar la vista si ya estamos dentro de un torneo
        if (nombres.length > 0 && !torneoActual) {
            cargarTorneo(nombres[0]);
        } else if (!torneoActual) {
            renderTabs();
            aplicarVista();
        } else {
            // Actualización silenciosa de los datos en pantalla
            _aplicarEstado(torneos[torneoActual]);
            renderTabs();
        }
    } catch(e) {
        console.warn("cargarBaseDatos error:", e);
        renderTabs();
        aplicarVista();
    }
}

async function guardar(){
    if(!torneoActual) return;
    
    torneos[torneoActual] = {
        config, 
        equipos, 
        torneo, 
        stats: statsEquipos, 
        disciplina: datosDisciplina, 
        fase: faseActual, 
        campeon: torneos[torneoActual]?.campeon || null
    };
    
    try {
        // CORRECCIÓN 2: Las cabeceras y el cuerpo deben ir DENTRO de las llaves del fetch
        const r = await fetch("/api/torneos/guardar/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                nombre: torneoActual, 
                datos: torneos[torneoActual]
            })
        });
        
        if(!r.ok) console.warn("Error al guardar:", await r.text());
    } catch(e) {
        console.warn("guardar error:", e);
    }
    
    renderTabs();
}


// ===== TABS =====
function renderTabs(){
  const c=$id("tabs-torneos"); if(!c) return;
  c.innerHTML=Object.keys(torneos).map(n=>`<button onclick="cargarTorneo('${n}')">${n===torneoActual?`>>> ${n}`:n}</button>`).join("");
}

// ===== TORNEOS =====
function estadoInicial(){return{config:{type:'liga_finales',n:10,pass:4,jornadas:3},equipos:[],torneo:{ligaMatches:[],bracket:[]},stats:{},disciplina:{},fase:"config",campeon:null}}

async function crearTorneo(){
  let nombre=prompt("Nombre del nuevo torneo:"); if(!nombre) return;
  nombre=nombre.trim(); if(!nombre){alert("Nombre inválido");return}
  if(torneos[nombre]){alert("Ese torneo ya existe");return}
  torneos[nombre]=estadoInicial();
  torneoActual=nombre;
  _aplicarEstado(torneos[nombre]);
  await guardar();
  aplicarVista(); actualizarSelectEquipos(); renderDisciplina();
  alert("Torneo creado correctamente");
}

async function eliminarTorneoActual(){
  if(!torneoActual){alert("No hay torneo seleccionado");return}
  if(!confirm(`¿Seguro que deseas eliminar "${torneoActual}"?`)) return;
  try{await fetch(`/api/torneos/eliminar/${encodeURIComponent(torneoActual)}/`,{method:"POST"})}catch(e){console.warn(e)}
  delete torneos[torneoActual];
  const rest=Object.keys(torneos);
  if(rest.length>0){cargarTorneo(rest[0])}
  else{torneoActual=null;_aplicarEstado(estadoInicial());renderTabs();aplicarVista()}
}

function iniciarNuevoTorneo(){
  if(confirm("¿Reiniciar todo? Se perderán los datos locales.")){
    torneos={};torneoActual=null;_aplicarEstado(estadoInicial());renderTabs();aplicarVista();
  }
}

function _aplicarEstado(d){
  config=d.config||{type:'liga_finales',n:10,pass:4,jornadas:3};
  equipos=d.equipos||[];
  torneo=d.torneo||{ligaMatches:[],bracket:[]};
  statsEquipos=d.stats||{};
  datosDisciplina=d.disciplina||{};
  faseActual=d.fase||"config";
}

function cargarTorneo(nombre){
  if(!torneos[nombre]) return;
  torneoActual=nombre;
  _aplicarEstado(torneos[nombre]);
  renderTabs(); renderRegistry(); actualizarSelectEquipos(); renderDisciplina(); aplicarVista();
  if(torneos[nombre].campeon) mostrarCampeon(torneos[nombre].campeon);
}

// ===== VISTAS =====
function aplicarVista(){
  ["setup-panel","team-registry-panel","competition-area","league-area","bracket-area"].forEach(id=>{const el=$id(id);if(el)el.style.display="none"});
  if(faseActual==="config") $id("setup-panel").style.display="block";
  if(faseActual==="equipos") $id("team-registry-panel").style.display="block";
  if(faseActual==="liga"){$id("competition-area").style.display="block";$id("league-area").style.display="block";renderTabla();renderJornadaActual()}
  if(faseActual==="finales"){$id("competition-area").style.display="block";$id("bracket-area").style.display="block";renderBracket()}
}

function toggleLeagueInputs(){$id("league-controls").style.display=$id("comp-type").value==="liga_finales"?"block":"none"}

function iniciarGestionEquipos(){
  config.type=$id("comp-type").value;
  config.n=parseInt($id("liga-num").value)||10;
  config.pass=parseInt($id("liga-pass").value)||4;
  config.jornadas=parseInt($id("liga-jornadas").value)||3;
  faseActual="equipos"; guardar(); aplicarVista();

}

// ===== EQUIPOS =====
function cargarEquiposExcel(){
  if(!archivoExcel){alert("Selecciona un archivo Excel");return}
  const hoja=$id("nombre-hoja").value;
  const fInicio=parseInt($id("fila-inicio").value);
  const fFin=parseInt($id("fila-fin").value);
  const colsStr=$id("columnas-usar").value;
  if(!hoja||isNaN(fInicio)||!colsStr){alert("Faltan datos");return}
  const cols=colsStr.split(",").map(c=>letraAIndice(c));
  const reader=new FileReader();
  reader.onload=e=>{
    const wb=XLSX.read(new Uint8Array(e.target.result),{type:"array"});
    const ws=wb.Sheets[hoja]; if(!ws){alert("Hoja no encontrada");return}
    const json=XLSX.utils.sheet_to_json(ws,{header:1});
    let count=0;
    for(let i=fInicio-1;i<(fFin||json.length);i++){
      if(!json[i]) continue;
      cols.forEach(ci=>{
        const val=json[i][ci]; if(!val) return;
        const name=String(val).trim();
        if(!equipos.find(eq=>eq.name.toLowerCase()===name.toLowerCase())&&equipos.length<config.n){
          equipos.push({name,logo:LOGO_DEFAULT});
          if(!datosDisciplina[name]) datosDisciplina[name]=[];
          count++;
        }
      });
    }
    guardar(); renderRegistry(); actualizarSelectEquipos(); alert(`Se agregaron ${count} equipos`);
  };
  reader.readAsArrayBuffer(archivoExcel);
}

function agregarEquipo(){
  const ni=$id("new-team-name"), li=$id("new-team-logo");
  const name=ni.value.trim(); if(!name){alert("Escribe un nombre");return}
  if(equipos.find(e=>e.name.toLowerCase()===name.toLowerCase())&&editIndex===null){alert("Ese equipo ya existe");return}
  const save=logo=>{
    if(editIndex!==null){equipos[editIndex]={name,logo};editIndex=null}
    else{if(equipos.length>=config.n){alert("Límite alcanzado");return}equipos.push({name,logo})}
    if(!datosDisciplina[name]) datosDisciplina[name]=[];
    guardar(); renderRegistry(); actualizarSelectEquipos(); ni.value=""; li.value="";
  };
  if(li.files&&li.files[0]){const r=new FileReader();r.onload=e=>save(e.target.result);r.readAsDataURL(li.files[0])}
  else save(editIndex!==null?equipos[editIndex].logo:LOGO_DEFAULT);
}

function renderRegistry(){
  const ul=$id("teams-list"); if(!ul) return;
  ul.innerHTML=equipos.map((e,i)=>`<li><span><img src="${e.logo}" width="25"> ${e.name}</span><button onclick="editarEquipo(${i})">Editar</button><button onclick="borrarEquipo(${i})">Borrar</button></li>`).join("");
  const btn=$id("btn-start-comp"); if(btn) btn.disabled=equipos.length<2;
}

function editarEquipo(i){editIndex=i;$id("new-team-name").value=equipos[i].name}

function borrarEquipo(i){if(!confirm("¿Eliminar equipo?"))return;equipos.splice(i,1);guardar();renderRegistry();actualizarSelectEquipos()}

// ===== LIGA =====
function iniciarCompeticion(){
  if(equipos.length<2){alert("Debes agregar mínimo 2 equipos");return}
  if(config.type==='liga_finales'){faseActual="liga";if(!torneo.ligaMatches.length)generarJornadaCompleta()}
  else{faseActual="finales";generarBracket(equipos)}
  guardar(); aplicarVista();
}

function generarJornadaCompleta() {
    torneo.ligaMatches = [];
    statsEquipos = {};
    const n = equipos.length;

    // Repetimos el ciclo tantas veces como config.jornadas indique
    for (let j = 0; j < config.jornadas; j++) {
        // Generamos todas las combinaciones posibles (AvsB, AvsC, BvsC)
        for (let i = 0; i < n; i++) {
            for (let k = i + 1; k < n; k++) {
                torneo.ligaMatches.push({
                    jornada: j + 1,
                    t1: { ...equipos[i] },
                    t2: { ...equipos[k] },
                    s1: null, s2: null, fin: false, fecha: "", hora: ""
                });
            }
        }
    }
    guardar(); // Guarda los 6 partidos generados en el backend
}

function updateMatchInfo(i,field,val){torneo.ligaMatches[i][field]=val;guardar()}

function updateMatchTeam(i,num,name){
  const eq=equipos.find(e=>e.name===name); if(!eq) return;
  if(num===1)torneo.ligaMatches[i].t1={...eq}; else torneo.ligaMatches[i].t2={...eq};
  guardar(); renderJornadaActual();
}

function renderJornadaActual(){
  const c=$id("league-matches-list"); if(!c) return;
  const jornadas=[...new Set(torneo.ligaMatches.map(m=>m.jornada))];
  c.innerHTML=jornadas.map(j=>`
    <div style="margin-top:20px"><h3>Jornada ${j}</h3></div>
    ${torneo.ligaMatches.map((m,i)=>m.jornada!==j?"":`
      <div style="display:flex;flex-wrap:wrap;align-items:center;justify-content:center;gap:10px;margin-bottom:15px;padding:12px;border:1px solid var(--border);border-radius:10px">
        <input type="date" value="${m.fecha||''}" onchange="updateMatchInfo(${i},'fecha',this.value)">
        <input type="time" value="${m.hora||''}" onchange="updateMatchInfo(${i},'hora',this.value)">
        <select onchange="updateMatchTeam(${i},1,this.value)">${equipos.map(e=>`<option value="${e.name}"${e.name===m.t1.name?' selected':''}>${e.name}</option>`).join("")}</select>
        <img src="${m.t1.logo}" width="25">
        <input type="number" value="${m.s1??''}" onchange="setScore(${i},1,this.value)" style="width:70px">
        <strong>VS</strong>
        <input type="number" value="${m.s2??''}" onchange="setScore(${i},2,this.value)" style="width:70px">
        <img src="${m.t2.logo}" width="25">
        <select onchange="updateMatchTeam(${i},2,this.value)">${equipos.map(e=>`<option value="${e.name}"${e.name===m.t2.name?' selected':''}>${e.name}</option>`).join("")}</select>
      </div>`).join("")}`).join("");
}

function setScore(i,team,val){
  if(val==="") return;
  const m=torneo.ligaMatches[i];
  if(m.fin){revertirStats(m.t1,m.s1,m.s2);revertirStats(m.t2,m.s2,m.s1)}
  if(team===1)m.s1=parseInt(val); else m.s2=parseInt(val);
  if(m.s1!==null&&m.s2!==null){m.fin=true;actualizarStats(m.t1,m.s1,m.s2);actualizarStats(m.t2,m.s2,m.s1)}
  guardar(); renderTabla();
}

// ===== STATS =====
function actualizarStats(eq,gf,gc){
  if(!statsEquipos[eq.name])statsEquipos[eq.name]={pj:0,g:0,e:0,p:0,gf:0,gc:0,dg:0,pts:0};
  const s=statsEquipos[eq.name];
  s.pj++;s.gf+=gf;s.gc+=gc;s.dg=s.gf-s.gc;
  if(gf>gc){s.g++;s.pts+=3}else if(gf===gc){s.e++;s.pts+=1}else s.p++;
}

function revertirStats(eq,gf,gc){
  const s=statsEquipos[eq.name]; if(!s) return;
  s.pj--;s.gf-=gf;s.gc-=gc;s.dg=s.gf-s.gc;
  if(gf>gc){s.g--;s.pts-=3}else if(gf===gc){s.e--;s.pts-=1}else s.p--;
}

function renderTabla(){
  const c=$id("tabla-puntos"); if(!c) return;
  let data=equipos.map(e=>({name:e.name,logo:e.logo,...(statsEquipos[e.name]||{pj:0,g:0,e:0,p:0,gf:0,gc:0,dg:0,pts:0})}));
  data.sort((a,b)=>b.pts!==a.pts?b.pts-a.pts:b.dg!==a.dg?b.dg-a.dg:b.gf-a.gf);
  c.innerHTML=`<table><thead><tr><th>#</th><th>Equipo</th><th>PJ</th><th>G</th><th>E</th><th>P</th><th>GF</th><th>GC</th><th>DG</th><th>PTS</th></tr></thead><tbody>${data.map((d,i)=>`<tr><td>${i+1}</td><td><img src="${d.logo}" width="20"> ${d.name}</td><td>${d.pj}</td><td>${d.g}</td><td>${d.e}</td><td>${d.p}</td><td>${d.gf}</td><td>${d.gc}</td><td>${d.dg}</td><td>${d.pts}</td></tr>`).join("")}</tbody></table>`;
}

// ===== FINALES =====
function finalizarLiga(){
  let data=equipos.map(e=>({name:e.name,logo:e.logo,...(statsEquipos[e.name]||{pts:0,dg:0})}));
  data.sort((a,b)=>b.pts!==a.pts?b.pts-a.pts:b.dg-a.dg);
  generarBracket(data.slice(0,config.pass)); faseActual="finales"; guardar(); aplicarVista();
}

function generarBracket(teams){
  torneo.bracket=[];
  let ronda=[];
  for(let i=0;i<teams.length;i+=2)ronda.push({t1:teams[i],t2:teams[i+1]||null,s1:null,s2:null,ganador:null});
  torneo.bracket.push(ronda);
  let n=Math.ceil(ronda.length/2);
  while(n>=1&&ronda.length>1){
    const nueva=Array.from({length:n},()=>({t1:null,t2:null,s1:null,s2:null,ganador:null}));
    torneo.bracket.push(nueva); ronda=nueva; n=Math.floor(n/2);
  }
  guardar(); renderBracket();
}

function renderBracket(){
  const c=$id("bracket-render"); if(!c) return;
  c.innerHTML=torneo.bracket.map((ronda,r)=>`
    <div><h3>Ronda ${r+1}</h3>${ronda.map((m,i)=>`
      <div style="margin:15px;padding:10px;border:1px solid var(--border);border-radius:10px">
        <div>${m.t1?.name||"TBD"} <input type="number" value="${m.s1??''}" onchange="setFinal(${r},${i},1,this.value)"></div>
        <div>${m.t2?.name||"TBD"} <input type="number" value="${m.s2??''}" onchange="setFinal(${r},${i},2,this.value)"></div>
      </div>`).join("")}</div>`).join("");
}

function setFinal(r,m,team,val){
  if(val==="") return;
  const p=torneo.bracket[r][m];
  if(team===1)p.s1=parseInt(val); else p.s2=parseInt(val);
  if(p.s1!==null&&p.s2!==null){
    p.ganador=p.s1>p.s2?p.t1:p.t2;
    if(torneo.bracket[r+1]){
      const sig=torneo.bracket[r+1][Math.floor(m/2)];
      if(m%2===0)sig.t1=p.ganador; else sig.t2=p.ganador;
    }else mostrarCampeon(p.ganador);
  }
  guardar(); renderBracket();
}

function mostrarCampeon(campeon){
  const box=$id("cuadro-campeon"); if(!box||!campeon) return;
  box.style.display="block";
  box.innerHTML=`<div style="padding:30px;text-align:center"><img src="${campeon.logo}" width="120"><h1>🏆 CAMPEÓN 🏆</h1><h2>${campeon.name}</h2></div>`;
  torneos[torneoActual].campeon=campeon; guardar();
}

// ===== DISCIPLINA =====
function actualizarSelectEquipos(){
  const sel=$id("select-equipo"); if(!sel) return;
  sel.innerHTML=`<option value="">-- Selecciona un equipo --</option>`+equipos.map(e=>`<option value="${e.name}">${e.name}</option>`).join("");
}

function cargarJugadoresExcel(){
  const equipo=$id("select-equipo").value;
  const file=$id("excel-jugadores").files[0];
  const hoja=$id("hoja-jugadores").value;
  const fInicio=parseInt($id("fila-inicio-jugadores").value);
  const fFin=parseInt($id("fila-fin-jugadores").value);
  const col=letraAIndice($id("columna-jugadores").value);
  if(!equipo||!file||!hoja||isNaN(fInicio)){alert("Faltan datos");return}
  const reader=new FileReader();
  reader.onload=e=>{
    const wb=XLSX.read(new Uint8Array(e.target.result),{type:"array"});
    const ws=wb.Sheets[hoja]; if(!ws){alert("Hoja no encontrada");return}
    const json=XLSX.utils.sheet_to_json(ws,{header:1});
    if(!datosDisciplina[equipo])datosDisciplina[equipo]=[];
    for(let i=fInicio-1;i<(fFin||json.length);i++){
      const fila=json[i];
      if(fila&&fila[col])datosDisciplina[equipo].push({nombre:String(fila[col]).trim(),amarillas:0,rojas:0,suspendido:false});
    }
    guardar(); renderDisciplina(); alert("Jugadores cargados");
  };
  reader.readAsArrayBuffer(file);
}


function sancionar(equipo,idx,tipo){
  const j=datosDisciplina[equipo][idx];
  if(tipo==="amarilla"){j.amarillas++;if(j.amarillas%5===0)j.suspendido=true}
  else{j.rojas++;j.suspendido=true}
  guardar(); renderDisciplina();
}

function habilitar(equipo,idx){datosDisciplina[equipo][idx].suspendido=false;guardar();renderDisciplina()}

function toggleLista(id){const el=$id(id);if(!el)return;el.style.display=el.style.display==="block"?"none":"block"}

function renderDisciplina(){
  const c=$id("contenedor-disciplinas"); if(!c) return;
  c.innerHTML=Object.keys(datosDisciplina).map((equipo,i)=>{
    const jug=datosDisciplina[equipo]; if(!jug?.length) return "";
    const tA=jug.reduce((s,j)=>s+j.amarillas,0), tR=jug.reduce((s,j)=>s+j.rojas,0);
    return `<div style="margin-bottom:20px;border:1px solid var(--border);border-radius:10px;padding:10px">
      <div onclick="toggleLista('lista-${i}')" style="cursor:pointer;display:flex;justify-content:center;gap:15px;align-items:center">
        <strong>${equipo}</strong><span>🟨 ${tA}</span><span>🟥 ${tR}</span>
      </div>
      <div id="lista-${i}" style="display:none">
        <table border="1"><tr><th>Jugador</th><th>A</th><th>R</th><th>Estado</th><th>Acciones</th></tr>
        ${jug.map((j,idx)=>`<tr><td>${j.nombre}</td><td>${j.amarillas}</td><td>${j.rojas}</td><td>${j.suspendido?'Suspendido':'OK'}</td>
          <td><button onclick="sancionar('${equipo}',${idx},'amarilla')">🟨</button>
          <button onclick="sancionar('${equipo}',${idx},'roja')">🟥</button>
          ${j.suspendido?`<button onclick="habilitar('${equipo}',${idx})">Habilitar</button>`:''}</td></tr>`).join("")}
        </table>
      </div>
    </div>`;
  }).join("");
}

// ===== SINCRONIZACIÓN AUTOMÁTICA =====
// Consulta la base de datos cada 2 segundos para reflejar cambios entre distintos dispositivos
setInterval(() => {
    cargarBaseDatos();
}, 2000);

// ===== KEEP ALIVE =====
setInterval(()=>fetch("/",{method:"GET",cache:"no-cache"}).catch(()=>{}), 240000);

// ===== ARRANQUE =====
cargarBaseDatos();