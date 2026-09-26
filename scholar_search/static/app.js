const searchForms = document.querySelectorAll('[data-search-form]');
searchForms.forEach(form => {
  const button = form.querySelector('[type="submit"]');
  const label = button.innerHTML;
  form.addEventListener('submit', () => {
    button.textContent = 'SEARCHING...';
    form.querySelector('[data-search-status]').textContent = 'Searching the collection';
    form.setAttribute('aria-busy', 'true');
  });
  window.addEventListener('pageshow', () => {
    button.innerHTML = label;
    form.removeAttribute('aria-busy');
    form.querySelector('[data-search-status]').textContent = '';
  });
});

const menu = document.querySelector('[data-menu]');
const sidebar = document.querySelector('#sidebar');
const narrowScreen = window.matchMedia('(max-width: 1023px)');
function syncSidebar() {
  sidebar.inert = narrowScreen.matches && !sidebar.classList.contains('is-open');
}
function closeMenu() {
  sidebar.classList.remove('is-open');
  menu.setAttribute('aria-expanded', 'false');
  syncSidebar();
}
menu.addEventListener('click', () => {
  const open = sidebar.classList.toggle('is-open');
  menu.setAttribute('aria-expanded', String(open));
  syncSidebar();
});
narrowScreen.addEventListener('change', closeMenu);
syncSidebar();
document.addEventListener('click', event => {
  if (!sidebar.contains(event.target) && !menu.contains(event.target)) closeMenu();
});

const rows = [...document.querySelectorAll('[data-paper-row]')];
let selected = -1;
document.addEventListener('keydown', event => {
  const editing = event.target.matches('input, textarea, select, [contenteditable="true"]');
  if (event.key === 'Escape') {
    if (sidebar.classList.contains('is-open')) menu.focus();
    closeMenu();
    if (editing) event.target.blur();
  }
  if (editing || event.ctrlKey || event.metaKey || event.altKey) return;
  if (event.key === '/') {
    event.preventDefault();
    const input = document.querySelector('#query') || document.querySelector('#library-query') || document.querySelector('#global-query');
    if (input && input.getClientRects().length) input.focus();
    else window.location.assign('/resps/');
  }
  if ((event.key === 'j' || event.key === 'k') && rows.length) {
    event.preventDefault();
    if (selected >= 0) rows[selected].classList.remove('keyboard-selected');
    selected = selected < 0 ? (event.key === 'j' ? 0 : rows.length - 1) : Math.max(0, Math.min(rows.length - 1, selected + (event.key === 'j' ? 1 : -1)));
    rows[selected].classList.add('keyboard-selected');
    rows[selected].querySelector('[data-paper-link]').focus({preventScroll: true});
    rows[selected].scrollIntoView({block: 'nearest'});
  }
});

let toastTimeout;
function notify(message) {
  const toast = document.querySelector('[data-toast]');
  toast.textContent = message;
  toast.hidden = false;
  clearTimeout(toastTimeout);
  toastTimeout = setTimeout(() => { toast.hidden = true; }, 3500);
}
document.querySelector('[data-copy-citation]')?.addEventListener('click', async () => {
  const citation = document.querySelector('#citation-text');
  try {
    await navigator.clipboard.writeText(citation.textContent);
    notify('BibTeX citation copied.');
  } catch {
    const selection = window.getSelection();
    const range = document.createRange();
    range.selectNodeContents(citation);
    selection.removeAllRanges();
    selection.addRange(range);
    notify('Citation selected. Use your browser copy command.');
  }
});
