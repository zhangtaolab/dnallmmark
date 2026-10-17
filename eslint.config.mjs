// ESLint 10 flat config (Phase 5, TEST-05).
//
// This file is deliberately dependency-free: it is consumed via
//   npx --yes eslint@10.12.0 --config eslint.config.mjs "dnallm-mark/js/*.js"
// with NO package.json and NO node_modules in the repo (the exact-pin npx
// form blessed by the 05-01 Task 2 blocking-human gate — maintainer reply:
// "approved"). Consequences of the manifest-free form:
//   - browser/CDN globals are INLINED in languageOptions.globals below —
//     importing the `globals` npm package would add an npm dependency
//   - the recommended rule set is selected rule-by-rule instead of
//     `import js from '@eslint/js'` — @eslint/js is not resolvable from a
//     config file with no node_modules tree to resolve it against
//
// The rules below are the correctness core (error-class subset of what
// eslint:recommended enables): undefined identifiers (the point of the
// inlined globals), unused/redeclared bindings, duplicate keys, unreachable
// code, and dangerous condition/assignment misuse. Style rules are out of
// scope for this lane.

export default [
  {
    files: ['dnallm-mark/js/*.js'],
    languageOptions: {
      ecmaVersion: 2023,
      sourceType: 'module',
      globals: {
        // Browser API surface observed across the ten frontend modules
        window: 'readonly',
        document: 'readonly',
        console: 'readonly',
        localStorage: 'readonly',
        navigator: 'readonly',
        fetch: 'readonly',
        location: 'readonly',
        performance: 'readonly',
        setTimeout: 'readonly',
        clearTimeout: 'readonly',
        requestIdleCallback: 'readonly',
        cancelIdleCallback: 'readonly',
        FileReader: 'readonly',
        FormData: 'readonly',
        alert: 'readonly',
        // CDN-loaded libraries (Chart.js 4.4.0 / SheetJS 0.18.5 <script> tags)
        Chart: 'readonly',
        XLSX: 'readonly',
        // CommonJS fallback guard in config.js / data.js
        // (`typeof module !== 'undefined' && module.exports`)
        module: 'writable',
      },
    },
    rules: {
      // no-unused-vars is tuned to the repo's documented idioms, not to hide
      // defects:
      //   - varsIgnorePattern '^app$': the page-controller singleton idiom
      //     (`const app = new DNALLMMark()` instantiated for side effects at
      //     module load — 6 files, per the frontend module pattern)
      //   - caughtErrors 'none' (the pre-ESLint-9 default): the repo's
      //     catch-and-continue error strategy deliberately discards the
      //     binding at several documented swallow sites
      //   - args 'none': event-handler signatures with unused params
      'no-undef': 'error',
      'no-unused-vars': [
        'error',
        { args: 'none', caughtErrors: 'none', varsIgnorePattern: '^app$' },
      ],
      'no-redeclare': 'error',
      'no-dupe-keys': 'error',
      'no-dupe-args': 'error',
      'no-dupe-else-if': 'error',
      'no-self-assign': 'error',
      'no-unreachable': 'error',
      'no-constant-condition': 'error',
      'no-empty': 'error',
      'no-cond-assign': 'error',
      'no-func-assign': 'error',
      'no-import-assign': 'error',
      'no-loss-of-precision': 'error',
      'no-setter-return': 'error',
      'no-shadow-restricted-names': 'error',
      'no-unsafe-negation': 'error',
      'no-unsafe-optional-chaining': 'error',
      'no-unused-private-class-members': 'error',
      'use-isnan': 'error',
      'valid-typeof': 'error',
    },
  },
];
