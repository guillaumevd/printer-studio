const element = id => document.getElementById(id);
window.addEventListener('pywebviewready', () => {
  const api = window.pywebview.api;
  element('install').onclick = () => api.install_update();
  element('continue').onclick = () => api.continue_app();
  async function refresh() {
    const state = await api.get_state();
    element('version').textContent = 'v' + state.current;
    element('message').textContent = state.message;
    element('install').hidden = state.status !== 'available';
    element('install').textContent = 'Install v' + state.latest;
    element('continue').disabled = ['downloading', 'installing'].includes(state.status);
    element('progress').classList.toggle('indeterminate', ['checking', 'opening', 'installing'].includes(state.status));
    element('progress').style.width = state.progress + '%';
  }
  refresh(); setInterval(refresh, 250);
});
