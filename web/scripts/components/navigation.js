const pages = {
  overview: ['Overview', 'My printer', 'Connect, inspect and manage your printer firmware.'],
  activity: ['Activity log', 'Activity log', 'Follow operation progress and export the results.'],
};

export function initializeNavigation() {
  const links = [...document.querySelectorAll('.nav-item')];
  function activate(id) {
    if (!pages[id]) id = 'overview';
    document.querySelectorAll('.workspace-panel').forEach(panel => { panel.hidden = panel.id !== id; });
    links.forEach(link => {
      const selected = link.hash === '#' + id;
      link.classList.toggle('selected', selected);
      if (selected) link.setAttribute('aria-current', 'page');
      else link.removeAttribute('aria-current');
    });
    const [label, title, description] = pages[id];
    document.getElementById('page-label').textContent = label;
    document.getElementById('page-title').replaceChildren(document.createTextNode(title), Object.assign(document.createElement('span'), {textContent: '.'}));
    document.getElementById('page-description').textContent = description;
  }
  links.forEach(link => link.addEventListener('click', event => {
    event.preventDefault();
    activate(link.hash.slice(1));
  }));
  activate('overview');
}
