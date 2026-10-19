/* Mapa interactivo de productos por departamento (sin librerías externas). */
(function () {
  const app = document.getElementById("mapa-app");
  const COLORES = ["#1a3f8f", "#a8c52a", "#e08a1e", "#1e7a3c", "#7a4fc1", "#d64f5f", "#1aa3a3", "#8a6d3b", "#2d6cc0", "#5b6b7f"];
  const NEUTRO = "#d9dee5";
  const $ = id => document.getElementById(id);
  const svg = $("mapa"), panel = $("panel"), leyenda = $("leyenda"), tbody = $("tabla").tBodies[0];
  const fSel = $("f-producto"), fDias = $("f-dias");
  const NS = "http://www.w3.org/2000/svg";
  let geo, datos, trazos = {}, seleccion = null;

  function el(tag, props, texto) {
    const e = document.createElement(tag);
    Object.assign(e, props || {});
    if (texto !== undefined) e.textContent = texto;
    return e;
  }
  const color = id => COLORES[datos.productos.findIndex(p => String(p.id) === String(id)) % COLORES.length];
  const nombreProd = id => (datos.productos.find(p => String(p.id) === String(id)) || {}).nombre || "";

  // Producto(s) con más registros en un departamento
  function lider(d) {
    let max = 0, ids = [];
    for (const [id, n] of Object.entries(d.productos)) {
      if (n > max) { max = n; ids = [id]; } else if (n === max && n > 0) ids.push(id);
    }
    return { max, ids };
  }

  async function cargarDatos() {
    const url = app.dataset.datos + (fDias.value ? "?dias=" + fDias.value : "");
    datos = await (await fetch(url, { credentials: "same-origin" })).json();
    const actual = fSel.value;
    fSel.length = 1;
    datos.productos.forEach(p => fSel.add(new Option(p.nombre, p.id)));
    fSel.value = datos.productos.some(p => String(p.id) === actual) ? actual : "";
    $("mapa-vacio").hidden = datos.total > 0;
    pintar();
  }

  function pintar() {
    const sel = fSel.value;
    const deptos = Object.values(datos.departamentos);
    const maxTotal = Math.max(1, ...deptos.map(d => d.total));
    const maxProd = Math.max(1, ...deptos.map(d => d.productos[sel] || 0));

    geo.departamentos.forEach(g => {
      const d = datos.departamentos[g.id], p = trazos[g.id], l = lider(d);
      let relleno = NEUTRO, opacidad = 1;
      if (sel) {
        const n = d.productos[sel] || 0;
        if (n) { relleno = "#1a3f8f"; opacidad = 0.2 + 0.8 * n / maxProd; }
      } else if (l.max) {
        relleno = color(l.ids[0]); opacidad = 0.35 + 0.65 * d.total / maxTotal;
      }
      p.setAttribute("fill", relleno);
      p.setAttribute("fill-opacity", opacidad);
      p.setAttribute("aria-label", `${d.nombre}: ${d.total} registros`);
    });
    pintarLeyenda(sel);
    pintarTabla();
    mostrar(seleccion);
  }

  function pintarLeyenda(sel) {
    leyenda.replaceChildren();
    if (sel) {
      leyenda.append(el("span", {}, "Menos registros"), el("span", { className: "grad" }), el("span", {}, "Más registros de " + nombreProd(sel)));
      return;
    }
    datos.productos.forEach(p => {
      const s = el("span"), i = el("i");
      i.style.background = color(p.id);
      s.append(i, document.createTextNode(p.nombre));
      leyenda.append(s);
    });
    leyenda.append(el("span", {}, "· Color = producto líder · Intensidad = cantidad de registros"));
  }

  function pintarTabla() {
    tbody.replaceChildren();
    Object.values(datos.departamentos).sort((a, b) => b.total - a.total || a.nombre.localeCompare(b.nombre)).forEach(d => {
      const l = lider(d), tr = tbody.insertRow();
      const nombres = l.ids.map(nombreProd).join(" / ");
      tr.insertCell().textContent = d.nombre;
      tr.insertCell().textContent = l.max ? nombres + (l.ids.length > 1 ? " (empate)" : "") : "Sin registros";
      tr.insertCell().textContent = l.max;
      tr.insertCell().textContent = d.total;
    });
  }

  function mostrar(id) {
    Object.values(trazos).forEach(p => p.classList.remove("sel"));
    panel.replaceChildren();
    if (!id) {
      panel.append(el("p", { className: "sub" }, "Pasa el cursor, usa el teclado o toca un departamento para ver el detalle."));
      return;
    }
    trazos[id].classList.add("sel");
    const d = datos.departamentos[id], l = lider(d);
    panel.append(el("h3", {}, d.nombre), el("p", { className: "sub" },
      d.total ? `${d.total} registros` + (l.ids.length > 1 ? " · empate en el primer lugar" : ` · líder: ${nombreProd(l.ids[0])}`) : "Sin registros todavía"));
    datos.productos.map(p => ({ p, n: d.productos[p.id] || 0 })).filter(x => x.n).sort((a, b) => b.n - a.n).forEach(({ p, n }) => {
      const barra = el("div", { className: "barra" }), b = el("b");
      b.style.width = (100 * n / l.max) + "%"; b.style.background = color(p.id);
      barra.append(b);
      const fila = el("div", { className: "fila" });
      fila.append(el("span", {}, p.nombre), barra, el("span", {}, String(n)));
      panel.append(fila);
    });
  }

  async function iniciar() {
    geo = await (await fetch(app.dataset.geo)).json();
    svg.setAttribute("viewBox", geo.viewBox);
    geo.departamentos.forEach(g => {
      const p = document.createElementNS(NS, "path");
      p.setAttribute("d", g.d);
      p.setAttribute("tabindex", "0");
      p.setAttribute("role", "button");
      const ver = () => { seleccion = g.id; mostrar(g.id); };
      p.addEventListener("mouseenter", ver);
      p.addEventListener("focus", ver);
      p.addEventListener("click", ver);
      trazos[g.id] = p;
      svg.append(p);
    });
    fSel.addEventListener("change", () => pintar());
    fDias.addEventListener("change", cargarDatos);
    await cargarDatos();
  }
  iniciar().catch(() => { panel.replaceChildren(el("p", {}, "No se pudo cargar el mapa. Recarga la página.")); });
})();
