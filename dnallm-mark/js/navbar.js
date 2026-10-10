/* ========================================
   DNALLM Mark Shared Navbar Renderer
   One config-driven renderer for every page (Pitfall 8: no per-page
   copies, no static <nav> duplicates — the navbar cannot drift across
   pages). Rendered content is escaped via DataAPI.escapeHTML (FIX-04
   bounded scope).
   ======================================== */

import CONFIG from './config.js';
import DataAPI from './data.js';

/**
 * Render the shared navbar into the page's .navbar-container element.
 * Active link is derived from location.pathname at render time (root-aware:
 * the '/' entry is active only on the index page). Null-guarded per the
 * project container convention (if (!el) return).
 */
function renderNavbar() {
  const container = document.querySelector('.navbar-container');
  if (!container) return;

  const currentPage = window.location.pathname;
  const navbarHTML = `
    <nav class="navbar">
      <div class="navbar-logo">
        <a href="/" class="logo">${DataAPI.escapeHTML(CONFIG.APP_NAME)}</a>
      </div>
      <ul class="navbar-nav">
        ${CONFIG.NAV_LINKS.map(link => {
          const isActive = (link.url === '/' && currentPage === '/') ||
                           (link.url !== '/' && currentPage.includes(link.url));
          return `<li><a href="${link.url}" class="nav-link ${isActive ? 'active' : ''}">${DataAPI.escapeHTML(link.name)}</a></li>`;
        }).join('')}
      </ul>
    </nav>
  `;
  container.innerHTML = navbarHTML;
}

export default renderNavbar;
export { renderNavbar };
