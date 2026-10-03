(() => {
  const root = new URL('../', document.currentScript.src);
  const themes = ['original', 'dark', 'compact', 'clean', 'green', 'blue', 'red'];
  const themeColors = { original: '#293f43', dark: '#171c1b', green: '#265d42', blue: '#245d82', red: '#842e3c' };
  const storageKey = 'winter-loop-theme';
  const route = 'https://www.google.com/maps/dir/8650+Manchester+Ct,+Evansville,+IN+47725/Territory+Route+66+RV+Park,+Hinton,+OK/Palo+Duro+Canyon+State+Park,+Canyon,+TX/MERUS+Adventure+Park,+Claude,+TX/Big+Pines+Campground,+Tyler,+TX/Dauphin+Island+Campground,+Dauphin+Island,+AL/8650+Manchester+Ct,+Evansville,+IN+47725';
  function applyTheme(theme) {
    if (!themes.includes(theme)) theme = 'original';
    document.documentElement.dataset.siteTheme = theme;
    document.documentElement.classList.toggle('site-color-theme', ['green', 'blue', 'red'].includes(theme));
    document.querySelectorAll('[data-site-theme-choice]').forEach(button => {
      button.setAttribute('aria-pressed', String(button.dataset.siteThemeChoice === theme));
    });
    const meta = document.querySelector('meta[name="theme-color"]');
    if (meta) meta.content = themeColors[theme] || '#ffffff';
  }
  let initialTheme = 'original';
  try { initialTheme = localStorage.getItem(storageKey) || 'original'; } catch {}
  applyTheme(initialTheme);

  document.addEventListener('DOMContentLoaded', () => {
    const header = document.querySelector('main > header, .shell > header, article.receipt > header');
    if (!header) return;
    const navigation = document.createElement('nav');
    navigation.className = 'site-navigation';
    navigation.setAttribute('aria-label', 'Site navigation');
    function link(label, path, external = false) {
      const anchor = document.createElement('a');
      anchor.textContent = label;
      anchor.href = external ? path : new URL(path, root).href;
      if (external) { anchor.target = '_blank'; anchor.rel = 'noopener noreferrer'; }
      else if (new URL(anchor.href).pathname === location.pathname) anchor.setAttribute('aria-current', 'page');
      return anchor;
    }
    const primary = document.createElement('div');
    primary.className = 'site-links';
    [link('Trip Overview', 'master-plan-2026.html'), link('Weather', 'weather-forecast.html'), link('MERUS Trails', 'activities/merus-trails.html'), link('Tyler Sites', 'campgrounds/tyler-sites.html'), link('Full Loop Map', route, true)].forEach(anchor => {
      if (!anchor.hasAttribute('aria-current')) primary.append(anchor);
    });
    function menu(label, entries) {
      const details = document.createElement('details');
      details.className = 'site-menu';
      const summary = document.createElement('summary');
      summary.textContent = label;
      const panel = document.createElement('div');
      panel.className = 'site-menu-links';
      entries.forEach(([text, path]) => panel.append(link(text, path)));
      details.append(summary, panel);
      details.addEventListener('toggle', () => {
        if (details.open) navigation.querySelectorAll('.site-menu').forEach(other => { if (other !== details) other.open = false; });
      });
      primary.append(details);
    }
    menu('Driving', [['Day 1: Hinton', 'driving/day01.html'], ['Day 2: Palo Duro', 'driving/day02.html'], ['Day 3: Camp day', 'driving/day03-a.html'], ['Day 3: MERUS outing', 'driving/day03-b.html'], ['Day 4: MERUS', 'driving/day04.html'], ['Day 5: Tyler', 'driving/day05.html']]);
    menu('Campgrounds', [['Hinton', 'campgrounds/territory-route-66.html'], ['Palo Duro', 'campgrounds/palo-duro.html'], ['MERUS', 'campgrounds/merus.html'], ['Tyler Sites', 'campgrounds/tyler-sites.html'], ['Dauphin Island', 'campgrounds/dauphin-island.html']]);
    menu('Receipts', [['Hinton', 'receipts/territory-rv.html'], ['Palo Duro', 'receipts/palo-duro.html'], ['MERUS', 'receipts/merus.html'], ['Tyler', 'receipts/tyler.html'], ['Dauphin Island', 'receipts/dauphin-island.html']]);
    navigation.append(primary);
    header.append(navigation);
    applyTheme(initialTheme);
    document.addEventListener('keydown', event => {
      if (event.key === 'Escape') navigation.querySelectorAll('.site-menu').forEach(details => { details.open = false; });
    });
    document.addEventListener('click', event => {
      navigation.querySelectorAll('.site-menu').forEach(details => { if (!details.contains(event.target)) details.open = false; });
    });
  });
  window.addEventListener('storage', event => {
    if (event.key === storageKey) { initialTheme = event.newValue || 'original'; applyTheme(initialTheme); }
  });
})();