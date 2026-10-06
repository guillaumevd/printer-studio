import {$, text} from '../dom.js';
import {firmwareCard} from './media-design.js';

const dnpVersions = ['02.04', '02.07', '02.10', '02.21'];
const vgTarget = 'VG-02.21';
const diTarget = 'DI-RS1 01.02';
export const versions = [...dnpVersions, diTarget, vgTarget];
let cardsSignature = '';
export function routeFor(printer, target) {
  if (!printer) return [];
  if (target === diTarget) return printer.firmware.startsWith('DS-RX1 ') ? [diTarget] : [];
  const current = printer.firmware === 'DI-RS1 01.02' ? -1 : dnpVersions.indexOf(printer.firmware.replace('DS-RX1 ', ''));
  if (current < 0 && printer.firmware !== 'DI-RS1 01.02') return [];
  if (target === vgTarget) {
    if (printer.edition === vgTarget) return [];
    return [...dnpVersions.slice(current + 1), vgTarget];
  }
  const destination = dnpVersions.indexOf(target);
  if (destination < 0) return [];
  if (destination === current) return target === '02.21' ? [target] : [];
  return destination < current ? [target] : dnpVersions.slice(current + 1, destination + 1);
}

export function renderFirmware(printer, target, state, running) {
  const steps = routeFor(printer, target);
  const signature = JSON.stringify([target, running, state.catalog?.map(item => [item.version, item.available])]);
  if (signature !== cardsSignature) {
    const focusedVersion = document.activeElement?.closest('[data-version]')?.dataset.version;
    $('version-options').replaceChildren(...versions.map(version =>
      firmwareCard(version, target, state.catalog?.find(item => item.version === version), running)));
    cardsSignature = signature;
    if (focusedVersion) [...$('version-options').children].find(card => card.dataset.version === focusedVersion)?.focus({preventScroll: true});
  }
  $('route').replaceChildren();
  if (steps.length) {
    [printer.firmware.replace(/^(DS-RX1|DI-RS1) /, ''), ...steps].forEach((version, index) => {
      if (index) $('route').append(document.createTextNode('→'));
      const chip = document.createElement('span'); chip.className = 'route-chip'; chip.textContent = version === vgTarget ? 'VG-RX1HS 2.21' : version; $('route').append(chip);
    });
  } else text('route', !printer ? 'Connect a printer to calculate the route.' : target === diTarget && printer.firmware === diTarget ? 'Original DI-RS1 1.02 is already installed.' : target === vgTarget && printer.edition === vgTarget ? 'VG-RX1HS 2.21 is already installed.' : printer.firmware === 'DS-RX1 ' + target ? 'This version is already installed.' : 'No supported route to this version.');
  const downgrade = dnpVersions.includes(target) && printer?.firmware?.startsWith('DS-RX1 ') && dnpVersions.indexOf(target) < dnpVersions.indexOf(printer.firmware.slice(7));
  text('update-title', target === diTarget ? 'Install original DI-RS1 1.02' : target === vgTarget ? 'Install DNP VG-RX1HS 2.21' : downgrade ? 'Return to DNP ' + target : printer?.firmware === 'DS-RX1 ' + target ? 'Reinstall stock DNP ' + target : 'Install DNP ' + target);
  text('update-description', target === diTarget
    ? 'Original DI Support media. Restores compatible converted DI-RS1 printers with their original DI bootloader.'
    : target === vgTarget
      ? 'Accepts DNP, DI Support and Citizen CY-02 media. Keeps the existing driver and Hot Folder compatibility.'
      : 'Original DNP media only. Replaces VG media support with the stock DNP firmware.');
  $('update').disabled = !steps.length || !printer?.serial || running || state.interrupted || !steps.every(v => state.catalog?.find(x => x.version === v)?.available);
}
