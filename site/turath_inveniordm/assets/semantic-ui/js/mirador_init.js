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

    // Phase A: Extract hocr_query and configure search sidebar if present
    var urlParams = new URLSearchParams(window.location.search);
    var hocrQuery = urlParams.get('hocr_query');
    
    if (hocrQuery) {
      // Configure Mirador to open with search sidebar active
      if (!cfg.windows) cfg.windows = [{}];
      if (!cfg.windows[0]) cfg.windows[0] = {};
      
      cfg.windows[0].sideBarOpen = true;
      cfg.windows[0].sideBarPanel = 'search';
      
      // Add companion window for search panel
      if (!cfg.window) cfg.window = {};
      cfg.window.panels = cfg.window.panels || {};
      cfg.window.panels.search = true;
    }

    if (window.Mirador && typeof window.Mirador.viewer === 'function') {
      window.Mirador.viewer(cfg);
      
      // Phase B: DOM manipulation to populate and trigger search (only if hocr_query exists)
      if (hocrQuery) {
        console.log('[Mirador Auto-Search] Starting with query:', hocrQuery);
        setTimeout(function() {
          try {
            // Prevent form submission during our manipulation
            document.addEventListener('submit', function(e) {
              var target = e.target;
              if (target && target.querySelector && target.querySelector('input[placeholder*="Search"]')) {
                e.preventDefault();
                e.stopPropagation();
              }
            }, true);

            // Find search input with multiple fallback selectors
            // Material-UI uses MuiAutocomplete-input class and id starting with "search-cw-"
            var searchInput = 
              document.querySelector('input.MuiAutocomplete-input[id^="search-cw-"]') ||
              document.querySelector('input.MuiAutocomplete-input') ||
              document.querySelector('input[id^="search-cw-"]') ||
              document.querySelector('input[placeholder*="Search"]') ||
              document.querySelector('input[aria-label*="search" i]') ||
              document.querySelector('.mirador-search-panel input[type="text"]') ||
              document.querySelector('[class*="SearchPanel"] input');

            console.log('[Mirador Auto-Search] Search input found:', !!searchInput);
            if (searchInput) {
              console.log('[Mirador Auto-Search] Input element:', searchInput);
              // Populate using native setter + dispatch input event for React
              var nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
              nativeInputValueSetter.call(searchInput, hocrQuery);
              
              var inputEvent = new Event('input', { bubbles: true });
              searchInput.dispatchEvent(inputEvent);
              
              // Find and click search button
              setTimeout(function() {
                var searchButton = 
                  document.querySelector('button[aria-label="Submit search"]') ||
                  document.querySelector('button[aria-label*="search" i]') ||
                  document.querySelector('.mirador-search-panel button[type="submit"]') ||
                  document.querySelector('[class*="SearchPanel"] button');
                
                console.log('[Mirador Auto-Search] Search button found:', !!searchButton);
                if (searchButton) {
                  console.log('[Mirador Auto-Search] Button element:', searchButton);
                  console.log('[Mirador Auto-Search] Clicking search button...');
                  // Simulate complete mouse event sequence for Material-UI
                  var mousedownEvent = new MouseEvent('mousedown', { bubbles: true, cancelable: true });
                  searchButton.dispatchEvent(mousedownEvent);
                  
                  setTimeout(function() {
                    var mouseupEvent = new MouseEvent('mouseup', { bubbles: true, cancelable: true });
                    searchButton.dispatchEvent(mouseupEvent);
                    
                    setTimeout(function() {
                      var clickEvent = new MouseEvent('click', { bubbles: true, cancelable: true });
                      searchButton.dispatchEvent(clickEvent);
                      console.log('[Mirador Auto-Search] Click sequence completed');
                    }, 50);
                  }, 50);
                } else {
                  console.warn('[Mirador Auto-Search] Search button not found - cannot trigger search');
                }
              }, 100);
            } else {
              console.warn('[Mirador Auto-Search] Search input not found - cannot populate query');
            }
          } catch (err) {
            console.error('[Mirador Auto-Search] Error during auto-search:', err);
          }
        }, 2500);
      }
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
