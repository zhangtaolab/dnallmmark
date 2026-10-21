/* ========================================
   DNALLM Mark Error Bars
   Vendored inline Chart.js 4.4.0 plugin (Phase 17, WEB-02): renders
   multi-seed error bars on the public charts — scatter whiskers on the
   main leaderboard, whisker caps over native floating bars on the task
   benchmark — with ZERO new dependencies (D17-05/D17-11: wired through
   each chart's top-level plugins array — never globally registered,
   never a new CDN script). The value→pixel math lives in the PURE whiskerGeometry
   export (scale injected — no Chart instance, no canvas, no DOM) so the
   Node test lane can assert geometry over generated fixtures (D17-09).
   Honest absence (D17-08): data without a usable std renders exactly as
   today — no zero-width fake whiskers, no scalar-array coercion.
   ======================================== */

/**
 * Map whisker endpoint VALUES to pixels through an injected scale.
 *
 * Pure by construction: the only Chart.js knowledge is the documented
 * scale contract `getPixelForValue(value)` (the linear implementation in
 * the shipped 4.4.0 UMD resolves the value against _startValue /
 * _valueRange via getPixelForDecimal — a duck-typed fake mirroring that
 * mapping is all tests need). Axis-agnostic: pass the y scale for
 * vertical whiskers (scatter), the x scale for horizontal ones (bars).
 *
 * @param {number} anchor - Anchor PIXEL on the constant axis (el.x for a
 *   scatter point, el.y for a horizontal floating bar).
 * @param {number} loValue - Lower whisker VALUE (mean - std, or the
 *   floating bar's raw[0]).
 * @param {number} hiValue - Upper whisker VALUE (mean + std, or raw[1]).
 * @param {{getPixelForValue: Function}} scale - Duck-typed value scale.
 * @param {number} capWidth - Full cap width in pixels; half extends to
 *   each side of the stem.
 * @returns {{anchor: number, lo: number, hi: number, capHalf: number}}
 *   Endpoint pixels (NOT clamped — clamping into chartArea is the
 *   plugin's drawing concern, kept out of the pure geometry).
 */
export function whiskerGeometry(anchor, loValue, hiValue, scale, capWidth) {
  return {
    anchor,
    lo: scale.getPixelForValue(loValue),
    hi: scale.getPixelForValue(hiValue),
    capHalf: capWidth / 2
  };
}

/**
 * The honest-absence scalar/array mapping for bar data (D17-08, Pitfall 4).
 *
 * Returns a native Chart.js floating-bar datum [mean-std, mean+std] ONLY
 * when std is a finite number > 0; otherwise the scalar metric value is
 * returned untouched (absent / zero / non-finite std renders as the plain
 * bar of today). This is the ONLY place the array form is born —
 * metricValue stays scalar everywhere else (sorting, leaderboard table,
 * tooltips read the closure model, never context.raw).
 *
 * @param {number} metricValue - The scalar metric value (a mean).
 * @param {number|undefined} std - Optional population std (ddof=0,
 *   precomputed offline — never recomputed client-side, DATA-07).
 * @returns {number|number[]} The scalar, or the [lo, hi] floating-bar pair.
 */
export function barDatum(metricValue, std) {
  if (typeof std !== 'number' || !isFinite(std) || std <= 0) {
    return metricValue;
  }
  return [metricValue - std, metricValue + std];
}

/**
 * Clamp a pixel into [floor, ceil]. The scatter pins explicit axis
 * min/max, so mean±std can fall OUTSIDE the chart area — a clamped stem
 * still renders toward the boundary instead of drawing over labels or
 * off-canvas (the axis-overflow edge in the must_haves).
 * @param {number} pixel - Endpoint pixel from whiskerGeometry.
 * @param {number} floor - chartArea boundary (top for point mode, left
 *   for bar mode).
 * @param {number} ceil - Opposite chartArea boundary (bottom / right).
 * @returns {number} The clamped pixel.
 */
function clampPixel(pixel, floor, ceil) {
  return Math.min(ceil, Math.max(floor, pixel));
}

/**
 * The vendored inline plugin. Registered per chart via the top-level
 * config `plugins: [errorBarsPlugin]` array (inline plugins are per-chart
 * and cannot be globally registered — the 4.4.0 documented convention);
 * its id is lowercase per the documented npm-name rule. Draw dispatch:
 *   - Array raw → bar-cap mode over the VALUE axis (x when indexAxis 'y'):
 *     caps always, stem only when options.drawStem (task.js passes false —
 *     the floating bar itself is the range).
 *   - Object raw carrying a finite std > 0 → point mode over chart.scales.y
 *     ONLY (the log-scale FLOPs x axis is structurally out of reach).
 * Everything else is honest absence: nothing is drawn (D17-08), so
 * malformed data degrades silently to today's rendering — never a crash,
 * never a fabricated whisker (T-17-04).
 */
const errorBarsPlugin = {
  id: 'errorbars',
  afterDatasetsDraw(chart, _args, options) {
    const { ctx, chartArea } = chart;
    if (!ctx || !chartArea) return;

    ctx.save();
    ctx.strokeStyle = options.color;
    ctx.lineWidth = options.lineWidth;

    chart.data.datasets.forEach((dataset, i) => {
      const meta = chart.getDatasetMeta(i);
      if (meta.hidden) return;

      dataset.data.forEach((raw, j) => {
        const el = meta.data[j];
        if (!el) return;

        if (Array.isArray(raw)) {
          // Bar-cap mode — raw is a floating-bar [lo, hi] pair born in
          // barDatum. A zero-width pair never renders (no fake whisker).
          if (raw.length !== 2 || raw[0] === raw[1]) return;
          const horizontal = chart.options.indexAxis === 'y';
          const valueScale = horizontal ? chart.scales.x : chart.scales.y;
          if (!valueScale) return;
          const g = whiskerGeometry(el.y, raw[0], raw[1], valueScale, options.capWidth);
          if (!isFinite(g.lo) || !isFinite(g.hi)) return;
          const lo = clampPixel(g.lo, chartArea.left, chartArea.right);
          const hi = clampPixel(g.hi, chartArea.left, chartArea.right);

          ctx.beginPath();
          if (options.drawStem) {
            ctx.moveTo(lo, g.anchor);
            ctx.lineTo(hi, g.anchor);
          }
          ctx.moveTo(lo, g.anchor - g.capHalf);
          ctx.lineTo(lo, g.anchor + g.capHalf);
          ctx.moveTo(hi, g.anchor - g.capHalf);
          ctx.lineTo(hi, g.anchor + g.capHalf);
          ctx.stroke();
        } else if (
          raw && typeof raw === 'object' &&
          typeof raw.y === 'number' &&
          typeof raw.std === 'number' && isFinite(raw.std) && raw.std > 0
        ) {
          // Point mode — vertical whiskers on the y scale only.
          const yScale = chart.scales.y;
          if (!yScale) return;
          const g = whiskerGeometry(
            el.x, raw.y - raw.std, raw.y + raw.std, yScale, options.capWidth
          );
          if (!isFinite(g.lo) || !isFinite(g.hi)) return;
          const lo = clampPixel(g.lo, chartArea.top, chartArea.bottom);
          const hi = clampPixel(g.hi, chartArea.top, chartArea.bottom);

          ctx.beginPath();
          if (options.drawStem) {
            ctx.moveTo(g.anchor, lo);
            ctx.lineTo(g.anchor, hi);
          }
          ctx.moveTo(g.anchor - g.capHalf, lo);
          ctx.lineTo(g.anchor + g.capHalf, lo);
          ctx.moveTo(g.anchor - g.capHalf, hi);
          ctx.lineTo(g.anchor + g.capHalf, hi);
          ctx.stroke();
        }
      });
    });

    ctx.restore();
  },
  defaults: {
    // --color-text-secondary (#595F6E), the token already hardcoded in
    // both charts' configs (discretion A5, matching-token precedent).
    color: '#595F6E',
    lineWidth: 1,
    capWidth: 8,
    drawStem: true
  }
};

// Plain ES exports only — require(esm) exposes this namespace to the
// Node test lane (the data.js dual-consumption seam; no CommonJS
// fallback needed).
export default errorBarsPlugin;
