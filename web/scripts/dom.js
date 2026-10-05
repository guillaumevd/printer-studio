export const $ = id => document.getElementById(id);
export const text = (id, value) => { $(id).textContent = value ?? '—'; };
export function notice(message) { $('notice').hidden = !message; text('notice', message); }
