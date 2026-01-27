/* CSP-safe Mirador initialization (no inline JS)
 * Pattern aligned with Zenodo's mirador3-dist approach: read dataset from DOM and init viewer.
 */
(function () {
  function safeParse(json, fallback) {
    try { return JSON.parse(json || ''); } catch (e) { return fallback; }
  }
  function init() {
    var container = document.getElementById('mirador-viewer') || document.getElementById('m3-dist');
    if (!container) return;

    // Accept either our current template (mirador-viewer) or Zenodo-like (m3-dist)
    var manifestUrl = container.getAttribute('data-manifest') || container.getAttribute('data-manifest-url');
    var cfg = safeParse(container.getAttribute('data-config') || container.getAttribute('data-mirador-config'), {});

    if (manifestUrl) {
      if (cfg && Array.isArray(cfg.windows) && cfg.windows.length > 0) {
        cfg.windows[0].manifestId = manifestUrl;
      } else {
        cfg = Object.assign({ id: 'mirador-viewer', windows: [{ manifestId: manifestUrl }] }, cfg || {});
      }
    }

    if (window.Mirador && typeof window.Mirador.viewer === 'function') {
      window.Mirador.viewer(cfg);
    } else {
      // Mirador library not available yet
      // Intentionally silent to avoid console noise under CSP
    }
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
