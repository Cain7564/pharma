(() => {
  const panel = document.getElementById('chat-panel');
  if (!panel) return;
  const toggle = document.getElementById('chat-toggle');
  const log = document.getElementById('chat-log');
  const input = document.getElementById('chat-input');
  let loaded = false;
  function message(text) {
    const node = document.createElement('div');
    node.className = 'chat-message'; node.textContent = text;
    log.appendChild(node); log.scrollTop = log.scrollHeight;
    return node;
  }
  async function consult(q) {
    const node = message('Consultando: ' + q + '…');
    try {
      const response = await fetch(panel.dataset.url + '?q=' + encodeURIComponent(q), {headers:{Accept:'application/json'}});
      if (!response.ok || !response.headers.get('content-type')?.includes('application/json')) throw Error();
      const data = await response.json();
      node.textContent = data.mensaje + '\n' + data.productos.map(p =>
        '\n• ' + p.nombre + ': ' + p.estado + (p.existencias === null ? '' : ' — ' + p.existencias + ' unidades (mínimo: ' + p.minimo + ')')
      ).join('') + (data.total > 50 ? '\nMostrando 50 de ' + data.total + '. Busca por nombre para precisar.' : '') +
        (data.pendientes ? '\n\nHay ' + data.pendientes + ' medicamento(s) sin inventario registrado.' : '');
      log.scrollTop = log.scrollHeight;
    } catch (_) { node.textContent = 'No se pudo consultar el inventario. Verifica tu conexión y sesión e inténtalo de nuevo.'; }
  }
  const sendBtn = document.getElementById('chat-send');
  if (sendBtn) sendBtn.addEventListener('click', async () => {
    const token = panel.querySelector('[name=csrfmiddlewaretoken]');
    const node = message('Enviando alerta…');
    sendBtn.disabled = true;
    try {
      const response = await fetch(panel.dataset.sendUrl, {method:'POST', headers:{Accept:'application/json','X-CSRFToken': token ? token.value : ''}});
      if (!response.ok || !response.headers.get('content-type')?.includes('application/json')) throw Error();
      const data = await response.json();
      node.textContent = (data.ok ? '✔ ' : '✖ ') + data.mensaje;
    } catch (_) { node.textContent = '✖ No se pudo enviar la alerta. Verifica tu sesión e inténtalo de nuevo.'; }
    sendBtn.disabled = false; log.scrollTop = log.scrollHeight;
  });
  toggle.addEventListener('click', () => {
    panel.hidden = !panel.hidden;
    toggle.setAttribute('aria-expanded', String(!panel.hidden));
    if (!panel.hidden) { if (!loaded) { loaded = true; consult('alertas'); } input.focus(); }
  });
  panel.addEventListener('keydown', e => {if(e.key === 'Escape'){panel.hidden=true;toggle.setAttribute('aria-expanded','false');toggle.focus();}});
  document.querySelectorAll('[data-query]').forEach(b => b.addEventListener('click', () => consult(b.dataset.query)));
  document.getElementById('chat-form').addEventListener('submit', e => {e.preventDefault(); const q=input.value.trim(); if(q){consult(q);input.value='';}});
})();
