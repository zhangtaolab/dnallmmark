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
 * Active link is derived from location.pathname at render time: the links
 * are './'-relative (WR-04), so a directory pathname (site root or subpath
 * root) means the index page — suffix matching works unchanged under
 * subpath hosting. Null-guarded per the project container convention
 * (if (!el) return).
 */
function renderNavbar() {
  const container = document.querySelector('.navbar-container');
  if (!container) return;

  const currentPage = window.location.pathname;
  const pageFile = currentPage.endsWith('/')
    ? 'index.html'
    : currentPage.split('/').pop();
  const navbarHTML = `
    <nav class="navbar">
      <div class="navbar-logo">
        <a href="./index.html" class="logo">${DataAPI.escapeHTML(CONFIG.APP_NAME)}</a>
      </div>
      <ul class="navbar-nav">
        ${CONFIG.NAV_LINKS.map(link => {
          const isActive = link.url === `./${pageFile}`;
          return `<li><a href="${link.url}" class="nav-link ${isActive ? 'active' : ''}">${DataAPI.escapeHTML(link.name)}</a></li>`;
        }).join('')}
      </ul>
    </nav>
  `;
  container.innerHTML = navbarHTML;
}

export default renderNavbar;
export { renderNavbar };
