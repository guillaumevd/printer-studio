const diTarget = 'DI-RS1 01.02';
export function firmwareDesign(version) {
  if (version === 'VG-02.21') return {
    theme: 'vg', title: 'VG-RX1HS', version: '2.21', asset: 'vg-media.svg',
    caption: 'Three media brands', brands: ['DNP', 'DI Support', 'Citizen'],
  };
  if (version === diTarget) return {
    theme: 'di', title: 'DI-RS1', version: '1.02', asset: 'di-media.svg',
    caption: 'Original DI firmware', brands: ['DI Support'],
  };
  return {
    theme: 'dnp', title: 'DNP RX1', version: version.replace(/^0/, ''), asset: 'dnp-media.svg',
    caption: 'Original DNP firmware', brands: ['DNP'],
  };
}

export function firmwareCard(version, target, item, running) {
  const design = firmwareDesign(version);
  const button = document.createElement('button');
  button.type = 'button';
  button.className = `version-option firmware-tile firmware-${design.theme}${version === target ? ' active' : ''}`;
  button.dataset.version = version;
  button.setAttribute('aria-pressed', String(version === target));
  button.setAttribute('aria-label', `${design.title} ${design.version}. Media: ${design.brands.join(', ')}${!item?.available ? '. Unavailable' : ''}`);
  button.disabled = running || !item?.available;
  const visual = document.createElement('span'); visual.className = 'firmware-visual';
  const image = document.createElement('img'); image.src = `/assets/firmware/${design.asset}`;
  image.alt = ''; image.width = 240; image.height = 110;
  visual.append(image);
  const heading = document.createElement('span'); heading.className = 'firmware-tile-heading';
  const name = document.createElement('strong'); name.textContent = design.title;
  const revision = document.createElement('span'); revision.className = 'firmware-revision'; revision.textContent = design.version;
  heading.append(name, revision);
  const caption = document.createElement('small'); caption.className = 'firmware-caption';
  caption.textContent = item?.available ? design.caption : 'Firmware unavailable';
  const brands = document.createElement('span'); brands.className = 'media-brands';
  design.brands.forEach(brand => {
    const badge = document.createElement('span'); badge.className = 'media-brand brand-' + brand.toLowerCase().split(' ')[0];
    badge.textContent = brand; brands.append(badge);
  });
  button.append(visual, heading, caption, brands);
  return button;
}
